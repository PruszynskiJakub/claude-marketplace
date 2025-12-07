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


def read_transcript(input_data: dict) -> str:
    """Read transcript file content."""
    transcript_path = input_data.get('transcript_path') or input_data.get('transcript_file')
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            pass
    return ""


def send_post_tool_use(input_data: dict) -> bool:
    """
    Send post-tool-use data to the backend API.
    Returns True if successful, False otherwise.
    """
    try:
        endpoint = "http://localhost:3001/api/hooks/post-tool-use"

        payload = {
            "sessionId": input_data.get('session_id'),
            "transcript": read_transcript(input_data),
            "data": input_data
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

        # Send the complete input data to the backend
        if input_data.get('session_id'):
            send_post_tool_use(input_data)

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
