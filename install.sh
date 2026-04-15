#!/bin/bash

set -e

echo "Installing Server Agent..."

# Create app directory
mkdir -p ~/.server-agent
cd ~/.server-agent
python3 -m venv venv
source venv/bin/activate

# Install Python deps
pip install --upgrade pip
pip install fastapi uvicorn psutil nvidia-ml-py

# Download agent.py
curl -sSL https://raw.githubusercontent.com/quentu/PyDash/main/agent/agent.py -o agent.py

# Create systemd service
sudo tee /etc/systemd/system/server-agent.service > /dev/null <<EOF
[Unit]
Description=Server Monitoring Agent
After=network.target

[Service]
User=$USER
WorkingDirectory=$HOME/.server-agent
ExecStart=$HOME/.server-agent/venv/bin/python -m uvicorn agent:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable + start service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable server-agent
sudo systemctl start server-agent

echo "Agent installed and running on port 8000"
