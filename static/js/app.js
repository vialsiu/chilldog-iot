let selectedTimeoutSec = 120;

let ACCESS_TOKEN = null;

async function getToken() {
  if (ACCESS_TOKEN) return ACCESS_TOKEN;
  const res = await fetch("/api/token");
  if (!res.ok) return null;
  const data = await res.json();
  ACCESS_TOKEN = data.access_token;
  return ACCESS_TOKEN;
}

const editLock = {
  onTemp: false,
  offTemp: false,
  energyEnabled: false,
  timeout: false,
};

function lock(key) { editLock[key] = true; }
function unlock(key) { editLock[key] = false; }

(function initDefaultTimeout() {
  const active = document.querySelector(".seg-btn.is-active");
  if (active?.dataset?.timeout) {
    selectedTimeoutSec = parseInt(active.dataset.timeout, 10);
  }
})();

// lock thresholds in my tile 3 while user is editing them
function lockThresholds() {
  lock("onTemp");
  lock("offTemp");
}
function unlockThresholds() {
  unlock("onTemp");
  unlock("offTemp");
}

["onTemp", "offTemp"].forEach((id) => {
  const el = document.getElementById(id);
  if (!el) return;

  el.addEventListener("focus", lockThresholds);
  el.addEventListener("input", lockThresholds);

    //  unlock after blur if focus didn't go to other input
  el.addEventListener("blur", () => {
    setTimeout(() => {
      const activeId = document.activeElement?.id;
      if (activeId !== "onTemp" && activeId !== "offTemp") {
        unlockThresholds();
      }
    }, 0);
  });
});

// lock energy saver toggle while user is interacting
const energyEl = document.getElementById("energyEnabled");
if (energyEl) {
  energyEl.addEventListener("pointerdown", () => lock("energyEnabled"));
  energyEl.addEventListener("blur", () => unlock("energyEnabled"));
}

// helper is here
async function postJSON(url, body) {
  const token = await getToken();
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body)
  });
  return res.json();
}

// ui helpers
function setTileLocked(tileId, locked) {
  const tile = document.getElementById(tileId);
  if (!tile) return;

  tile.classList.toggle("is-locked", !!locked);

  tile.querySelectorAll("input, button, select, textarea").forEach(el => {
    el.disabled = !!locked;
  });
}

function setManualLocks(isManual) {
  setTileLocked("thresholdsTile", isManual);
  setTileLocked("energyTile", isManual);
  editLock.onTemp = isManual;
  editLock.offTemp = isManual;
  editLock.energyEnabled = isManual;
  editLock.timeout = isManual;
}



function setConnection(ok, text) {
  const dot = document.getElementById("connDot");
  const label = document.getElementById("connText");
  if (dot) dot.style.background = ok ? "#16a34a" : "#9ca3af";
  if (label && text) label.textContent = text;
}

function setFanButtonState(state) {
  // state: "on" | "off" | "auto"
  const btnOn = document.getElementById("btnOn");
  const btnOff = document.getElementById("btnOff");
  const btnAuto = document.getElementById("btnAuto");

  [btnOn, btnOff, btnAuto].forEach(b => b?.classList.remove("is-active"));

  if (state === "on") btnOn?.classList.add("is-active");
  if (state === "off") btnOff?.classList.add("is-active");
  if (state === "auto") btnAuto?.classList.add("is-active");
}

function setFanUI(isOn, mode) {
  const tile = document.getElementById("fanTile");
  const tag = document.getElementById("fanTag");
  const fanText = document.getElementById("fan");

  if (fanText) fanText.textContent = isOn ? "ON" : "OFF";
  if (tag) tag.textContent = isOn ? "ON" : "OFF";
  if (tile) tile.classList.toggle("is-on", !!isOn);

  // highlight logic is like this
  // manual mode highlight ON or OFF
  // otherwise highlight AUTO
  if ((mode || "").toLowerCase().includes("manual")) {
    setFanButtonState(isOn ? "on" : "off");
  } else {
    setFanButtonState("auto");
  }
}

