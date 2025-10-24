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
from typing import Optional


def send_user_message(session_id: str, user_message: str, api_url: str = "http://localhost:3999") -> bool:
    """
    Send user message to the backend API.
    Returns True if successful, False otherwise.
    """
    try:
        endpoint = f"{api_url}/api/sessions/{session_id}/message"
        payload = {
            "sessionId": session_id,
            "userMessage": user_message
        }

        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        return response.status_code in [200, 201]
    except Exception as e:
        # Silently fail - don't block the prompt
        return False


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract session_id and prompt
        session_id = input_data.get('session_id')
        prompt = input_data.get('prompt', '')

        if session_id and prompt:
            # Send the message to the backend
            send_user_message(session_id, prompt)

        # Always exit successfully to not block the prompt
        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == '__main__':
    main()