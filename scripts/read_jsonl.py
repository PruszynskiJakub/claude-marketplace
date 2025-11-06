#!/usr/bin/env python3
"""
Script to read and print JSONL file content
"""
import json
import sys
from pathlib import Path


def read_jsonl(file_path):
    """Read and print JSONL file line by line, extracting structured data for user/assistant messages"""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Reading file: {file_path}")
    print("=" * 80)

    line_number = 0
    filtered_count = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            line_number += 1
            try:
                data = json.loads(line)

                # Skip lines with isMeta: true
                if data.get('isMeta') is True:
                    continue

                # Check if this line has a message field
                if 'message' not in data:
                    continue

                message = data['message']
                timestamp = data.get('timestamp')

                # Filter: only include user or assistant roles
                if isinstance(message, dict):
                    role = message.get('role')

                    if role == 'user':
                        # For user: { role, content, timestamp } - only text content
                        content = message.get('content')

                        # If content is a string, use it directly
                        if isinstance(content, str):
                            content_str = content
                        # If content is an array, extract only text items
                        elif isinstance(content, list):
                            text_items = []
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text_items.append(item.get('text'))
                            content_str = '\n'.join(text_items) if text_items else None
                        else:
                            content_str = None

                        # Only include if there's text content
                        if content_str:
                            filtered_count += 1
                            extracted = {
                                'role': role,
                                'content': content_str,
                                'timestamp': timestamp
                            }
                            print(f"\n--- Line {line_number} (Filtered #{filtered_count}) ---")
                            print(json.dumps(extracted, indent=2, ensure_ascii=False))
                            print()

                    elif role == 'assistant':
                        # For assistant: extract text or thinking from content array
                        filtered_count += 1
                        content_array = message.get('content', [])

                        # Extract content based on type
                        extracted_content = []
                        for item in content_array:
                            if isinstance(item, dict):
                                if item.get('type') == 'text':
                                    extracted_content.append(item.get('text'))
                                elif item.get('type') == 'thinking':
                                    extracted_content.append(item.get('thinking'))

                        # Join multiple content items or use the first one
                        content_str = '\n'.join(extracted_content) if extracted_content else None

                        if content_str:
                            extracted = {
                                'role': role,
                                'content': content_str,
                                'timestamp': timestamp
                            }
                            print(f"\n--- Line {line_number} (Filtered #{filtered_count}) ---")
                            print(json.dumps(extracted, indent=2, ensure_ascii=False))
                            print()

            except json.JSONDecodeError as e:
                print(f"\n--- Line {line_number} (Parse Error) ---")
                print(f"Error: {e}")
                print(f"Raw content: {line[:200]}...")
                print()

    print("=" * 80)
    print(f"Total lines processed: {line_number}")
    print(f"Filtered messages shown: {filtered_count}")


if __name__ == "__main__":
    # Default file path
    file_path = "test/0b6f97dd-0c6e-4df9-8263-c905a17c7d8e.jsonl"

    # Allow command line argument to override
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    read_jsonl(file_path)