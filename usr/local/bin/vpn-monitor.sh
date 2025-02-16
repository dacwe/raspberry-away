#!/bin/bash

failures=0

# Initial sleep is a little bit shorter to try and get the vpn up faster
sleep 150

while true; do
    # Check if VPN is up by pinging a known address
    if ping -c 1 -W 5 192.168.40.1 > /dev/null 2>&1; then
        # Reset failure count if VPN is up
        echo "VPN is up."
        failures=0
    else
        # Increment failure count and check threshold
        ((failures++))
        if [ $failures -lt 5 ]; then
            echo "VPN is down. Attempting to restart wg-quick@wg0.service..."
            sudo systemctl restart wg-quick@wg0.service --no-block
        else
            echo "VPN failed 5 times. Restarting the machine..."
            sudo reboot
        fi
    fi

    # Wait for 5 minutes before checking again
    sleep 300
done
