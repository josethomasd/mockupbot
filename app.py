import os, json, requests
import sys, time

from flask import jsonify
from flask import Flask, request, redirect, url_for, flash

from flask_sqlalchemy import SQLAlchemy

from flask_heroku import Heroku

app = Flask(__name__)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://ahkxbkuocpywok:b5e4d08bf346c284467caa5da3a429332d14025ecfe4322b6129cc56588746eb@ec2-54-163-233-201.compute-1.amazonaws.com:5432/dcemq8m371umpf'

heroku = Heroku(app)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    countval = db.Column(db.Integer, unique=True)

    def __init__(self, countval):
        self.countval = countval
    def __repr__(self):
        return '<title {}'.format(self.name)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.countval

@app.route("/")
def index():
    user = User.query.all()
    user.countval = 0
    db.session.commit()
    return "Hello World"

@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "ok", 200

@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    user = User.query.all()
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    base_url = "https://graph.facebook.com/v2.8/"
    access_token = os.environ["PAGE_ACCESS_TOKEN"]
    data = request.get_json()
    try:
        if data["object"] == "page":
            if data["entry"][0]["messaging"]:
                sender_id = data["entry"][0]["messaging"][0]["sender"]["id"]
                # the facebook ID of the person sending you the message 
                message_text = data["entry"][0]["messaging"][0]["message"]["text"]  # the message's text
                if(user.countval==0):
                    message_data = "Yo"
                else:
                    message_data = "Yoyo"
                send_message(sender_id, message_data)
                    #send_button(sender_id, message_data)
               # send_message(sender_id, message_data)
    except Exception,e: 
        print str(e)

    return "ok", 200

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })

    r = requests.post("https://graph.facebook.com/v2.9/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def send_button(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
            "quick_replies":[
            {
            "content_type":"text",
            "title":"I changed my mind",
            "payload":"first",
          },
          {
            "content_type":"text",
            "title":"I ordered it by mistake",
            "payload":"lunch",
          },
          {
            "content_type":"text",
            "title":"Too small",
            "payload":"evening",
          },
          {
            "content_type":"text",
            "title":"Too big",
            "payload":"breaking",
          },
          {
            "content_type":"text",
            "title":"Not what I expected",
            "payload":"breaking",
          },
          {
            "content_type":"text",
            "title":"I don't need it anymore",
            "payload":"breaking",
          }  
        ]
        }
    })

    r = requests.post("https://graph.facebook.com/v2.9/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def send_state(recipient_id):

    log("sending state to {recipient}: ".format(recipient=recipient_id))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action":"typing_on"

    })
    r = requests.post("https://graph.facebook.com/v2.8/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True)
