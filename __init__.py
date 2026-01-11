import os
import re
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .auth_db import init_db, create_user, get_user_by_email
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from .routes.api import init_api

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chilldog-dev-secret")
application = app
app.config["PROPAGATE_EXCEPTIONS"] = True

init_db()

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

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        next_url = request.args.get("next") or "/"
        return render_template("login.html", error="Invalid email or password", next=next_url)

    session["user_id"] = user["id"]
    session["user_email"] = user["email"]

    next_url = request.args.get("next") or url_for("home")
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

    if not email or "@" not in email:
        next_url = request.args.get("next") or "/"
        return render_template("signup.html", error="Please enter a valid email", next=next_url)

    err = validate_password(password)
    if err:
        return render_template("signup.html", error=err, next=nxt)

    password_hash = generate_password_hash(password)
    ok = create_user(email, password_hash)

    if not ok:
        next_url = request.args.get("next") or "/"
        return render_template("signup.html", error="That email is already registered", next=next_url)

    user = get_user_by_email(email)
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]

    next_url = request.args.get("next") or url_for("home")
    return redirect(next_url)

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

if __name__ == "__main__":
    app.run(debug=True)
