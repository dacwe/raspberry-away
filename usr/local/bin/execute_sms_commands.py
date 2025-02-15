#!/usr/bin/env python3

import time
import json
import subprocess
from modem_commands import get_sms_list, send_sms, delete_sms

def fetch_sms_messages():
    return get_sms_list().get("Messages", [])

def process_command(message):
    parts = message.get("Content", "").strip().split(" ", 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    index = message["Index"]
    phone = message["Phone"]
    
    """Executes actions based on the received SMS command."""
    if command == "reboot":
        print(f"Found {command} command: Rebooting...")
        delete_sms(index)
        send_sms(phone, "Rebooting in 10 seconds...")
        time.sleep(10)
        subprocess.run(["reboot"])
        return

    if command == "help":
        print(f"Found {command} command: Sending help...")
        delete_sms(index)
        send_sms(phone, "Available commands:\nreboot\nlist-sms\ndelete-all-smses\nsend-sms number message\nping")
        return

    if command == "list-sms":
        print(f"Found {command} command: Sending SMS list...")
        delete_sms(index)
        sms_list = fetch_sms_messages()
        sms_content = "\n\n".join(
            f"{msg.get('Phone', 'Unknown')} {msg.get('Date', 'Unknown')}: {msg.get('Content', '')}"
            for msg in sms_list
        )
        send_sms(phone, sms_content if sms_content else "No SMS messages.")
        return

    if command == "delete-all-smses":
        print(f"Found {command} command: Deleting all messages...")
        delete_sms(index)
        send_sms(phone, "Deleting all SMS messages...")
        for msg in fetch_sms_messages():
            if "Index" in msg:
                delete_sms(msg["Index"])
        return

    if command == "ping":
        print(f"Found {command} command: pong")
        delete_sms(index)
        send_sms(phone, "pong")
        return

    if command.startswith("send-sms"):
        print(f"Found send-sms command: Sending SMS...")
        delete_sms(index)
        sms_parts = args.split(" ", 1)
        if len(sms_parts) < 2:
            send_sms(phone, "Usage: send-sms number message")
            return
        recipient, sms_message = sms_parts
        print(f"{sms_message} -> {recipient}")
        #send_sms(recipient, sms_message)
        send_sms(phone, f"Message sent to {recipient}")
        return


def check_for_commands():
    """Checks for SMS commands and processes them."""
    print("Checking for (new) messages...")
    sms_messages = fetch_sms_messages()

    for message in sms_messages:
        process_command(message)

if __name__ == "__main__":
    while True:
        check_for_commands()
        time.sleep(10)  # Check every 10 seconds
