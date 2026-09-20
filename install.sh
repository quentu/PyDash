#!/bin/bash

set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
agent_dir="$HOME/.server-agent"
agent_user="$(id -un)"
if [[ ! -f "$source_dir/agent/agent.py" ]]; then
    echo 'Run bash install.sh from an extracted PyDash release.' >&2
    exit 1
fi
mkdir -p "$agent_dir"
python3 -m venv "$agent_dir/venv"
"$agent_dir/venv/bin/python" -m pip install -r "$source_dir/agent/requirements.txt"
install -m 644 "$source_dir/agent/agent.py" "$agent_dir/agent.py"
sudo tee /etc/systemd/system/server-agent.service >/dev/null <<EOF
[Unit]
Description=PyDash Server Monitoring Agent
After=network.target

[Service]
Type=simple
User=$agent_user
WorkingDirectory=$agent_dir
ExecStart=$agent_dir/venv/bin/python -m uvicorn agent:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF
sudo systemd-analyze verify /etc/systemd/system/server-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now server-agent.service
echo 'PyDash agent installed and running on port 8000.'

