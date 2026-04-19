# 🚨 NeuroGuard – Predictive Server Failure Monitoring System

NeuroGuard is an AI-powered predictive maintenance system built for a hackathon to monitor server health in real time and predict possible failures before they happen.

The system continuously collects server metrics such as:

- CPU usage
- Memory usage
- Disk health
- Temperature
- Network activity

and generates early alerts so system administrators can take action before downtime occurs.

---

## 🎯 Problem Statement

Traditional monitoring systems only notify after a failure occurs.

NeuroGuard solves this by:

✅ Detecting unusual patterns  
✅ Predicting server failures early  
✅ Sending smart alerts  
✅ Reducing downtime  
✅ Improving infrastructure reliability  

---

## 🚀 Features

### 📊 Real-Time Monitoring
Live dashboard for:
- CPU
- RAM
- Disk
- Temperature
- Network load

### 🤖 AI Prediction Engine
Predicts:
- overheating
- abnormal resource spikes
- disk issues
- server crash probability

### 🚨 Alert System
Provides:
- warning alerts
- critical alerts
- failure logs
- notification history

### 📱 Emergency Contact Alerts
Automatically sends:
- SMS alerts
- email alerts
to the administrator.

### 📈 Dashboard Analytics
Shows:
- server health score
- risk percentage
- alert history
- prediction timeline

---

## 🛠 Tech Stack

### Frontend
- React.js
- Tailwind CSS
- Chart.js

### Backend
- FastAPI
- Python
- APScheduler

### Database
- SQLite / PostgreSQL

### AI / ML
- Scikit-learn
- Pandas
- NumPy

---

## 📂 Project Structure

backend/
│── src/
│ ├── routes/
│ ├── services/
│ ├── models/
│ └── main.py

frontend/
│── src/
│ ├── components/
│ ├── pages/
│ └── App.jsx

yaml
Copy code

---

## ⚙ Installation

### Clone Repository

```bash
git clone https://github.com/your-username/neuroguard.git
cd neuroguard
Backend Setup
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
Frontend Setup
cd frontend
npm install
npm run dev
🌐 API Endpoints
Server Metrics
POST /api/v1/metrics/ingest
Dashboard
GET /api/v1/servers/alert-dashboard
Alert Logs
GET /api/v1/alert-logs?limit=30
🖥 Sample Dashboard

Add screenshots here:

![Dashboard Screenshot](screenshots/dashboard.png)
🔥 Hackathon Innovation

NeuroGuard stands out because it combines:

predictive analytics
real-time monitoring
intelligent alerts
automated response

instead of just showing raw server data.

📌 Future Improvements
Cloud deployment
Voice assistant alerts
Auto-healing servers
Mobile app
Advanced ML models
👨‍💻 Team

Built during Hackathon by:

Chethan Gowda S N
Computer Science Student

📄 License

This project is licensed under the MIT License
