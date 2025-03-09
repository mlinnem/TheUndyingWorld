"""
Tests for message models.

This module tests the message models defined in message_models.py.
"""

import unittest
from .message_models import (
    UserMessage, AssistantMessage, ErrorMessage, TextContent,
    ToolUseContent, ToolResultContent, create_user_message,
    create_error_message, base_message_to_client_format
)


class TestMessageModels(unittest.TestCase):
    """Tests for message models."""

    def test_user_message_creation(self):
        """Test creating a user message."""
        # Create a valid user message
        user_message = UserMessage(
            role="user",
            content=[TextContent(type="text", text="Hello, world!")]
        )
        self.assertEqual(user_message.role, "user")
        self.assertEqual(len(user_message.content), 1)
        self.assertEqual(user_message.content[0].text, "Hello, world!")

        # Test with factory function
        user_message = create_user_message("Hello, world!")
        self.assertEqual(user_message.role, "user")
        self.assertEqual(user_message.content[0].text, "Hello, world!")

    def test_user_message_validation(self):
        """Test validation of user messages."""
        # Test with invalid role
        with self.assertRaises(ValueError):
            UserMessage(
                role="assistant",  # Invalid role for UserMessage
                content=[TextContent(type="text", text="Hello, world!")]
            )

        # Test with empty content
        with self.assertRaises(ValueError):
            UserMessage(
                role="user",
                content=[]
            )

        # Test with no text content
        with self.assertRaises(ValueError):
            UserMessage(
                role="user",
                content=[ToolUseContent(type="tool_use", tool_use={"name": "test"})]
            )

    def test_error_message_creation(self):
        """Test creating an error message."""
        # Create a valid error message
        error_message = ErrorMessage(
            source="server",
            type="error",
            error_type="validation_error",
            error_message="Invalid input"
        )
        self.assertEqual(error_message.source, "server")
        self.assertEqual(error_message.type, "error")
        self.assertEqual(error_message.error_type, "validation_error")
        self.assertEqual(error_message.error_message, "Invalid input")

        # Test with factory function
        error_message = create_error_message(
            error_type="validation_error",
            error_message="Invalid input",
            error_code="VAL_001"
        )
        self.assertEqual(error_message.error_type, "validation_error")
        self.assertEqual(error_message.error_message, "Invalid input")
        self.assertEqual(error_message.error_code, "VAL_001")

    def test_format_conversion(self):
        """Test converting between message formats."""
        # Create a user message
        user_message = create_user_message("Hello, world!")
        
        # Convert to client format
        client_format = base_message_to_client_format(user_message)
        
        # Verify conversion
        self.assertEqual(client_format["source"], "client")
        self.assertEqual(client_format["type"], "user_message")
        self.assertEqual(client_format["user_message"], "Hello, world!")
        self.assertIn("timestamp", client_format)


if __name__ == "__main__":
    unittest.main()