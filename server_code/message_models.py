"""
Message models for validating and converting message structures.

This module defines Pydantic models for various message types used in the application.
These models provide validation, type checking, and conversion methods to ensure
consistent message handling throughout the application.
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Literal, Union, Annotated
from pydantic import BaseModel, Field, field_validator, model_validator, RootModel


class MessageRole(str, Enum):
    """Enumeration of valid message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageContentType(str, Enum):
    """Enumeration of valid message content types."""
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class MessageSource(str, Enum):
    """Enumeration of valid message sources."""
    CLIENT = "client"
    SERVER = "server"
    LLM = "llm"


class TextContent(BaseModel):
    """Model for text content in a message."""
    type: Literal["text"]
    text: str


class ToolUseContent(BaseModel):
    """Model for tool use content in a message."""
    type: Literal["tool_use"]
    tool_use: Dict[str, Any]  # Tool use details vary


class ToolResultContent(BaseModel):
    """Model for tool result content in a message."""
    type: Literal["tool_result"]
    content: str  # Tool result content


class MessageContent(RootModel):
    """Union model for different types of message content."""
    root: Union[TextContent, ToolUseContent, ToolResultContent]


class BaseMessage(BaseModel):
    """Base model for all message types."""
    role: MessageRole
    content: List[Union[TextContent, ToolUseContent, ToolResultContent]]


class UserMessage(BaseMessage):
    """Model for user messages."""
    role: Literal[MessageRole.USER]
    
    @field_validator('content')
    def validate_content(cls, v):
        """Validate that user messages have appropriate content."""
        if not v:
            raise ValueError("User message must have content")
        if not any(c.type == "text" for c in v):
            raise ValueError("User message must have at least one text content")
        return v


class AssistantMessage(BaseMessage):
    """Model for assistant messages."""
    role: Literal[MessageRole.ASSISTANT]


class SystemMessage(BaseMessage):
    """Model for system messages."""
    role: Literal[MessageRole.SYSTEM]


class ClientMessage(BaseModel):
    """Model for messages to/from the client."""
    source: Literal[MessageSource.CLIENT]
    type: str
    user_message: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ServerMessage(BaseModel):
    """Model for messages from the server."""
    source: Literal[MessageSource.SERVER]
    type: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    

class LLMMessage(BaseModel):
    """Model for messages from the LLM."""
    source: Literal[MessageSource.LLM]
    type: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ErrorMessage(ServerMessage):
    """Model for error messages."""
    type: Literal["error"]
    error_type: str
    error_message: str
    original_message: Optional[Any] = None
    error_context: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


# Factory functions to create validated message objects

def create_user_message(text: str) -> UserMessage:
    """
    Create a validated user message.
    
    Args:
        text: The text content of the message
        
    Returns:
        UserMessage: A validated user message object
    """
    return UserMessage(
        role=MessageRole.USER,
        content=[TextContent(type="text", text=text)]
    )


def create_error_message(
    error_type: str,
    error_message: str,
    original_message: Optional[Any] = None,
    error_context: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None
) -> ErrorMessage:
    """
    Create a validated error message.
    
    Args:
        error_type: Category of error
        error_message: Human-readable error description
        original_message: The original message that caused the error
        error_context: Additional context about the error
        error_code: Machine-readable error code
        
    Returns:
        ErrorMessage: A validated error message object
    """
    return ErrorMessage(
        source=MessageSource.SERVER,
        type="error",
        error_type=error_type,
        error_message=error_message,
        original_message=original_message,
        error_context=error_context,
        error_code=error_code,
        timestamp=datetime.now()
    )


# Conversion functions between message formats

def base_message_to_client_format(message: BaseMessage) -> Dict:
    """Convert a BaseMessage to the client format dictionary."""
    if isinstance(message, UserMessage):
        text_content = next(c for c in message.content if c.type == "text")
        return {
            "source": "client",
            "type": "user_message",
            "user_message": text_content.text,
            "timestamp": datetime.now().isoformat()
        }
    elif isinstance(message, AssistantMessage):
        # Handle different assistant message types
        # This would need to be expanded based on all the possible assistant message types
        text_content = next((c for c in message.content if c.type == "text"), None)
        if text_content:
            return {
                "source": "llm",
                "type": "ooc_message",
                "ooc_message": text_content.text,
                "timestamp": datetime.now().isoformat()
            }
    
    # Default fallback for other message types
    return {
        "source": "server",
        "type": "unknown",
        "message": str(message),
        "timestamp": datetime.now().isoformat()
    }