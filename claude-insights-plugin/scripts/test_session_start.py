#!/usr/bin/env python3
"""Unit tests for session_start.py webhook script."""

import json
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO
import urllib.error

# Import the module under test
sys.path.insert(0, '/Users/jakubpruszynski/WebstormProjects/claude_insights/apps/backend/scripts')
import session_start


class TestSessionStart(unittest.TestCase):
    """Test cases for session_start.py webhook script."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_input = {
            'session_id': 'test-session-123',
            'transcript_path': '/path/to/transcript.json',
            'cwd': '/Users/test/project'
        }
        self.expected_payload = {
            'sessionId': 'test-session-123',
            'projectName': 'project',
            'projectMemory': ''
        }

    @patch('sys.stdin', new_callable=StringIO)
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_successful_session_creation(self, mock_exit, mock_urlopen, mock_file, mock_stdin):
        """Test successful session creation with valid input."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Act
        session_start.main()

        # Assert
        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        self.assertEqual(request.get_full_url(), 'http://localhost:3999/api/sessions')
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.headers['Content-type'], 'application/json')

        sent_data = json.loads(request.data.decode('utf-8'))
        self.assertEqual(sent_data['sessionId'], self.expected_payload['sessionId'])
        self.assertEqual(sent_data['projectName'], self.expected_payload['projectName'])
        self.assertEqual(sent_data['projectMemory'], self.expected_payload['projectMemory'])

        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_session_with_claude_md(self, mock_exit, mock_urlopen, mock_stdin):
        """Test session creation with CLAUDE.md file present (when AGENTS.md doesn't exist)."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock file open to fail on AGENTS.md and README.md, succeed on CLAUDE.md
        def open_side_effect(filename, *args, **kwargs):
            if 'AGENTS.md' in filename or 'README.md' in filename:
                raise FileNotFoundError()
            elif 'CLAUDE.md' in filename:
                return mock_open(read_data='# Project Memory\nThis is test content.')()
            raise FileNotFoundError()

        # Act
        with patch('builtins.open', side_effect=open_side_effect) as mock_file:
            session_start.main()

            # Assert - Should have tried AGENTS.md, CLAUDE.md, and README.md
            self.assertEqual(mock_file.call_count, 3)

            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            sent_data = json.loads(request.data.decode('utf-8'))

            self.assertEqual(sent_data['projectMemory'], '# Project Memory\nThis is test content.')
            mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_session_without_claude_md(self, mock_exit, mock_urlopen, mock_file, mock_stdin):
        """Test session creation when CLAUDE.md doesn't exist."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Act
        session_start.main()

        # Assert
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        sent_data = json.loads(request.data.decode('utf-8'))

        self.assertEqual(sent_data['projectMemory'], '')
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_invalid_json_input(self, mock_exit, mock_stdin):
        """Test graceful handling of invalid JSON input."""
        # Arrange
        mock_stdin.write('not valid json {]')
        mock_stdin.seek(0)

        # Act
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            session_start.main()
            stderr_output = mock_stderr.getvalue()

        # Assert
        self.assertIn('JSON decode error', stderr_output)
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Connection refused'))
    @patch('sys.exit')
    def test_api_connection_failure(self, mock_exit, mock_urlopen, mock_stdin):
        """Test graceful handling when API is not available."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        # Act
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            session_start.main()
            stderr_output = mock_stderr.getvalue()

        # Assert
        self.assertIn('Failed to connect to API', stderr_output)
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_missing_session_id(self, mock_exit, mock_stdin):
        """Test handling of input without session_id."""
        # Arrange
        input_data = {
            'transcript_path': '/path/to/transcript.json',
            'cwd': '/Users/test/project'
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        # Act
        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            session_start.main()

            # Assert
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            sent_data = json.loads(request.data.decode('utf-8'))

            self.assertEqual(sent_data['sessionId'], 'unknown')
            mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_empty_cwd(self, mock_exit, mock_stdin):
        """Test handling of empty cwd field."""
        # Arrange
        input_data = {
            'session_id': 'test-session-123',
            'transcript_path': '/path/to/transcript.json',
            'cwd': ''
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        # Act
        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            session_start.main()

            # Assert
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            sent_data = json.loads(request.data.decode('utf-8'))

            self.assertEqual(sent_data['projectName'], 'unknown')
            mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_claude_md_permission_error(self, mock_exit, mock_urlopen, mock_stdin):
        """Test graceful handling when CLAUDE.md cannot be read due to permissions."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock file open to fail on AGENTS.md (FileNotFoundError), then fail on CLAUDE.md (PermissionError)
        def open_side_effect(filename, *args, **kwargs):
            if 'AGENTS.md' in filename:
                raise FileNotFoundError()
            elif 'CLAUDE.md' in filename:
                raise PermissionError('Permission denied')
            raise FileNotFoundError()

        # Act
        with patch('builtins.open', side_effect=open_side_effect) as mock_file:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                session_start.main()
                stderr_output = mock_stderr.getvalue()

                # Assert
                self.assertIn('Could not read CLAUDE.md', stderr_output)

                call_args = mock_urlopen.call_args
                request = call_args[0][0]
                sent_data = json.loads(request.data.decode('utf-8'))

                # Should still create session with empty projectMemory
                self.assertEqual(sent_data['projectMemory'], '')
                mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_api_timeout(self, mock_exit, mock_urlopen, mock_stdin):
        """Test handling of API timeout."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)
        mock_urlopen.side_effect = urllib.error.URLError('Timeout')

        # Act
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            session_start.main()
            stderr_output = mock_stderr.getvalue()

        # Assert
        self.assertIn('Failed to connect to API', stderr_output)
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_project_name_extraction(self, mock_exit, mock_urlopen, mock_stdin):
        """Test correct extraction of project name from various cwd paths."""
        # Arrange
        test_cases = [
            ('/Users/test/my-project', 'my-project'),
            ('/home/user/workspace/cool_app', 'cool_app'),
            ('/single', 'single')
        ]

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        for cwd, expected_name in test_cases:
            with self.subTest(cwd=cwd):
                # Arrange
                input_data = {
                    'session_id': 'test-session',
                    'cwd': cwd
                }
                mock_stdin.truncate(0)
                mock_stdin.seek(0)
                mock_stdin.write(json.dumps(input_data))
                mock_stdin.seek(0)
                mock_urlopen.reset_mock()

                # Act
                session_start.main()

                # Assert
                call_args = mock_urlopen.call_args
                request = call_args[0][0]
                sent_data = json.loads(request.data.decode('utf-8'))

                self.assertEqual(sent_data['projectName'], expected_name)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_agents_md_priority(self, mock_exit, mock_urlopen, mock_stdin):
        """Test that AGENTS.md is read first when it exists."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock the file open to return AGENTS.md content
        def open_side_effect(filename, *args, **kwargs):
            if 'AGENTS.md' in filename:
                return mock_open(read_data='# Agents Memory\nThis is AGENTS.md content.')()
            elif 'README.md' in filename:
                raise FileNotFoundError()
            raise FileNotFoundError()

        with patch('builtins.open', side_effect=open_side_effect) as mock_file:
            # Act
            session_start.main()

            # Assert
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            sent_data = json.loads(request.data.decode('utf-8'))

            self.assertEqual(sent_data['projectMemory'], '# Agents Memory\nThis is AGENTS.md content.')
            mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_fallback_to_claude_md(self, mock_exit, mock_urlopen, mock_stdin):
        """Test that CLAUDE.md is used when AGENTS.md doesn't exist."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock file open to fail on AGENTS.md and README.md, succeed on CLAUDE.md
        def open_side_effect(filename, *args, **kwargs):
            if 'AGENTS.md' in filename or 'README.md' in filename:
                raise FileNotFoundError()
            elif 'CLAUDE.md' in filename:
                return mock_open(read_data='# Claude Memory\nThis is CLAUDE.md content.')()
            raise FileNotFoundError()

        with patch('builtins.open', side_effect=open_side_effect) as mock_file:
            # Act
            session_start.main()

            # Assert - Should have tried AGENTS.md, CLAUDE.md, and README.md
            self.assertEqual(mock_file.call_count, 3)

            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            sent_data = json.loads(request.data.decode('utf-8'))

            self.assertEqual(sent_data['projectMemory'], '# Claude Memory\nThis is CLAUDE.md content.')
            mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_neither_agents_nor_claude_md_exists(self, mock_exit, mock_urlopen, mock_file, mock_stdin):
        """Test that empty projectMemory is used when neither AGENTS.md nor CLAUDE.md exist."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Act
        session_start.main()

        # Assert - Should have tried AGENTS.md, CLAUDE.md, and README.md
        self.assertEqual(mock_file.call_count, 3)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        sent_data = json.loads(request.data.decode('utf-8'))

        self.assertEqual(sent_data['projectMemory'], '')
        self.assertEqual(sent_data['projectReadme'], '')
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('builtins.open', side_effect=PermissionError('Permission denied'))
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_agents_md_permission_error(self, mock_exit, mock_urlopen, mock_file, mock_stdin):
        """Test graceful handling when AGENTS.md cannot be read due to permissions."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Act
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            session_start.main()
            stderr_output = mock_stderr.getvalue()

        # Assert
        self.assertIn('Could not read AGENTS.md', stderr_output)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        sent_data = json.loads(request.data.decode('utf-8'))

        # Should still create session with empty projectMemory
        self.assertEqual(sent_data['projectMemory'], '')
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_readme_md_reading(self, mock_exit, mock_urlopen, mock_stdin):
        """Test that README.md is read when it exists."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock file open to return README.md content
        def open_side_effect(filename, *args, **kwargs):
            if 'AGENTS.md' in filename or 'CLAUDE.md' in filename:
                raise FileNotFoundError()
            elif 'README.md' in filename:
                return mock_open(read_data='# Project README\nThis is README.md content.')()
            raise FileNotFoundError()

        with patch('builtins.open', side_effect=open_side_effect) as mock_file:
            # Act
            session_start.main()

            # Assert
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            sent_data = json.loads(request.data.decode('utf-8'))

            self.assertEqual(sent_data['projectReadme'], '# Project README\nThis is README.md content.')
            mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_readme_md_not_exists(self, mock_exit, mock_urlopen, mock_file, mock_stdin):
        """Test that empty projectReadme is used when README.md doesn't exist."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Act
        session_start.main()

        # Assert
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        sent_data = json.loads(request.data.decode('utf-8'))

        self.assertEqual(sent_data['projectReadme'], '')
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_readme_md_permission_error(self, mock_exit, mock_urlopen, mock_stdin):
        """Test graceful handling when README.md cannot be read due to permissions."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock file open to fail on all files with PermissionError for README.md
        def open_side_effect(filename, *args, **kwargs):
            if 'AGENTS.md' in filename or 'CLAUDE.md' in filename:
                raise FileNotFoundError()
            elif 'README.md' in filename:
                raise PermissionError('Permission denied')
            raise FileNotFoundError()

        # Act
        with patch('builtins.open', side_effect=open_side_effect) as mock_file:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                session_start.main()
                stderr_output = mock_stderr.getvalue()

                # Assert
                self.assertIn('Could not read README.md', stderr_output)

                call_args = mock_urlopen.call_args
                request = call_args[0][0]
                sent_data = json.loads(request.data.decode('utf-8'))

                # Should still create session with empty projectReadme
                self.assertEqual(sent_data['projectReadme'], '')
                mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()