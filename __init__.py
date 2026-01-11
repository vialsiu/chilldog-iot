import os
import re
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .auth_db import init_db, create_user, get_user_by_email
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from .routes.api import init_api
from .iot_db import init_iot_tables, insert_status_and_maybe_event, fetch_fan_events

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chilldog-dev-secret")
application = app
app.config["PROPAGATE_EXCEPTIONS"] = True

init_db()
init_iot_tables()

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
COMMANDS_CHANNEL = f"chilldog.commands.{DEVICE_ID}"
STATUS_CHANNEL = f"chilldog.status.{DEVICE_ID}"

def validate_password(pw: str) -> str | None:
    if len(pw) < 10:
        return "Password must be at least 10 characters"
    if " " in pw:
        return "Password cannot contain spaces"
    if not re.search(r"[a-z]", pw):
        return "Password must include a lowercase letter"
    if not re.search(r"[A-Z]", pw):
        return "Password must include an uppercase letter"
    if not re.search(r"\d", pw):
        return "Password must include a number"
    if not re.search(r"[^A-Za-z0-9]", pw):
        return "Password must include a symbol"
    return None

pnconfig = PNConfiguration()
pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
pnconfig.user_id = os.getenv("PUBNUB_USER_ID", "chilldog-web")
pnconfig.ssl = True

pubnub = PubNub(pnconfig)

app.register_blueprint(init_api(pubnub, COMMANDS_CHANNEL), url_prefix="")

@app.get("/")
def home():
    if not session.get("user_id"):
        return redirect(url_for("signup_page", next="/"))
    return render_template("index.html")

@app.get("/api/info")
def api_info():
    return jsonify({
        "deviceId": DEVICE_ID,
        "commandsChannel": COMMANDS_CHANNEL,
        "statusChannel": STATUS_CHANNEL,
        "subscribeKey": pnconfig.subscribe_key
    })

@app.get("/login")
def login_page():
    if session.get("user_id"):
        return redirect(url_for("home"))
    next_url = request.args.get("next") or "/"
    return render_template("login.html", error=None, next=next_url)

@app.post("/login")
def login_submit():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    next_url = request.args.get("next") or "/"

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password", next=next_url)

    session["user_id"] = user["id"]
    session["user_email"] = user["email"]

    return redirect(next_url)

@app.get("/signup")
def signup_page():
    if session.get("user_id"):
        return redirect(url_for("home"))
    next_url = request.args.get("next") or "/"
    return render_template("signup.html", error=None, next=next_url)

@app.post("/signup")
def signup_submit():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    next_url = request.args.get("next") or "/"

    if not email or "@" not in email:
        return render_template("signup.html", error="Please enter a valid email", next=next_url)

    err = validate_password(password)
    if err:
        return render_template("signup.html", error=err, next=next_url)

    password_hash = generate_password_hash(password)
    ok = create_user(email, password_hash)

    if not ok:
        return render_template("signup.html", error="That email is already registered", next=next_url)

    user = get_user_by_email(email)
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]

    return redirect(next_url)

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.get("/login/google")
def login_google():
    next_url = request.args.get("next") or "/"
    session["oauth_next"] = next_url
    redirect_uri = url_for("auth_google_callback", _external=True, _scheme="https")
    return google.authorize_redirect(redirect_uri)

@app.get("/auth/google/callback")
def auth_google_callback():
    token = google.authorize_access_token()
    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = google.get("userinfo").json()

    email = (userinfo.get("email") or "").strip().lower()
    if not email:
        return redirect(url_for("login_page"))

    user = get_user_by_email(email)

    if not user:
        random_pw = os.urandom(24).hex()
        password_hash = generate_password_hash(random_pw)
        create_user(email, password_hash)
        user = get_user_by_email(email)

    session["user_id"] = user["id"]
    session["user_email"] = user["email"]

    next_url = session.pop("oauth_next", "/")
    return redirect(next_url)

@app.post("/api/ingest-status")
def ingest_status():
    if not session.get("user_id"):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    if (data.get("type") or "").upper() != "STATUS":
        return jsonify({"error": "invalid payload type"}), 400

    ok, event = insert_status_and_maybe_event(data)
    return jsonify({"ok": ok, "event": event})

@app.get("/api/fan-events")
def api_fan_events():
    if not session.get("user_id"):
        return jsonify({"error": "unauthorized"}), 401

    device_id = request.args.get("deviceId") or DEVICE_ID
    limit = request.args.get("limit") or 20
    events = fetch_fan_events(device_id, int(limit))
    return jsonify({"deviceId": device_id, "events": events})


if __name__ == "__main__":
    app.run(debug=True)

