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


def send_pre_tool_use(session_id: str, tool_data: dict) -> bool:
    """
    Send pre-tool-use data to the backend API.
    Returns True if successful, False otherwise.
    """
    try:
        endpoint = "http://localhost:3001/api/hooks/pre-tool-use"
        payload = {
            "sessionId": session_id,
            "toolName": tool_data.get("tool_name"),
            "toolInput": tool_data.get("tool_input"),
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
        # Silently fail - don't block the tool use
        return False


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract session_id and tool data
        session_id = input_data.get('session_id')
        tool_name = input_data.get('tool_name')
        tool_input = input_data.get('tool_input')

        if session_id and tool_name:
            tool_data = {
                "tool_name": tool_name,
                "tool_input": tool_input
            }
            # Send the data to the backend
            send_pre_tool_use(session_id, tool_data)

        # Always exit successfully to not block the tool use
        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == '__main__':
    main()