#!/usr/bin/env python3
"""Unit tests for user_prompt_submit.py webhook script."""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Import the module under test
sys.path.insert(0, '/Users/jakubpruszynski/WebstormProjects/claude_insights/apps/backend/scripts')
import user_prompt_submit


class TestUserPromptSubmit(unittest.TestCase):
    """Test cases for user_prompt_submit.py webhook script."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_input = {
            'session_id': 'test-session-123',
            'prompt': 'Help me write a function'
        }

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_successful_message_send(self, mock_exit, mock_stdin, mock_post):
        """Test successful user message submission."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_called_once_with(
            'http://localhost:3999/api/sessions/test-session-123/message',
            json={
                'sessionId': 'test-session-123',
                'userMessage': 'Help me write a function'
            },
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_successful_message_send_201(self, mock_exit, mock_stdin, mock_post):
        """Test successful user message submission with 201 status."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_api_error_does_not_block(self, mock_exit, mock_stdin, mock_post):
        """Test that API errors don't block the prompt."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_called_once()
        mock_exit.assert_called_once_with(0)  # Should still exit successfully

    @patch('requests.post', side_effect=Exception('Network error'))
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_network_exception_does_not_block(self, mock_exit, mock_stdin, mock_post):
        """Test that network exceptions don't block the prompt."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_called_once()
        mock_exit.assert_called_once_with(0)  # Should still exit successfully

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_missing_session_id(self, mock_exit, mock_stdin, mock_post):
        """Test handling of input without session_id."""
        # Arrange
        input_data = {
            'prompt': 'Help me write a function'
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_not_called()  # Should not make API call without session_id
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_missing_prompt(self, mock_exit, mock_stdin, mock_post):
        """Test handling of input without prompt."""
        # Arrange
        input_data = {
            'session_id': 'test-session-123'
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_not_called()  # Should not make API call without prompt
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_empty_prompt(self, mock_exit, mock_stdin, mock_post):
        """Test handling of empty prompt."""
        # Arrange
        input_data = {
            'session_id': 'test-session-123',
            'prompt': ''
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        # Act
        user_prompt_submit.main()

        # Assert
        mock_post.assert_not_called()  # Should not make API call with empty prompt
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_invalid_json_does_not_block(self, mock_exit, mock_stdin):
        """Test that invalid JSON doesn't block the prompt."""
        # Arrange
        mock_stdin.write('not valid json {]')
        mock_stdin.seek(0)

        # Act
        user_prompt_submit.main()

        # Assert
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_timeout_does_not_block(self, mock_exit, mock_stdin, mock_post):
        """Test that timeout errors don't block the prompt."""
        # Arrange
        mock_stdin.write(json.dumps(self.valid_input))
        mock_stdin.seek(0)
        mock_post.side_effect = TimeoutError('Request timeout')

        # Act
        user_prompt_submit.main()

        # Assert
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    def test_send_user_message_function(self, mock_post):
        """Test the send_user_message function directly."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        result = user_prompt_submit.send_user_message(
            'test-session',
            'Test message',
            'http://localhost:3999'
        )

        # Assert
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://localhost:3999/api/sessions/test-session/message',
            json={
                'sessionId': 'test-session',
                'userMessage': 'Test message'
            },
            headers={'Content-Type': 'application/json'},
            timeout=5
        )

    @patch('requests.post')
    def test_send_user_message_with_custom_url(self, mock_post):
        """Test send_user_message with custom API URL."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        # Act
        result = user_prompt_submit.send_user_message(
            'test-session',
            'Test message',
            'http://custom-host:8080'
        )

        # Assert
        self.assertTrue(result)
        call_args = mock_post.call_args
        self.assertEqual(
            call_args[1]['json']['sessionId'],
            'test-session'
        )
        self.assertIn('custom-host:8080', call_args[0][0])

    @patch('requests.post')
    def test_send_user_message_failure(self, mock_post):
        """Test send_user_message returns False on failure."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Act
        result = user_prompt_submit.send_user_message(
            'test-session',
            'Test message'
        )

        # Assert
        self.assertFalse(result)

    @patch('requests.post', side_effect=Exception('Connection error'))
    def test_send_user_message_exception(self, mock_post):
        """Test send_user_message returns False on exception."""
        # Act
        result = user_prompt_submit.send_user_message(
            'test-session',
            'Test message'
        )

        # Assert
        self.assertFalse(result)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_special_characters_in_prompt(self, mock_exit, mock_stdin, mock_post):
        """Test handling of special characters in prompt."""
        # Arrange
        input_data = {
            'session_id': 'test-session-123',
            'prompt': 'Help me with "quotes" and \'apostrophes\' and\nnewlines'
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        user_prompt_submit.main()

        # Assert
        call_args = mock_post.call_args
        sent_payload = call_args[1]['json']
        self.assertEqual(
            sent_payload['userMessage'],
            'Help me with "quotes" and \'apostrophes\' and\nnewlines'
        )
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_long_prompt(self, mock_exit, mock_stdin, mock_post):
        """Test handling of very long prompts."""
        # Arrange
        long_prompt = 'A' * 10000  # 10KB prompt
        input_data = {
            'session_id': 'test-session-123',
            'prompt': long_prompt
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        user_prompt_submit.main()

        # Assert
        call_args = mock_post.call_args
        sent_payload = call_args[1]['json']
        self.assertEqual(sent_payload['userMessage'], long_prompt)
        mock_exit.assert_called_once_with(0)

    @patch('requests.post')
    @patch('sys.stdin', new_callable=StringIO)
    @patch('sys.exit')
    def test_unicode_characters(self, mock_exit, mock_stdin, mock_post):
        """Test handling of Unicode characters in prompt."""
        # Arrange
        input_data = {
            'session_id': 'test-session-123',
            'prompt': 'Help me with emoji 🚀 and Chinese 你好 and Arabic مرحبا'
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        user_prompt_submit.main()

        # Assert
        call_args = mock_post.call_args
        sent_payload = call_args[1]['json']
        self.assertIn('🚀', sent_payload['userMessage'])
        self.assertIn('你好', sent_payload['userMessage'])
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()