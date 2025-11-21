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


def send_permission_request(session_id: str, permission_data: dict) -> bool:
    """
    Send permission request data to the backend API.
    Returns True if successful, False otherwise.
    """
    try:
        endpoint = "http://localhost:3001/api/hooks/permission-request"
        payload = {
            "sessionId": session_id,
            "permissionType": permission_data.get("permission_type"),
            "details": permission_data.get("details"),
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
        # Silently fail - don't block the permission request
        return False


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract session_id and permission data
        session_id = input_data.get('session_id')
        permission_type = input_data.get('permission_type')
        details = input_data.get('details', {})

        if session_id and permission_type:
            permission_data = {
                "permission_type": permission_type,
                "details": details
            }
            # Send the data to the backend
            send_permission_request(session_id, permission_data)

        # Always exit successfully to not block the permission request
        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == '__main__':
    main()