function setModeUI(mode) {
  const el = document.getElementById("mode");
  if (el) el.textContent = mode || "--";
}

function setClimateUI(temp, hum) {
  const t = document.getElementById("temp");
  const h = document.getElementById("hum");

  const tempNum = temp == null ? null : parseFloat(temp);
  const humNum = hum == null ? null : parseFloat(hum);

  if (t) t.textContent = Number.isFinite(tempNum) ? tempNum.toFixed(1) : "--";
  if (h) h.textContent = Number.isFinite(humNum) ? humNum.toFixed(1) : "--";
}

function setEnergyUI(enabled, timeoutSec) {
  const checkbox = document.getElementById("energyEnabled");
  const toggleText = document.querySelector(".toggle-text");

  if (!editLock.energyEnabled && checkbox && typeof enabled === "boolean") {
    checkbox.checked = enabled;
  }
  if (toggleText) toggleText.textContent = enabled ? "Enabled" : "Disabled";

  if (!editLock.timeout && timeoutSec != null) {
    selectedTimeoutSec = parseInt(timeoutSec, 10);
    document.querySelectorAll(".seg-btn").forEach(b => {
      b.classList.toggle(
        "is-active",
        parseInt(b.dataset.timeout, 10) === selectedTimeoutSec
      );
    });
  }
}

async function applyEnergySaver(enabled) {
  const timeoutSec = selectedTimeoutSec;

  setEnergyUI(enabled, timeoutSec);

  try {
    setConnection(true, "Sending…");
    await postJSON("/api/energy-saver", { enabled, timeoutSec });
    setConnection(true, "Command sent");
  } catch (e) {
    console.error(e);
    setConnection(false, "Error sending");
  }
}

// energy toggle
document.getElementById("energyEnabled")?.addEventListener("change", async (e) => {
  const enabled = !!e.target.checked;
  lock("energyEnabled");
  lock("timeout");

  await applyEnergySaver(enabled);

  setTimeout(() => {
    unlock("energyEnabled");
    unlock("timeout");
  }, 800);
});

// energy timeout buttons
document.querySelectorAll(".seg-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    lock("timeout");

    document.querySelectorAll(".seg-btn").forEach(b => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    selectedTimeoutSec = parseInt(btn.dataset.timeout, 10);

    const enabled = !!document.getElementById("energyEnabled")?.checked;

    if (enabled) {
      await applyEnergySaver(true);
    } else {
      setEnergyUI(false, selectedTimeoutSec);
    }

    setTimeout(() => unlock("timeout"), 800);
  });
});

// FAN CONTROLS START HERE 
document.getElementById("btnOn")?.addEventListener("click", async () => {
  try {
    setFanButtonState("on");
    setConnection(true, "Sending…");
    await postJSON("/api/fan", { on: true });
    setConnection(true, "Command sent");
  } catch (e) {
    console.error(e);
    setConnection(false, "Error sending");
  }
});

document.getElementById("btnOff")?.addEventListener("click", async () => {
  try {
    setFanButtonState("off");
    setConnection(true, "Sending…");
    await postJSON("/api/fan", { on: false });
    setConnection(true, "Command sent");
  } catch (e) {
    console.error(e);
    setConnection(false, "Error sending");
  }
});

document.getElementById("btnAuto")?.addEventListener("click", async () => {
  try {
    setFanButtonState("auto");
    setConnection(true, "Sending…");
    await postJSON("/api/fan/auto");
    setConnection(true, "Command sent");
  } catch (e) {
    console.error(e);
    setConnection(false, "Error sending");
  }
});

