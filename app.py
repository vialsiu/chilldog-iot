import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

# Import your blueprint factory
from routes.api import init_api

load_dotenv()

app = Flask(__name__)

DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
COMMANDS_CHANNEL = f"chilldog.commands.{DEVICE_ID}"
STATUS_CHANNEL = f"chilldog.status.{DEVICE_ID}"

pnconfig = PNConfiguration()
pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
pnconfig.user_id = os.getenv("PUBNUB_USER_ID", "chilldog-web")
pnconfig.ssl = True

pubnub = PubNub(pnconfig)

# Register API routes (fan, auto, target-temp, energy-saver)
app.register_blueprint(init_api(pubnub, COMMANDS_CHANNEL), url_prefix="")

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/info")
def api_info():
    # Handy for debugging that config loaded correctly
    return jsonify({
        "deviceId": DEVICE_ID,
        "commandsChannel": COMMANDS_CHANNEL,
        "statusChannel": STATUS_CHANNEL
    })

if __name__ == "__main__":
    app.run(debug=True)
