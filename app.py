from flask import Flask, jsonify
from dotenv import load_dotenv
import os

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

load_dotenv()

app = Flask(__name__)

pnconfig = PNConfiguration()
pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
pnconfig.user_id = os.getenv("PUBNUB_USER_ID", "chilldog-web")
pnconfig.ssl = True

pubnub = PubNub(pnconfig)

@app.get("/")
def home():
    return "Chilldog PubNub test running"

@app.post("/api/test-publish")
def test_publish():
    message = {
        "source": "chilldog-web",
        "message": "Hello from Flask via PubNub"
    }

    envelope = pubnub.publish() \
        .channel("chilldog.test") \
        .message(message) \
        .sync()

    return jsonify({
        "status": "sent",
        "timetoken": envelope.result.timetoken
    })

if __name__ == "__main__":
    app.run(debug=True)
