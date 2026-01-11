from flask import Blueprint, jsonify, request
from typing import Any
from flask_jwt_extended import jwt_required

def init_api(pubnub: Any, commands_channel: str):
    api = Blueprint("api", __name__)

    def publish_command(message: dict):
        envelope = pubnub.publish().channel(commands_channel).message(message).sync()
        return envelope.result.timetoken

    @api.post("/api/fan")
    @jwt_required()
    def set_fan():
        data = request.get_json(force=True)
        fan_on = bool(data.get("on", False))
        message = {"type": "SET_FAN", "on": fan_on, "source": "chilldog-web"}
        timetoken = publish_command(message)
        return jsonify({"status": "sent", "channel": commands_channel, "timetoken": timetoken, "message": message})

    @api.post("/api/fan/auto")
    @jwt_required()
    def fan_auto():
        message = {"type": "CLEAR_MANUAL_OVERRIDE", "source": "chilldog-web"}
        timetoken = publish_command(message)
        return jsonify({"status": "sent", "channel": commands_channel, "timetoken": timetoken, "message": message})

    @api.post("/api/energy-saver")
    @jwt_required()
    def set_energy_saver():
        data = request.get_json(force=True)
        enabled = bool(data.get("enabled", False))
        timeout_sec = int(data.get("timeoutSec", 120))
        message = {"type": "SET_ENERGY_SAVER", "enabled": enabled, "timeoutSec": timeout_sec, "source": "chilldog-web"}
        timetoken = publish_command(message)
        return jsonify({"status": "sent", "channel": commands_channel, "timetoken": timetoken, "message": message})

    @api.post("/api/temp-thresholds")
    @jwt_required()
    def set_temp_thresholds():
        data = request.get_json(force=True)
        on_temp = float(data.get("onTemp"))
        off_temp = float(data.get("offTemp"))

        if off_temp >= on_temp:
            off_temp = on_temp - 0.5

        message = {"type": "SET_TEMP_THRESHOLDS", "onTemp": on_temp, "offTemp": off_temp, "source": "chilldog-web"}
        timetoken = publish_command(message)
        return jsonify({"status": "sent", "channel": commands_channel, "timetoken": timetoken, "message": message})

    return api
