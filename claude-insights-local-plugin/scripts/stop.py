#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

import json
import sys
import requests
import os


def send_stop(session_id: str, stop_data: dict) -> bool:
    """
    Send stop data to the backend API.
    Returns True if successful, False otherwise.
    """
    try:
        endpoint = "http://localhost:3001/api/hooks/stop"
        payload = {
            "sessionId": session_id,
            "reason": stop_data.get("reason"),
        }

        # Prepare headers with Authorization if API key is set
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get('CLAUDE_INSIGHTS_API_KEY', '')
        if api_key:
            headers['x-api-key'] = api_key

        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=5
        )

        return response.status_code in [200, 201]
    except Exception as e:
        # Silently fail - don't block the stop
        return False


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract session_id and stop reason
        session_id = input_data.get('session_id')
        reason = input_data.get('reason', '')

        if session_id:
            stop_data = {
                "reason": reason
            }
            # Send the data to the backend
            send_stop(session_id, stop_data)

        # Always exit successfully to not block the stop
        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == '__main__':
    main()
