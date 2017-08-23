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
        return '<title {}'.format(self.countval)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.countval

@app.route("/")
def index():
    user = User.query.filter_by(id=1).first()
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
    user = User.query.filter_by(id=1).first()
    log(user)
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
                    message_data = "Hi there!  Returns are accepted when items are in their original condition: unwashed and unworn. Items not in this condition will not be accepted. You have up to 45 days to return items purchased. Items may be returned to your local store, Returns and exchanges are free when you use our prepaid return shipping label. Was that helpful?"
                elif(user.countval==1):
                    message_data = "OK, no problem. I need to get some information from you. What is your email?"
                elif(user.countval==2):
                    message_data = "Thank you! Is your name Jessica Stanfield?"
                elif(user.countval==3):
                    message_data = "Jessica, I see here that the last order you placed was Order #AA56789. Do you want to return the entire order, or just part of it?"
                elif(user.countval==4):
                    message_data = "I see that you ordered 2 pairs of shoes. Do you want to return both pairs?"
                elif(user.countval==5):
                    message_data = "So you want to return the Salvatore Ferragamo Black Patent Flats with Grosgrain Bow in Size 8. Is that correct?"
                elif(user.countval==6):
                    message_data = "Can you tell me why? Simply choose the reason that most closely matches your reasons for returning this product. For multiple reasons, just type the numbers separated by commas, like so: 1, 3"
                elif(user.countval==7):
                    message_data = "Would you be interested in exchanging the original pair for a larger size? I see that we have a Size 8.5 and a Size 9 in stock in the same color."
                elif(user.countval==8):
                    message_data = "OK, I just want to confirm that you want to exchange the Salvatore Ferragamo Black Patent Flats with Grosgrain Bow in Size 8 for Size 8.5."
                elif(user.countval==9):
                    message_data = "Do you still have the shipping label that was sent to you with your order?"
                elif(user.countval==10):
                    message_data = "Don't worry, I will email a new shipping label to myemail@gmail.com for the exchange. Please send us back the Salvatore Ferragamo Black Patent Flats with Grosgrain Bow Size 8 shoes in this box with the shipping label I am emailing you now."
                elif(user.countval==11):
                    message_data = "Do you want me to send the Salvatore Ferragamo Black Patent Flats with Grosgrain Bow in Size 8.5 to the same address as the original order? Type ‘yes' if you do, ‘no' if you want me to send them to a new address."
                elif(user.countval==12):
                    message_data = "OK, can you confirm the address I have is correct?\n\nJessica Stanfield\n123 Pine Heights Blvd.\nNiceville, CA 12345"
                elif(user.countval==13):
                    message_data = " Thank you. Once the package carrier scans the return label on your original order, we will automatically send you your exchange order Salvatore Ferragamo Black Patent Flats with Grosgrain Bow Size 8.5."
                elif(user.countval==14):
                    message_data = "I'm happy to help! Is there anything else I can do for you? Just type ‘yes' and what I can help you with, or ‘bye'. "
                else:
                    message_data = "Have a great day, Jessica!  :)"
                if(user.countval==6):
                    send_button(sender_id,message_data)
                else:
                    send_message(sender_id, message_data)
                user.countval = user.countval+1
                db.session.commit()
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
