from flask import Blueprint, jsonify, request


def init_api(pubnub, commands_channel):
    api = Blueprint("api", __name__)

    def publish_command(message: dict):
        envelope = pubnub.publish().channel(commands_channel).message(message).sync()
        return envelope.result.timetoken

    @api.post("/api/fan")
    def set_fan():
        data = request.get_json(force=True)
        fan_on = bool(data.get("on", False))

        message = {"type": "SET_FAN", "on": fan_on, "source": "chilldog-web"}
        timetoken = publish_command(message)

        return jsonify({
            "status": "sent",
            "channel": commands_channel,
            "timetoken": timetoken,
            "message": message
        })

    @api.post("/api/fan/auto")
    def fan_auto():
        message = {"type": "CLEAR_MANUAL_OVERRIDE", "source": "chilldog-web"}
        timetoken = publish_command(message)

        return jsonify({
            "status": "sent",
            "channel": commands_channel,
            "timetoken": timetoken,
            "message": message
        })

    @api.post("/api/target-temp")
    def set_target_temp():
        data = request.get_json(force=True)
        target = float(data.get("targetTemp"))

        message = {"type": "SET_TARGET_TEMP", "targetTemp": target, "source": "chilldog-web"}
        timetoken = publish_command(message)

        return jsonify({
            "status": "sent",
            "channel": commands_channel,
            "timetoken": timetoken,
            "message": message
        })

    @api.post("/api/energy-saver")
    def set_energy_saver():
        data = request.get_json(force=True)
        enabled = bool(data.get("enabled", False))
        timeout_sec = int(data.get("timeoutSec", 120))

        message = {
            "type": "SET_ENERGY_SAVER",
            "enabled": enabled,
            "timeoutSec": timeout_sec,
            "source": "chilldog-web"
        }
        timetoken = publish_command(message)

        return jsonify({
            "status": "sent",
            "channel": commands_channel,
            "timetoken": timetoken,
            "message": message
        })

    return api