// THRESHHOLDS HERE
document.getElementById("btnSetThresholds")?.addEventListener("click", async () => {
  try {
    const onTempEl = document.getElementById("onTemp");
    const offTempEl = document.getElementById("offTemp");

    let onTemp = parseFloat(onTempEl?.value);
    let offTemp = parseFloat(offTempEl?.value);
    if (!Number.isFinite(onTemp) || !Number.isFinite(offTemp)) return;

    if (offTemp >= onTemp) {
      offTemp = onTemp - 0.5;
      if (offTempEl) offTempEl.value = offTemp.toFixed(1);
    }

    setConnection(true, "Sending…");
    await postJSON("/api/temp-thresholds", { onTemp, offTemp });
    setConnection(true, "Command sent");

    unlockThresholds(); // just is resync
  } catch (e) {
    console.error(e);
    setConnection(false, "Error sending");
  }
});

setFanButtonState("auto");

// pubnub sub to live stat
(async function initStatus() {
  try {
    const infoRes = await fetch("/api/info");
    const info = await infoRes.json();
    const statusChannel = info.statusChannel;

    const pubnub = new PubNub({
      subscribeKey: info.subscribeKey || "sub-c-6196e5ab-b7e4-4e06-ad4b-bc25001b2587",
      userId: "chilldog-web-ui",
      ssl: true
    });

    pubnub.addListener({
      status: function (s) {
        if (s.category === "PNConnectedCategory") setConnection(true, "Live");
      },
      message: function (event) {
        const data = event.message || {};
        if (data.type !== "STATUS") return;

        setConnection(true, "Live");

        setClimateUI(data.temp ?? data.temperature, data.humidity);
        setModeUI(data.mode);
        setFanUI(!!data.fanOn, data.mode);

        // lock/unlock tiles based on mode
        const isManual = (data.mode || "").toLowerCase().includes("manual");
        setManualLocks(isManual);

        if (!editLock.onTemp && data.onTemp != null) {
          const el = document.getElementById("onTemp");
          if (el && document.activeElement !== el) {
            el.value = String(parseFloat(data.onTemp).toFixed(1));
          }
        }
        if (!editLock.offTemp && data.offTemp != null) {
          const el = document.getElementById("offTemp");
          if (el && document.activeElement !== el) {
            el.value = String(parseFloat(data.offTemp).toFixed(1));
          }
        }

        if (typeof data.energySaverEnabled === "boolean") {
          if (!editLock.energyEnabled && !editLock.timeout) {
            setEnergyUI(!!data.energySaverEnabled, data.energySaverTimeoutSec);
          }
        }

        postJSON("/api/ingest-status", data);
      }
    });

    pubnub.subscribe({ channels: [statusChannel] });
  } catch (e) {
    console.error(e);
    setConnection(false, "Status offline");
  }
})();

function fmtTime(ts) {
  try {
    const d = new Date((ts || 0) * 1000);
    return d.toLocaleString();
  } catch {
    return String(ts || "");
  }
}

function renderEvents(events) {
  const list = document.getElementById("eventsList");
  if (!list) return;

  if (!events || events.length === 0) {
    list.innerHTML = `<div class="events-empty">No events yet.</div>`;
    return;
  }

  list.innerHTML = events.map(e => {
    const title = e.event === "FAN_ON" ? "Fan turned ON" : "Fan turned OFF";
    const temp = (e.temp == null) ? "NA" : Number(e.temp).toFixed(1) + "°C";
    const hum = (e.humidity == null) ? "NA" : Number(e.humidity).toFixed(1) + "%";
    const mode = e.mode || "—";
    return `
      <div class="event-row">
        <div class="event-top">
          <div class="event-title">${title}</div>
          <div class="event-time">${fmtTime(e.ts)}</div>
        </div>
        <div class="event-sub">Temp ${temp} • Hum ${hum} • Mode ${mode}</div>
      </div>
    `;
  }).join("");
}

async function pollFanEvents() {
  try {
    const token = await getToken();
    const res = await fetch("/api/fan-events?limit=25", {
      cache: "no-store",
      headers: token ? { "Authorization": `Bearer ${token}` } : {}
    });
    if (!res.ok) return;
    const data = await res.json();
    renderEvents(data.events || []);
  } catch {}
}

pollFanEvents();
setInterval(pollFanEvents, 4000);
