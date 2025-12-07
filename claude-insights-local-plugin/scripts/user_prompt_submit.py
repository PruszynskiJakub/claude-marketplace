#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

import json
import sys
import os
import requests


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


def send_user_message(session_id: str, user_message: str, transcript: str) -> bool:
    """
    Send user message to the backend API.
    Returns True if successful, False otherwise.
    """
    try:
        endpoint = f"http://localhost:3001/api/hooks/user-prompt-submit"
        payload = {
            "sessionId": session_id,
            "message": user_message,
            "transcript": transcript
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
            send_user_message(session_id, prompt, read_transcript(input_data))

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