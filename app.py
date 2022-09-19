import os
import re
import requests
import json
import urllib.parse
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App, Say
from slack_sdk import WebClient
from flask import Flask, request
from requests.models import PreparedRequest
from requests.models import PreparedRequest

# Activate venv
# Start ngrok
# Change URL to match the new ngrok forwarding address
# Start python flask app

app = Flask(__name__)
req = PreparedRequest()

header = {
    'Authorization': 'SSWS 00zbUAa01XCT-Qwen1h2NxeiFcPutIrC3jur4WqlIb',
    'Content-Type': 'application/json'
}

group_id = '00g29orhy9ARPzrFR697'
base_url = 'https://trial-3887295.okta.com/api/v1'

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
bolt_app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

def parse_user_email(payload: dict):
    payload_string = str(payload['text'])
    user_email = str((payload['blocks'][0]['elements'][0]['elements'][1]['text']))
    return user_email


def parse_for_profile(payload: dict):
    payload_string = str(payload['text'])
    profile = {}
    body = {}
    for i, element in enumerate(payload["blocks"][0]["elements"][0]["elements"]):
        block = element["text"]
        if(i==1):
            profile["email"] = block
            profile["login"] = block
        else:
            attrs = block.split(" ")
    
    for i, item in enumerate(attrs):
        if i > 0:
            key, value = item.split("=", 1)
            profile[key] = value
    body["profile"] = profile
    json_body = json.dumps(body)
    return json_body

@bolt_app.message(re.compile("(users|list)"))
def all_users(payload: dict):
    """ Return all users from Okta """
    
    users_string = []

    header = {
    'Authorization': 'SSWS 00zbUAa01XCT-Qwen1h2NxeiFcPutIrC3jur4WqlIb'
    }
    #  "/groups/" + group_id +
    data = requests.get(base_url + "/users?limit=25", headers = header).json()
    print(data)
    for user in data:
        message_string = user['profile']['email'] + ' - ' + user['profile']['firstName']  + ' ' + user['profile']['lastName']
    
        response = client.chat_postMessage(channel=payload.get('channel'),
                                       thread_ts=payload.get('ts'),
                                       text=message_string)
def check_user_exists(payload: dict):
    user_email = parse_user_email(payload)

    params = {
        'q': user_email,
        'limit': '1',
    }

    payload_str = urllib.parse.urlencode(params, safe='@')
    url = "https://trial-3887295.okta.com/api/v1/users?" + payload_str

    try:
        data = requests.get(url, headers = header).json()
        user_info = data[0]['profile']
        if(user_info['email']):
            return True
        else:
            return False
    except Exception as e:
        print(e)

@bolt_app.message("query")
def query_user(payload: dict):
    user_email = parse_user_email(payload)
    
    params = {
        'q': user_email,
        'limit': '1',
    }

    payload_str = urllib.parse.urlencode(params, safe='@')
    url = "https://trial-3887295.okta.com/api/v1/users?" + payload_str

    data = requests.get(url, headers = header).json()
    user_info = data[0]['profile']
    message_string = user_info['email'] + ' - ' + user_info['firstName']  + ' ' + user_info['lastName']
    response = client.chat_postMessage(channel=payload.get('channel'),
                                       thread_ts=payload.get('ts'),
                                       text=f"User: {message_string}")

@bolt_app.message("create")
def create_user(payload: dict):

    if(check_user_exists(payload)):
        response = client.chat_postMessage(channel=payload.get('channel'),
                                       thread_ts=payload.get('ts'),
                                       text=f"Failure: User with that email already exists")
    else:
        json_body = parse_for_profile(payload)
        try:
            r = requests.post("https://trial-3887295.okta.com/api/v1/users?activate=true",data=json_body,headers=header)
            r.raise_for_status()
            response = client.chat_postMessage(channel=payload.get('channel'),
                                       thread_ts=payload.get('ts'),
                                       text=f"Success: User Created")    
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)

@bolt_app.message("update")
def update_user(payload: dict):
    json_body = parse_for_profile(payload)
    print(json_body)
    
    print('Hi')

handler = SlackRequestHandler(bolt_app)

@app.route("/slacky/events", methods=["POST"])
def slack_events():
    """ Declaring the route where slack will post a request """
    return handler.handle(request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)