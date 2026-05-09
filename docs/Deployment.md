# 🚀 Production Deployment Guide

Complete guide for deploying the LinkedIn Job Automation Agent to production environments.

---

## 📋 Table of Contents

1. [Local Production Setup](#local-production-setup)
2. [Cloud Deployment (VPS)](#cloud-deployment-vps)
3. [Docker Deployment](#docker-deployment)
4. [Scheduling & Automation](#scheduling--automation)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Scaling Strategies](#scaling-strategies)
7. [Security Best Practices](#security-best-practices)

---

## 🏠 Local Production Setup

### For Personal Daily Use

**Goal:** Run automatically every day on your personal computer

#### Step 1: Complete Installation

```bash
# Follow main README.md for initial setup
./setup.sh

# Verify everything works
python main.py  # Test run
```

#### Step 2: Create Production Config

```python
# config.py - Production settings
max_applications_per_day = 15  # Reasonable daily limit
min_delay_between_apps = 120   # 2 minutes
max_delay_between_apps = 240   # 4 minutes

# Enable notifications (future feature)
enable_email_notifications = True
email_to = "your.email@gmail.com"
```

#### Step 3: Setup Scheduled Runs

**Option A: Windows Task Scheduler**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "LinkedIn Job Agent"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
   - Program: `C:\Path\To\venv\Scripts\python.exe`
   - Arguments: `C:\Path\To\main.py`
   - Start in: `C:\Path\To\linkedin-job-agent`

**Option B: macOS Launchd**

Create `~/Library/LaunchAgents/com.linkedin.jobagent.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.linkedin.jobagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/main.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/path/to/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/logs/stderr.log</string>
</dict>
</plist>
```

Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.linkedin.jobagent.plist
launchctl start com.linkedin.jobagent
```

**Option C: Linux Cron**

```bash
# Edit crontab
crontab -e

# Add daily job at 9 AM
0 9 * * * /path/to/venv/bin/python /path/to/main.py >> /path/to/logs/cron.log 2>&1
```

---

## ☁️ Cloud Deployment (VPS)

### Deploy to DigitalOcean, AWS EC2, or Linode

**Recommended Specs:**
- OS: Ubuntu 22.04 LTS
- RAM: 2GB minimum (4GB recommended)
- Storage: 20GB SSD
- Cost: ~$12-24/month

#### Step 1: Server Setup

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.11 python3.11-venv python3-pip git

# Install Playwright dependencies
apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

#### Step 2: Deploy Application

```bash
# Create application user
useradd -m -s /bin/bash linkedin-bot
su - linkedin-bot

# Clone repository
git clone https://github.com/yourusername/linkedin-job-agent.git
cd linkedin-job-agent

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

#### Step 3: Configure for Headless

```python
# config.py - Server mode
class BrowserConfig:
    headless: bool = True  # Must be True for servers
    
    # Additional args for server environment
    args: List[str] = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-extensions"
    ]
```

#### Step 4: Setup Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/linkedin-bot.service
```

Add:
```ini
[Unit]
Description=LinkedIn Job Automation Agent
After=network.target

[Service]
Type=oneshot
User=linkedin-bot
WorkingDirectory=/home/linkedin-bot/linkedin-job-agent
Environment="PATH=/home/linkedin-bot/linkedin-job-agent/venv/bin"
ExecStart=/home/linkedin-bot/linkedin-job-agent/venv/bin/python main.py
StandardOutput=append:/home/linkedin-bot/linkedin-job-agent/logs/service.log
StandardError=append:/home/linkedin-bot/linkedin-job-agent/logs/error.log

[Install]
WantedBy=multi-user.target
```

#### Step 5: Setup Timer

```bash
# Create timer file
sudo nano /etc/systemd/system/linkedin-bot.timer
```

Add:
```ini
[Unit]
Description=Run LinkedIn Bot Daily
Requires=linkedin-bot.service

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-bot.timer
sudo systemctl start linkedin-bot.timer

# Check status
sudo systemctl status linkedin-bot.timer
sudo systemctl list-timers
```

---

## 🐳 Docker Deployment

### Containerized Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p data logs resumes

# Run as non-root user
RUN useradd -m -u 1000 linkedin-bot && \
    chown -R linkedin-bot:linkedin-bot /app
USER linkedin-bot

# Run application
CMD ["python", "main.py"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  linkedin-bot:
    build: .
    container_name: linkedin-job-agent
    restart: unless-stopped
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - TZ=America/New_York
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./resumes:/app/resumes
      - ./linkedin_cookies.json:/app/linkedin_cookies.json
      - ./linkedin_cookies_refreshed.json:/app/linkedin_cookies_refreshed.json
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

#### Build and Run

```bash
# Build image
docker-compose build

# Run once
docker-compose run --rm linkedin-bot

# Run with scheduled restarts (using cron on host)
docker-compose up -d
```

---

## ⏰ Scheduling & Automation

### Advanced Scheduling Strategies

#### Multi-Session per Day

```bash
# Morning session: 9 AM (15 applications)
0 9 * * * /path/to/run.sh --max-apps 15

# Afternoon session: 2 PM (15 applications)
0 14 * * * /path/to/run.sh --max-apps 15

# Evening session: 7 PM (20 applications)
0 19 * * * /path/to/run.sh --max-apps 20

# Total: 50 applications per day
```

#### Weekend Schedule

```bash
# Different schedule for weekends
0 10 * * 6,0 /path/to/run.sh --max-apps 30  # Saturday & Sunday
```

#### Retry Logic

Create `run.sh`:
```bash
#!/bin/bash

MAX_RETRIES=3
RETRY_DELAY=300  # 5 minutes

for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i of $MAX_RETRIES"
    
    if python main.py "$@"; then
        echo "Success!"
        exit 0
    else
        echo "Failed. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
done

echo "All retries failed"
exit 1
```

---

## 📊 Monitoring & Alerts

### Log Monitoring

```bash
# Real-time log viewing
tail -f logs/errors.log

# Check application statistics
python -c "from application_manager import app_manager; app_manager.print_statistics()"

# Weekly summary
python scripts/weekly_summary.py
```

### Email Notifications

Add to `main.py`:

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(subject: str, body: str):
    """Send email notification"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "linkedin-bot@yourdomain.com"
    msg['To'] = "your.email@gmail.com"
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login("your-email@gmail.com", "app-password")
        server.send_message(msg)

# After agent run
stats = app_manager.get_statistics()
send_notification(
    subject=f"LinkedIn Bot Report - {stats['today_applications']} applications",
    body=f"Submitted: {stats['submitted']}\nFailed: {stats['failed']}"
)
```

### Telegram Notifications

```python
import requests

def send_telegram(message: str):
    """Send Telegram notification"""
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    
    requests.post(url, data=data)

# Usage
send_telegram(f"✅ Applied to {applied_count} jobs today!")
```

---

## 📈 Scaling Strategies

### Strategy 1: Time-Based Scaling

```python
# Spread applications throughout the day
import datetime

current_hour = datetime.datetime.now().hour

if 9 <= current_hour < 12:
    max_apps = 15  # Morning
elif 14 <= current_hour < 17:
    max_apps = 20  # Afternoon
elif 19 <= current_hour < 22:
    max_apps = 15  # Evening
else:
    max_apps = 0   # Off hours
```

### Strategy 2: Adaptive Rate Limiting

```python
# Adjust based on success rate
recent_failures = get_recent_failure_count()

if recent_failures > 5:
    # Slow down if too many failures
    config.linkedin.min_delay_between_apps = 180  # 3 minutes
    config.linkedin.max_applications_per_day = 5
else:
    # Normal speed
    config.linkedin.min_delay_between_apps = 90
    config.linkedin.max_applications_per_day = 15
```

### Strategy 3: Multi-Account Orchestration

**⚠️ High Risk - Use with caution**

```python
# accounts.json
[
    {"cookie_file": "cookies_account1.json", "daily_limit": 30},
    {"cookie_file": "cookies_account2.json", "daily_limit": 30},
    {"cookie_file": "cookies_account3.json", "daily_limit": 30}
]

# orchestrator.py
for account in accounts:
    agent = LinkedInJobAgent(account)
    await agent.run(max_apps=account["daily_limit"])
    await asyncio.sleep(3600)  # 1 hour between accounts
```

---

## 🔒 Security Best Practices

### Environment Variables

```bash
# Never commit .env file
echo ".env" >> .gitignore
echo "linkedin_cookies*.json" >> .gitignore

# Use strong API keys
# Rotate keys regularly
```

### Cookie Security

```bash
# Encrypt cookies at rest
openssl enc -aes-256-cbc -salt -in linkedin_cookies.json -out linkedin_cookies.json.enc

# Decrypt when needed
openssl enc -d -aes-256-cbc -in linkedin_cookies.json.enc -out linkedin_cookies.json
```

### Server Hardening

```bash
# Enable firewall
ufw enable
ufw allow ssh
ufw allow 443

# Automatic security updates
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Fail2ban for SSH protection
apt install fail2ban
systemctl enable fail2ban
```

### Monitoring for Anomalies

```python
# Add to main.py
def check_for_anomalies():
    """Detect unusual patterns"""
    stats = app_manager.get_statistics()
    
    # Alert if too many failures
    if stats['failed'] > stats['submitted']:
        send_alert("⚠️ High failure rate detected!")
    
    # Alert if no applications submitted
    if stats['today_applications'] == 0:
        send_alert("⚠️ No applications submitted today!")
```

---

## 🎯 Production Checklist

- [ ] All dependencies installed
- [ ] API keys configured
- [ ] Resume files added
- [ ] Cookies exported and working
- [ ] Configuration tuned for production
- [ ] Scheduled execution setup
- [ ] Logging configured
- [ ] Monitoring/alerts implemented
- [ ] Backup strategy in place
- [ ] Security hardened
- [ ] Documentation updated

---

## 📞 Troubleshooting Production Issues

### Issue: Agent Not Running on Schedule

```bash
# Check timer status
sudo systemctl status linkedin-bot.timer

# Check service logs
sudo journalctl -u linkedin-bot.service -n 50

# Manual test
sudo -u linkedin-bot /path/to/venv/bin/python /path/to/main.py
```

### Issue: Headless Browser Crashes

```bash
# Check available memory
free -h

# Increase swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: Cookie Expiration

```python
# Add automatic cookie refresh logic
async def refresh_cookies_if_needed():
    """Check and refresh cookies"""
    cookie_age = get_cookie_age()
    
    if cookie_age > 30:  # days
        send_alert("🔒 Cookies expiring soon. Please refresh.")
```

---

## 🚀 Next-Level: SaaS Deployment

### For building a commercial service:

1. **Infrastructure:**
   - Kubernetes for orchestration
   - PostgreSQL for data storage
   - Redis for job queues
   - S3 for document storage

2. **Features:**
   - Web dashboard
   - User authentication
   - Payment integration
   - Multi-tenant architecture

3. **Scaling:**
   - Horizontal pod autoscaling
   - Load balancing
   - CDN for assets

4. **Compliance:**
   - GDPR compliance
   - SOC 2 certification
   - Legal terms of service

---

**Remember:** Start small, monitor closely, scale gradually. The goal is reliable, sustainable automation—not aggressive spamming.

Good luck with your deployment! 🚀