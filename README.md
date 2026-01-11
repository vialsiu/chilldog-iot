# ChillDog IoT Cooling Fan Project

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws)
![PubNub](https://img.shields.io/badge/PubNub-FF0066?style=for-the-badge)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens)
![Raspberry%20Pi](https://img.shields.io/badge/Raspberry%20Pi-Zero%202W-C51A4A?style=for-the-badge&logo=raspberrypi)

---

<img width="2554" height="1439" alt="Login" src="https://github.com/user-attachments/assets/16672fce-f762-42e7-a6ff-7b99b21e4911" />

<img width="2523" height="1439" alt="Dashboard" src="https://github.com/user-attachments/assets/c72764a3-f033-4d14-abc0-f4d3a4512f7f" />


---

| Component | Repository |
| --------- | ---------- |
| **Backend (Flask / API / Database)** | https://github.com/vialsiu/chilldog-iot |
| **Hardware (Raspberry Pi IoT)** | https://github.com/vialsiu/IoT-solo |

## Technologies & Stack

| Component | Technology |
|--------|-----------|
| **Runtime** | Python 3 |
| **Backend Framework** | Flask |
| **Database** | MySQL (AWS RDS) |
| **Cloud Hosting** | AWS EC2 |
| **Messaging** | PubNub (Publish / Subscribe) |
| **Authentication** | JWT |
| **Environment Management** | dotenv |
| **Hardware** | Raspberry Pi 4 |

---
## What This System Does

### 1. Environmental Monitoring (IoT Device)

- Reads temperature and humidity via DHT22
- Detects motion using a PIR sensor
- Publishes real-time telemetry every few seconds

### 2. Remote Fan Control

- Fan is powered externally and controlled via a relay
- Commands are sent securely from the web dashboard
- Device listens for commands in real time

### 3. Cloud Backend & Persistence

- Authenticates users
- Authorizes commands using JWT
- Stores:
  - sensor readings
  - fan on/off events
- Supports multi-user data separation

### 4. Live Web Dashboard

- Displays real-time climate data
- Allows manual fan control
- Reflects device state instantly
- Acts as the ingestion bridge between PubNub and the database

---

## System Architecture

<img width="1948" height="1192" alt="Data in Transit Diagram" src="https://github.com/user-attachments/assets/09cf646e-4080-4b82-b537-fd8f29db03b5" />


```

Raspberry Pi
├─ DHT22 (temperature / humidity)
├─ PIR motion sensor
├─ Relay-controlled fan
│
V
PubNub (real-time messaging)
│
V
Web Dashboard (authenticated)
│
V
Flask API (AWS EC2)
│
V
MySQL Database (AWS RDS)

````

---

## Hardware Wiring Diagram

<img width="1795" height="1028" alt="Fritzing Diagram" src="https://github.com/user-attachments/assets/8d0126db-e4a1-4944-baa5-acaba565e5d5" />


**Notes**
- Fan power is electrically isolated from the Raspberry Pi using a relay
- Sensors share a common ground with the Pi
- DHT22 is assumed to have 4 pins (VCC, DATA, NC, GND)

---

## Real-Time Messaging (PubNub)

### Channels

````

chilldog.status.<DEVICE_ID>
chilldog.commands.<DEVICE_ID>

````

### Example STATUS payload

```json
{
  "type": "STATUS",
  "deviceId": "pi-001",
  "ts": 1768149030,
  "temp": 24.3,
  "humidity": 45.1,
  "fanOn": true,
  "mode": "AUTO"
}
````

### Example COMMAND payload

```json
{
  "type": "COMMAND",
  "action": "FAN_ON"
}
```

---

## Database Integration

The backend uses a relational MySQL schema with user ownership enforced via foreign keys.

### Core Tables

* `users`
* `sensor_status`
* `fan_events`

### Relationship Overview

```
users
 ├─ sensor_status (user_id FK)
 └─ fan_events    (user_id FK)
```

Each record is timestamped and permanently stored for historical analysis.

---

## Authentication & Security

* Email/password authentication
* Password hashing
* JWT-based protected API routes
* Tokens required for all command and ingestion endpoints
* Secrets stored in `.env` files (never committed)

---

## Environment Variables

### Backend (`.env` on AWS EC2)

```
SECRET_KEY=...
JWT_SECRET_KEY=...

DB_HOST=...
DB_PORT=3306
DB_NAME=chilldog
DB_USER=chilldog_app
DB_PASSWORD=...
DB_SSL=true

PUBNUB_PUBLISH_KEY=...
PUBNUB_SUBSCRIBE_KEY=...
PUBNUB_SECRET_KEY=...
DEVICE_ID=pi-001
```

### Raspberry Pi (`.env`)

```
PUBNUB_PUBLISH_KEY=...
PUBNUB_SUBSCRIBE_KEY=...
PUBNUB_SECRET_KEY=...
DEVICE_ID=pi-001
```

---

## Installation & Setup

### Raspberry Pi

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

### Backend (AWS EC2)

```bash
pip install -r requirements.txt
sudo systemctl restart apache2
```

---

## Testing the System

1. Run the IoT script on the Raspberry Pi
2. Open the web dashboard and log in
3. Observe live temperature and humidity updates
4. Toggle the fan ON/OFF
5. Verify database entries are created in `sensor_status` and `fan_events`

---

## Design Notes

* Pub/Sub messaging enables low-latency updates
* Client-side ingestion simplifies architecture
* Relay isolation protects the Raspberry Pi
* JWT ensures secure multi-user access
* Cloud database enables persistent storage and scalability

---

## Security Considerations

Security was considered at every stage of the ChillDog system design, covering the IoT device, communication channels, web server, database, and data in transit.

### IoT Device Security
The Raspberry Pi does not have direct access to the database or web server.  
It communicates exclusively through PubNub channels using restricted publish and subscribe keys stored locally in environment variables. No credentials are hardcoded into the device source code.

Physical isolation is also enforced through the use of a relay module, ensuring that higher-power fan circuitry is electrically separated from the Raspberry Pi GPIO pins.

---

### Communication Channel Security
All communication between the IoT device and the web application is handled through PubNub’s publish/subscribe infrastructure.

- Separate channels are used for device status and control commands
- Channels are namespaced by device ID
- PubNub access keys are not exposed publicly
- Only authorised publishers and subscribers can interact with the channels

This prevents unauthorised devices or clients from sending commands or injecting telemetry.

---

### Web Server Security
The Flask web application enforces authentication using JSON Web Tokens (JWT).

- Users must log in to access the dashboard
- All API endpoints related to commands and data ingestion are protected
- Tokens are issued server-side and validated on every request
- Secrets are loaded via environment variables and never committed to version control

The web server is hosted behind Apache on AWS EC2 and served over HTTPS.

---

### Database Security
The MySQL database is hosted on AWS RDS and is not publicly accessible.

- The database can only be accessed from within the AWS VPC
- Credentials are stored securely in environment variables
- Each sensor reading and event is linked to a specific authenticated user
- Passwords are stored as secure hashes

This ensures data confidentiality and user separation.

---

### Data in Transit
All data moving through the system is protected:

- HTTPS is used for browser-to-server communication
- PubNub provides encrypted transport for device messaging
- No plaintext credentials or sensitive information are transmitted

---

## Known Limitations and Issues

The following limitations are acknowledged in the current implementation:

- Database ingestion is triggered client-side, meaning the dashboard must be open for telemetry to be persisted
- Automation logic may override manual fan control unless the device is placed into manual mode
- During development, mobile hotspot networking caused dynamic IP changes when connecting to the Raspberry Pi

These limitations were accepted as design trade-offs for the scope of this project and are documented transparently.
