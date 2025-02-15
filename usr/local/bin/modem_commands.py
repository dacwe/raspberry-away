#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
import json

BASE_URL = "http://192.168.8.1/api"

class ModemAPIError(Exception):
    """Custom exception for modem API errors."""
    pass

def get_sesinfo_and_tokinfo():
    """Fetches session and token information and returns as JSON."""
    response = requests.get(f"{BASE_URL}/webserver/SesTokInfo")
    if response.status_code != 200:
        raise ModemAPIError("Error fetching session/token info")

    try:
        root = ET.fromstring(response.text)
        return {
            "SesInfo": root.find("SesInfo").text,
            "TokInfo": root.find("TokInfo").text
        }
    except Exception as e:
        raise ModemAPIError(f"Error parsing XML response: {e}")

def get_headers():
    """Returns headers with session and token info."""
    ses_info = get_sesinfo_and_tokinfo()
    return {
        "Cookie": ses_info["SesInfo"],
        "__RequestVerificationToken": ses_info["TokInfo"],
        "Content-Type": "application/xml"
    }

def send_sms(phone, sms):
    """Sends an SMS and returns response as JSON."""
    headers = get_headers()
    sms_data = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<request>'
        '<Index>-1</Index>'
        f'<Phones><Phone>{phone}</Phone></Phones>'
        '<Sca></Sca>'
        f'<Content>{sms}</Content>'
        '<Length>-1</Length>'
        '<Reserved>1</Reserved>'
        '<Date>-1</Date>'
        '</request>'
    )
    response = requests.post(f"{BASE_URL}/sms/send-sms", headers=headers, data=sms_data)
    return handle_response(response)

def get_sms_list():
    """Fetches SMS list and returns JSON."""
    headers = get_headers()
    sms_list_data = """<?xml version="1.0" encoding="UTF-8"?>
    <request>
        <PageIndex>1</PageIndex>
        <ReadCount>20</ReadCount>
        <BoxType>1</BoxType>
        <SortType>0</SortType>
        <Ascending>0</Ascending>
        <UnreadPreferred>0</UnreadPreferred>
    </request>"""
    response = requests.post(f"{BASE_URL}/sms/sms-list", headers=headers, data=sms_list_data)
    return handle_response(response, list_key="Message")

def delete_sms(index):
    """Deletes an SMS by its index and returns response as JSON."""
    headers = get_headers()
    delete_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <request>
        <Index>{index}</Index>
    </request>"""
    response = requests.post(f"{BASE_URL}/sms/delete-sms", headers=headers, data=delete_data)
    return handle_response(response)

def handle_response(response, list_key=None):
    """Handles API response, checking for errors and returning JSON."""
    if response.status_code != 200:
        raise ModemAPIError("API request failed with status code " + str(response.status_code))
    
    try:
        root = ET.fromstring(response.text)
        error_code = root.find("code")
        if error_code is not None and error_code.text not in ["0", "0000"]:
            raise ModemAPIError(f"API error: {error_code.text}")
        return parse_xml_to_json(response.text, list_key)
    except ET.ParseError as e:
        raise ModemAPIError(f"Error parsing XML response: {e}")

def parse_xml_to_json(xml_data, list_key=None):
    """Parses XML response and converts it to JSON format."""
    try:
        root = ET.fromstring(xml_data)
        result = {}
        if list_key:
            messages = []
            for message in root.findall(f".//{list_key}"):
                msg_dict = {child.tag: child.text for child in message}
                messages.append(msg_dict)
            result = {f"{list_key}s": messages}
        else:
            result = {child.tag: child.text for child in root}
        return result
    except Exception as e:
        raise ModemAPIError(f"Error parsing XML response: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print("Usage: python sms_tool.py <command> [args]")
        print("Available commands: send-sms <phone> <message>, list-sms, delete-sms <index>")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command == "send-sms" and len(sys.argv) == 4:
            print(json.dumps(send_sms(sys.argv[2], sys.argv[3]), indent=4))
        elif command == "list-sms":
            print(json.dumps(get_sms_list(), indent=4))
        elif command == "delete-sms" and len(sys.argv) == 3:
            print(json.dumps(delete_sms(sys.argv[2]), indent=4))
        else:
            print(json.dumps({"error": "Invalid command or missing arguments"}, indent=4))
            sys.exit(1)
    except ModemAPIError as e:
        print(json.dumps({"error": str(e)}), indent=4)
        sys.exit(1)
