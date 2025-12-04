#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.error
import os
import re
from pathlib import Path


def parse_command_file(file_path):
    """Parse a command markdown file and extract metadata and content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter if present
        frontmatter = {}
        command_content = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Parse frontmatter
                frontmatter_text = parts[1].strip()
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

                # Get content after frontmatter
                command_content = parts[2].strip()

        return {
            'metadata': frontmatter,
            'content': command_content
        }
    except Exception as e:
        print(f"Error parsing command file {file_path}: {e}", file=sys.stderr)
        return None


def collect_project_commands(cwd):
    """Collect all slash commands from .claude/commands/ directory."""
    if not cwd:
        return []

    commands_dir = Path(cwd) / '.claude' / 'commands'
    if not commands_dir.exists():
        return []

    commands = []

    # Recursively find all .md files in commands directory
    for md_file in commands_dir.rglob('*.md'):
        # Get command name and namespace from file path relative to commands dir
        relative_path = md_file.relative_to(commands_dir)

        # Extract namespace (empty string for root, subfolder name for nested commands)
        namespace = ''
        if len(relative_path.parts) > 1:
            # Command is in a subfolder, use the immediate parent folder as namespace
            namespace = relative_path.parts[0]

        # Command name is just the filename without extension
        command_name = relative_path.stem

        # Parse the command file
        parsed = parse_command_file(md_file)
        if parsed:
            commands.append({
                'name': command_name,
                'namespace': namespace,
                'metadata': parsed['metadata'],
                'content': parsed['content']
            })

    return commands


def collect_project_agents(cwd):
    """Collect all agents from .claude/agents/ directory."""
    if not cwd:
        return []

    agents_dir = Path(cwd) / '.claude' / 'agents'
    if not agents_dir.exists():
        return []

    agents = []

    # Recursively find all .md files in agents directory
    for md_file in agents_dir.rglob('*.md'):
        # Get agent name and namespace from file path relative to agents dir
        relative_path = md_file.relative_to(agents_dir)

        # Extract namespace (empty string for root, subfolder name for nested agents)
        namespace = ''
        if len(relative_path.parts) > 1:
            # Agent is in a subfolder, use the immediate parent folder as namespace
            namespace = relative_path.parts[0]

        # Agent name is just the filename without extension
        agent_name = relative_path.stem

        # Parse the agent file
        parsed = parse_command_file(md_file)
        if parsed:
            agents.append({
                'name': agent_name,
                'namespace': namespace,
                'metadata': parsed['metadata'],
                'content': parsed['content']
            })

    return agents


def collect_user_commands():
    """Collect all user-level slash commands from ~/.claude/commands/ directory."""
    home_dir = os.path.expanduser('~')
    commands_dir = Path(home_dir) / '.claude' / 'commands'

    if not commands_dir.exists():
        return []

    commands = []

    # Recursively find all .md files in commands directory
    for md_file in commands_dir.rglob('*.md'):
        # Get command name and namespace from file path relative to commands dir
        relative_path = md_file.relative_to(commands_dir)

        # Extract namespace (empty string for root, subfolder name for nested commands)
        namespace = ''
        if len(relative_path.parts) > 1:
            # Command is in a subfolder, use the immediate parent folder as namespace
            namespace = relative_path.parts[0]

        # Command name is just the filename without extension
        command_name = relative_path.stem

        # Parse the command file
        parsed = parse_command_file(md_file)
        if parsed:
            commands.append({
                'name': command_name,
                'namespace': namespace,
                'metadata': parsed['metadata'],
                'content': parsed['content']
            })

    return commands


def collect_user_agents():
    """Collect all user-level agents from ~/.claude/agents/ directory."""
    home_dir = os.path.expanduser('~')
    agents_dir = Path(home_dir) / '.claude' / 'agents'

    if not agents_dir.exists():
        return []

    agents = []

    # Recursively find all .md files in agents directory
    for md_file in agents_dir.rglob('*.md'):
        # Get agent name and namespace from file path relative to agents dir
        relative_path = md_file.relative_to(agents_dir)

        # Extract namespace (empty string for root, subfolder name for nested agents)
        namespace = ''
        if len(relative_path.parts) > 1:
            # Agent is in a subfolder, use the immediate parent folder as namespace
            namespace = relative_path.parts[0]

        # Agent name is just the filename without extension
        agent_name = relative_path.stem

        # Parse the agent file
        parsed = parse_command_file(md_file)
        if parsed:
            agents.append({
                'name': agent_name,
                'namespace': namespace,
                'metadata': parsed['metadata'],
                'content': parsed['content']
            })

    return agents


def get_git_remote_origin(cwd):
    """Get the git remote origin URL for the project."""
    if not cwd:
        return ''

    try:
        import subprocess
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ''
    except Exception:
        return ''


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract session information
        session_id = input_data.get('session_id', 'unknown')
        session_source = input_data.get('source', 'unknown')
        transcript_path = input_data.get('transcript_path', '')
        cwd = input_data.get('cwd', '')

        # Extract project name from cwd
        project_name = os.path.basename(cwd) if cwd else 'unknown'

        # Read AGENTS.md first, fallback to CLAUDE.md from project directory
        project_memory = ''
        if cwd:
            # Try AGENTS.md first
            agents_md_path = os.path.join(cwd, 'AGENTS.md')
            claude_md_path = os.path.join(cwd, 'CLAUDE.md')

            try:
                with open(agents_md_path, 'r', encoding='utf-8') as f:
                    project_memory = f.read()
            except FileNotFoundError:
                # AGENTS.md doesn't exist, try CLAUDE.md
                try:
                    with open(claude_md_path, 'r', encoding='utf-8') as f:
                        project_memory = f.read()
                except FileNotFoundError:
                    # Neither file exists, leave empty
                    pass
                except Exception as e:
                    # Log but don't fail if we can't read CLAUDE.md
                    print(f"Could not read CLAUDE.md: {e}", file=sys.stderr)
            except Exception as e:
                # Log but don't fail if we can't read AGENTS.md
                print(f"Could not read AGENTS.md: {e}", file=sys.stderr)

        # Read README.md from project directory
        project_readme = ''
        if cwd:
            readme_path = os.path.join(cwd, 'README.md')
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    project_readme = f.read()
            except FileNotFoundError:
                # README.md doesn't exist, leave empty
                pass
            except Exception as e:
                # Log but don't fail if we can't read README.md
                print(f"Could not read README.md: {e}", file=sys.stderr)

        # Collect project commands and agents
        project_commands = collect_project_commands(cwd)
        project_agents = collect_project_agents(cwd)

        # Collect user-level commands and agents
        user_commands = collect_user_commands()
        user_agents = collect_user_agents()

        # Combine commands with level information
        commands = [
            {**cmd, 'level': 'project'} for cmd in project_commands
        ] + [
            {**cmd, 'level': 'user'} for cmd in user_commands
        ]

        # Combine agents with level information
        subagents = [
            {**agent, 'level': 'project'} for agent in project_agents
        ] + [
            {**agent, 'level': 'user'} for agent in user_agents
        ]

        # Get git remote origin URL
        git_repository = get_git_remote_origin(cwd)

        # Prepare payload for API
        payload = {
            'sessionId': session_id,
            'projectPath': cwd,
            'commands': commands,
            'subagents': subagents,
            'memory': project_memory,
            'readme': project_readme,
            'source': session_source,
            'gitRepository': git_repository,
        }

        # Make POST request to localhost:3000/api/sessions
        url = 'http://localhost:3001/api/hooks/session-start'
        headers = {
            'Content-Type': 'application/json'
        }

        # Add Authorization header if API key is set
        api_key = os.environ.get('CLAUDE_INSIGHTS_API_KEY', '')
        if api_key:
            headers['x-api-key'] = api_key

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=5) as response:
            response_data = response.read()
            # Optionally log success
            # print(f"Session {session_id} logged successfully", file=sys.stderr)

        # Success
        sys.exit(0)

    except json.JSONDecodeError as e:
        # Handle JSON decode errors gracefully
        print(f"JSON decode error: {e}", file=sys.stderr)
        sys.exit(0)
    except urllib.error.URLError as e:
        # Handle network errors gracefully (API might not be running)
        print(f"Failed to connect to API: {e}", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        # Handle any other errors gracefully
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()