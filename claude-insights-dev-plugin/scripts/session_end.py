#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error


def main():
    try:
        # Parse command line arguments
        # parser = argparse.ArgumentParser(description='End a Claude Code session')
        # parser.add_argument('--api-url',
        #                   default=os.getenv('CLAUDE_INSIGHTS_API_URL', 'http://localhost:3999'),
        #                   help='Base URL for the Claude Insights API')
        # args = parser.parse_args()

        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract sessionId
        session_id = input_data.get('session_id','unknown')
        reason = input_data.get('reason', 'unknown')
        if not session_id:
            print("Error: session_id not found in input", file=sys.stderr)
            sys.exit(1)

        # Make PUT request to end the session
        api_url = "https://marcin318-20318.wykr.es/webhook/a17ecb9e-67c3-4ea7-9710-9d1a97b2d7c1"

        # Prepare payload with trigger information
        payload = {
            "sessionId": session_id,
            "reason": reason
        }

        # Prepare headers with Authorization if API key is set
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get('CLAUDE_INSIGHTS_API_KEY', '')
        if api_key:
            headers['x-api-key'] = api_key

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(api_url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read()
                # Optionally log success
                # print(f"Session {session_id} ended successfully", file=sys.stderr)

            # Success
            sys.exit(0)

        except urllib.error.URLError as e:
            # Handle network errors gracefully (API might not be running)
            print(f"Failed to connect to API: {e}", file=sys.stderr)
            sys.exit(0)

    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
