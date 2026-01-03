const deviceId = "pi-001";
const statusChannel = `chilldog.status.${deviceId}`;

const subscribeKey = "sub-c-6196e5ab-b7e4-4e06-ad4b-bc25001b2587";
const userId = "chilldog-web-ui";

const pubnub = new PubNub({
  subscribeKey,
  userId,
  ssl: true
});

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

/* here I subscribe to status updates */
pubnub.addListener({
  message: function(event) {
    const msg = event.message;

    if (msg.type !== "STATUS") return;

    if (typeof msg.temp !== "undefined") setText("temp", Number(msg.temp).toFixed(1));
    if (typeof msg.humidity !== "undefined" && msg.humidity !== null) setText("hum", Number(msg.humidity).toFixed(1));

    setText("fan", msg.fanOn ? "ON" : "OFF");
    setText("mode", msg.mode || "--");
  }
});

pubnub.subscribe({ channels: [statusChannel] });

/* flask api endpoints*/
async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null
  });
  return res.json();
}

document.getElementById("btnOn").addEventListener("click", async () => {
  await postJSON("/api/fan", { on: true });
});

document.getElementById("btnOff").addEventListener("click", async () => {
  await postJSON("/api/fan", { on: false });
});

document.getElementById("btnAuto").addEventListener("click", async () => {
  await postJSON("/api/fan/auto");
});

document.getElementById("btnSetTemp").addEventListener("click", async () => {
  const val = parseFloat(document.getElementById("targetTemp").value);
  await postJSON("/api/target-temp", { targetTemp: val });
});

document.getElementById("btnEnergy").addEventListener("click", async () => {
  const enabled = document.getElementById("energyEnabled").checked;
  const timeoutSec = parseInt(document.getElementById("timeoutSec").value, 10);
  await postJSON("/api/energy-saver", { enabled, timeoutSec });
});
