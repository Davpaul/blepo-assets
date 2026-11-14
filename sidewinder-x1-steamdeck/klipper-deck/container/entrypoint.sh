#!/bin/bash
# Runs inside the container. Modes: run (default), flash
set -u

DATA="$HOME/printer_data"
HTTP_PORT="${HTTP_PORT:-80}"

prepare() {
    mkdir -p "$DATA"/{config,logs,gcodes,comms,database}
    for f in printer.cfg moonraker.conf; do
        if [ ! -f "$DATA/config/$f" ]; then
            cp "/opt/deck/defaults/$f" "$DATA/config/$f"
            echo "Created default $f"
        fi
    done
    # Mainsail's standard macros: always refreshed, don't edit this one
    cp /opt/mainsail-config/mainsail.cfg "$DATA/config/mainsail.cfg"
}

# keep_running <name> <command...>: restart the command if it ever exits
keep_running() {
    local name="$1"; shift
    while true; do
        "$@"
        echo "[$name] exited (code $?), restarting in 3s"
        sleep 3
    done
}

run() {
    prepare
    sed "s/__HTTP_PORT__/$HTTP_PORT/g" /opt/deck/nginx.conf.template > /etc/nginx/conf.d/mainsail.conf

    keep_running klipper /opt/klippy-env/bin/python /opt/klipper/klippy/klippy.py \
        "$DATA/config/printer.cfg" \
        -I "$DATA/comms/klippy.serial" \
        -l "$DATA/logs/klippy.log" \
        -a "$DATA/comms/klippy.sock" > /dev/null 2>&1 &

    keep_running moonraker /opt/moonraker-env/bin/python /opt/moonraker/moonraker/moonraker.py \
        -d "$DATA" > /dev/null 2>&1 &

    keep_running nginx nginx -g 'daemon off;' &

    trap 'echo "Stopping..."; kill 0; exit 0' TERM INT
    sleep 4
    echo
    echo "Klipper, Moonraker and Mainsail are running."
    echo "Logs are in ~/klipper-deck/printer_data/logs on the Deck."
    wait
}

case "${1:-run}" in
    run)   run ;;
    flash) prepare; exec /opt/deck/flash-mcu.sh ;;
    shell) prepare; exec bash ;;
    *)     exec "$@" ;;
esac
