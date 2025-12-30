from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

load_dotenv()

app = Flask(__name__)

DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
COMMANDS_CHANNEL = f"chilldog.commands.{DEVICE_ID}"

pnconfig = PNConfiguration()
pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
pnconfig.user_id = os.getenv("PUBNUB_USER_ID", "chilldog-web")
pnconfig.ssl = True

pubnub = PubNub(pnconfig)

@app.get("/")
def home():
    return "Chilldog PubNub running"

@app.post("/api/test-publish")
def test_publish():
    message = {"source": "chilldog-web", "message": "Hello from Flask via PubNub"}
    envelope = pubnub.publish().channel("chilldog.test").message(message).sync()
    return jsonify({"status": "sent", "timetoken": envelope.result.timetoken})

@app.post("/api/fan")
def set_fan():
    data = request.get_json(force=True)
    fan_on = bool(data.get("on", False))

    message = {
        "type": "SET_FAN",
        "on": fan_on,
        "source": "chilldog-web"
    }

    envelope = pubnub.publish().channel(COMMANDS_CHANNEL).message(message).sync()
    return jsonify({
        "status": "sent",
        "channel": COMMANDS_CHANNEL,
        "timetoken": envelope.result.timetoken,
        "message": message
    })

if __name__ == "__main__":
    app.run(debug=True)
