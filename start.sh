#!/bin/bash
# One-command runner to start both server.py and Cloudflare Tunnel

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "================================================="
echo "   Starting Recruiter Mailer Remote Pipeline     "
echo "================================================="

# Start Python server in background
python3 "$DIR/server.py" &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "Stopping server and tunnel..."
    kill $SERVER_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

sleep 1

# Start Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8080

cleanup
