#!/usr/bin/env bash

set -euo pipefail

agent_dir="$HOME/.server-agent"
service_file="/etc/systemd/system/server-agent.service"

echo "Removing PyDash agent..."

if systemctl list-unit-files server-agent.service >/dev/null 2>&1; then
    echo "Stopping server-agent.service..."
    sudo systemctl disable --now server-agent.service || true
fi

if [[ -f "$service_file" ]]; then
    echo "Removing systemd service..."
    sudo rm -f "$service_file"
fi

sudo systemctl daemon-reload
sudo systemctl reset-failed

if [[ -d "$agent_dir" ]]; then
    echo "Removing $agent_dir..."
    rm -rf "$agent_dir"
fi

echo "PyDash agent removed successfully."