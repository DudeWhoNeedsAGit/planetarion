#!/bin/bash
# Stop all development services cleanly

echo "🛑 Stopping Planetarion development services..."
echo "==============================================="

# Function to kill processes by pattern
kill_processes() {
    local pattern="$1"
    local name="$2"

    local pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        echo "Stopping $name processes: $pids"
        kill $pids 2>/dev/null || true
        sleep 2

        # Force kill if still running
        local remaining=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
        if [ ! -z "$remaining" ]; then
            echo "Force killing remaining $name processes: $remaining"
            kill -9 $remaining 2>/dev/null || true
        fi
    else
        echo "No $name processes found"
    fi
}

# Stop Flask backend
kill_processes "flask run" "Flask"

# Stop React frontend
kill_processes "react-scripts start" "React"

# Stop npm processes
kill_processes "npm start" "npm"

# Stop Python processes that might be running
kill_processes "python.*flask" "Python Flask"

echo ""
echo "✅ All development services stopped"
echo "==================================="
echo "Services can be restarted with: ./test/dev/start.sh"
