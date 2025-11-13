#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

"""
Session End Transcript Hook
Parses Claude Code transcript into structured format and sends to backend.
"""

import json
import sys
import requests
from typing import List, Dict, Any
from pathlib import Path


def parse_transcript(transcript_path: str) -> List[Dict[str, Any]]:
    """
    Parse NDJSON transcript into structured format.
    Returns list of transcript entries (user and assistant messages).
    """
    try:
        conversations = []

        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get('type')

                # Skip metadata entries
                if entry_type in ['file-history-snapshot', 'summary']:
                    continue

                # Skip meta user messages (like /exit commands)
                if entry.get('isMeta'):
                    continue

                # Parse user messages
                if entry_type == 'user':
                    message = entry.get('message', {})
                    if message.get('role') == 'user':
                        content = message.get('content', '')
                        timestamp = entry.get('timestamp', '')

                        # Extract only text content from user messages
                        if isinstance(content, str):
                            content_str = content
                        elif isinstance(content, list):
                            # Extract only text items from array
                            text_items = []
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text_items.append(item.get('text', ''))
                            content_str = '\n'.join(text_items) if text_items else None
                        else:
                            content_str = None

                        # Only include if there's text content
                        if content_str:
                            conversations.append({
                                'role': 'user',
                                'text': content_str,
                                'timestamp': timestamp,
                                'type': 'text'
                            })

                # Parse assistant messages
                elif entry_type == 'assistant':
                    message = entry.get('message', {})
                    if message.get('role') == 'assistant':
                        content_blocks = message.get('content', [])
                        timestamp = entry.get('timestamp', '')

                        # Create separate entries for each content block
                        for block in content_blocks:
                            block_type = block.get('type')

                            if block_type == 'text':
                                text_content = block.get('text', '')
                                if text_content:
                                    conversations.append({
                                        'role': 'assistant',
                                        'type': 'text',
                                        'text': text_content,
                                        'timestamp': timestamp
                                    })

                            elif block_type == 'thinking':
                                thinking_content = block.get('thinking', '')
                                if thinking_content:
                                    conversations.append({
                                        'role': 'assistant',
                                        'type': 'thinking',
                                        'text': thinking_content,
                                        'timestamp': timestamp
                                    })

        return conversations

    except FileNotFoundError:
        print(f"Error: Transcript file not found at {transcript_path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error parsing transcript: {str(e)}", file=sys.stderr)
        return []


def format_conversations(conversations: List[Dict[str, Any]]) -> str:
    """Format parsed conversations into clean, readable text."""
    if not conversations:
        return "No conversation data found."

    formatted_lines = []
    formatted_lines.append("=" * 80)
    formatted_lines.append("SESSION TRANSCRIPT")
    formatted_lines.append("=" * 80)
    formatted_lines.append("")

    for i, conv in enumerate(conversations, 1):
        if conv['type'] == 'user':
            formatted_lines.append(f"[{i}] USER:")
            formatted_lines.append(conv['content'])
            formatted_lines.append("")

        elif conv['type'] == 'assistant':
            formatted_lines.append(f"[{i}] CLAUDE:")

            if conv.get('text'):
                formatted_lines.append(conv['text'])

            if conv.get('tool_calls'):
                formatted_lines.append("")
                formatted_lines.append("Tools used:")
                for tool in conv['tool_calls']:
                    tool_name = tool.get('name', 'Unknown')
                    tool_input = tool.get('input', {})

                    # Format tool input based on common patterns
                    if tool_name == 'Read':
                        file_path = tool_input.get('file_path', '')
                        formatted_lines.append(f"  • Read: {file_path}")

                    elif tool_name == 'Write':
                        file_path = tool_input.get('file_path', '')
                        formatted_lines.append(f"  • Write: {file_path}")

                    elif tool_name == 'Edit':
                        file_path = tool_input.get('file_path', '')
                        formatted_lines.append(f"  • Edit: {file_path}")

                    elif tool_name == 'Bash':
                        command = tool_input.get('command', '')
                        # Truncate long commands
                        if len(command) > 80:
                            command = command[:77] + "..."
                        formatted_lines.append(f"  • Bash: {command}")

                    elif tool_name == 'Grep':
                        pattern = tool_input.get('pattern', '')
                        path = tool_input.get('path', '')
                        formatted_lines.append(f"  • Grep: '{pattern}' in {path if path else 'current directory'}")

                    elif tool_name == 'Glob':
                        pattern = tool_input.get('pattern', '')
                        formatted_lines.append(f"  • Glob: {pattern}")

                    elif tool_name == 'Task':
                        description = tool_input.get('description', '')
                        subagent = tool_input.get('subagent_type', '')
                        formatted_lines.append(f"  • Task ({subagent}): {description}")

                    else:
                        # Generic format for other tools
                        formatted_lines.append(f"  • {tool_name}")

            if conv.get('tokens'):
                formatted_lines.append(f"(Tokens: {conv['tokens']})")

            formatted_lines.append("")
            formatted_lines.append("-" * 80)
            formatted_lines.append("")

    return '\n'.join(formatted_lines)


def send_to_backend(session_id: str, transcript: List[Dict[str, Any]], api_url: str = "http://localhost:3999") -> bool:
    """Send structured transcript to backend API."""
    try:
        import os

        endpoint = "https://marcin318-20318.wykr.es/webhook/ac4e80ea-8f5e-44dc-86d8-f499b049ebb3"
        payload = {
            "sessionId": session_id,
            "transcript": transcript
        }

        # Prepare headers with Authorization if API key is set
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get('CLAUDE_INSIGHTS_API_KEY', '')
        if api_key:
            headers['x-api-key'] = api_key

        response = requests.put(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )

        return response.status_code in [200, 201]

    except requests.exceptions.ConnectionError:
        # Backend might not be running - fail silently
        return False
    except Exception as e:
        print(f"Error sending transcript to backend: {str(e)}", file=sys.stderr)
        return False


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract session_id and transcript_path
        session_id = input_data.get('session_id')
        transcript_path = input_data.get('transcript_path')

        if not session_id or not transcript_path:
            sys.exit(0)

        # Parse transcript into structured data
        transcript = parse_transcript(transcript_path)

        # Send to backend
        send_to_backend(session_id, transcript)

        # Always exit successfully to not block session end
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == '__main__':
    main()
