#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

"""
Session End Transcript Hook
Parses Claude Code transcript into human-readable format and sends to backend.
"""

import json
import sys
import requests
from typing import List, Dict, Any
from pathlib import Path


def parse_transcript(transcript_path: str) -> str:
    """
    Parse NDJSON transcript into clean, readable format.
    Returns formatted string with conversation flow.
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

                        conversations.append({
                            'type': 'user',
                            'content': content,
                            'timestamp': timestamp
                        })

                # Parse assistant messages
                elif entry_type == 'assistant':
                    message = entry.get('message', {})
                    if message.get('role') == 'assistant':
                        content_blocks = message.get('content', [])

                        # Extract different content types
                        text_parts = []
                        tool_calls = []

                        for block in content_blocks:
                            block_type = block.get('type')

                            if block_type == 'text':
                                text_parts.append(block.get('text', ''))

                            elif block_type == 'tool_use':
                                tool_calls.append({
                                    'name': block.get('name'),
                                    'input': block.get('input', {})
                                })

                        # Get token usage
                        usage = message.get('usage', {})
                        tokens = usage.get('output_tokens', 0)

                        timestamp = entry.get('timestamp', '')

                        conversations.append({
                            'type': 'assistant',
                            'text': '\n'.join(text_parts) if text_parts else None,
                            'tool_calls': tool_calls if tool_calls else None,
                            'tokens': tokens,
                            'timestamp': timestamp
                        })

        # Format conversations into readable text
        return format_conversations(conversations)

    except FileNotFoundError:
        return f"Error: Transcript file not found at {transcript_path}"
    except Exception as e:
        return f"Error parsing transcript: {str(e)}"


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


def send_to_backend(session_id: str, transcript: str, api_url: str = "http://localhost:3999") -> bool:
    """Send formatted transcript to backend API."""
    try:
        endpoint = f"{api_url}/api/sessions/{session_id}/transcript"
        payload = {
            "sessionId": session_id,
            "transcript": transcript
        }

        response = requests.put(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        return response.status_code in [200, 201]

    except requests.exceptions.ConnectionError:
        # Backend might not be running - fail silently
        return False
    except Exception:
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

        # Parse transcript
        formatted_transcript = parse_transcript(transcript_path)

        # Send to backend
        send_to_backend(session_id, formatted_transcript)

        # Always exit successfully to not block session end
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == '__main__':
    main()
