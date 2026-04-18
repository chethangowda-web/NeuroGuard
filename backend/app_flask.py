from flask import Flask, jsonify, request

from backend.services.sms_service import send_sms_alert


app = Flask(__name__)


def should_trigger_alert(cpu: float, memory: float, disk: float, failure_probability: float) -> bool:
    return cpu > 80 or memory > 85 or disk > 90 or failure_probability > 0.75


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/test-sms")
def test_sms():
    message = "NeuroGuard Test SMS Alert: Twilio working successfully!"
    success = send_sms_alert(message)
    return jsonify({"success": success, "message": message}), (200 if success else 500)


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    cpu = float(payload.get("cpu", 0))
    memory = float(payload.get("memory", 0))
    disk = float(payload.get("disk", 0))
    failure_probability = float(payload.get("failure_probability", 0))

    alert_triggered = should_trigger_alert(cpu, memory, disk, failure_probability)
    sms_sent = False

    if alert_triggered:
        alert_message = (
            "NeuroGuard Alert: "
            f"cpu={cpu}, memory={memory}, disk={disk}, failure_probability={failure_probability}"
        )
        sms_sent = send_sms_alert(alert_message)

    return jsonify(
        {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "failure_probability": failure_probability,
            "alert_triggered": alert_triggered,
            "sms_sent": sms_sent,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
