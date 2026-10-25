#!/usr/bin/env bash
# ==============================================================================
# 🔥 Přihořívá Solver - Launcher Script
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/.server.pid"
ICON="$DIR/icon.png"
PORT=8080
URL="http://127.0.0.1:$PORT"

is_server_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null || true)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi

    # Test if port 8080 is listening
    python3 -c "import socket; s = socket.socket(); s.settimeout(0.3); res = s.connect_ex(('127.0.0.1', $PORT)); s.close(); exit(0 if res == 0 else 1)" 2>/dev/null
}

start_server() {
    if is_server_running; then
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Přihořívá Solver" "Aplikace již běží na $URL. Otevírám prohlížeč..." -i "$ICON"
        fi
    else
        cd "$DIR"
        setsid python3 "$DIR/app.py" --port "$PORT" </dev/null > "$DIR/server.log" 2>&1 &
        SERVER_PID=$!
        echo "$SERVER_PID" > "$PID_FILE"

        # Wait up to 3 seconds for server to be responsive
        for i in {1..30}; do
            if python3 -c "import socket; s = socket.socket(); s.settimeout(0.2); res = s.connect_ex(('127.0.0.1', $PORT)); s.close(); exit(0 if res == 0 else 1)" 2>/dev/null; then
                break
            fi
            sleep 0.1
        done

        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Přihořívá Solver" "Server byl úspěšně spuštěn na $URL" -i "$ICON"
        fi
    fi

    # Open default browser
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 &
    fi
}

stop_server() {
    STOPPED=0
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null || true)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
            STOPPED=1
        fi
        rm -f "$PID_FILE"
    fi

    PIDS=$(pgrep -f "python3.*$DIR/app.py" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        kill $PIDS 2>/dev/null || true
        STOPPED=1
    fi

    if [ "$STOPPED" -eq 1 ]; then
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Přihořívá Solver" "Webový server byl zastaven." -i "$ICON"
        fi
        echo "Webový server byl zastaven."
    else
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Přihořívá Solver" "Server neběžel." -i "$ICON"
        fi
        echo "Server neběžel."
    fi
}

start_cli() {
    if command -v konsole >/dev/null 2>&1; then
        konsole --workdir "$DIR" -e bash -c "python3 '$DIR/app.py' --cli; echo ''; read -p 'Stiskněte Enter pro ukončení...' -n 1 -r" &
    else
        x-terminal-emulator -e bash -c "cd '$DIR' && python3 app.py --cli; echo ''; read -p 'Stiskněte Enter pro ukončení...' -n 1 -r" &
    fi
}

case "$1" in
    stop)
        stop_server
        ;;
    cli)
        start_cli
        ;;
    status)
        if is_server_running; then
            echo "Server běží na $URL."
        else
            echo "Server neběží."
        fi
        ;;
    open-folder)
        xdg-open "$DIR" >/dev/null 2>&1 &
        ;;
    *)
        start_server
        ;;
esac
