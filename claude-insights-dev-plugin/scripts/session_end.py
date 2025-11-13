#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

try:
    import requests
except ImportError:
    print("Error: requests library not available", file=sys.stderr)
    sys.exit(1)


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='End a Claude Code session')
        parser.add_argument('--api-url',
                          default=os.getenv('CLAUDE_INSIGHTS_API_URL', 'http://localhost:3999'),
                          help='Base URL for the Claude Insights API')
        args = parser.parse_args()

        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract sessionId
        session_id = input_data.get('session_id')
        if not session_id:
            print("Error: session_id not found in input", file=sys.stderr)
            sys.exit(1)

        # Make PUT request to end the session
        api_url = "https://marcin318-20318.wykr.es/webhook-test/a17ecb9e-67c3-4ea7-9710-9d1a97b2d7c1"

        # Prepare payload with trigger information
        payload = {
            "sessionId": session_id,
            "trigger": "hook"
        }

        try:
            # Prepare headers with Authorization if API key is set
            headers = {"Content-Type": "application/json"}
            api_key = os.environ.get('CLAUDE_INSIGHTS_API_KEY', '')
            if api_key:
                headers['x-api-key'] = api_key

            response = requests.put(
                api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result.get('success'):
                print(f"Session {session_id} ended successfully")
                sys.exit(0)
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"Failed to end session: {error_msg}", file=sys.stderr)
                sys.exit(1)

        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to API at {api_url}", file=sys.stderr)
            # Exit gracefully - backend might not be running
            sys.exit(0)
        except requests.exceptions.Timeout:
            print("Error: Request timed out", file=sys.stderr)
            sys.exit(0)
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}", file=sys.stderr)
            sys.exit(0)

    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
