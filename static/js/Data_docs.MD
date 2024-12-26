# Anthropic notions

## Message

This is one full turn taken by either the user or the assistant.

Messages have a role, which is either "user" or "assistant", and a content field, which is an array of content blocks.

## Content block

Content blocks are the basic units of information in a message. They can be of various types, each serving a specific purpose in the conversation.

* text: a string of text.
* tool_use: a tool use block.
* tool_result: a tool result block.

## Content block classifications

We classifying content blocks into different types, so that we can render them differently in the frontend.

In some cases, we then further divide content blocks into sections, so that we can handle them differently in the frontend. Sections are divided by a `#` in the content block, and have a header on a single line after the `#`. The value of the header is the subsequent content after the header line, and before any new `#` in the content block.

### User message

A user message is a message that is sent by the user.

No sections.

### OOC message

An OOC message is a message that is a message from the system to the user that isn't part of the in-game conversation. It can either communicate system status, or provide information to the user that is relevant to the in-game conversation.

No sections.

### Analysis block

An analysis block is a block that contains an analysis of the situation.

Should contain a difficulty analysis, difficulty target, world analysis, and a world level section. Sections will be converted into objects when provided to the frontend.

### Roll block

A roll block is a block that contains a roll of the dice.

Should contain a difficulty roll, and/or a world roll section.

### Response block

A response block is a block that contains a response to the user.

Should contain a 'resulting scene description' section, a 'tracked operations' section, and a 'condition table' section.

### Map data block

A map data block is a block that contains map data for the game.

May be of the sub-types 'map', 'zones', or 'quadrants'.
# Server notions

The server is the one that handles the conversation, and the one that sends messages to the client.

## Backend conversation

A conversation is the list of messages, as well as some metadata. This represents the state of the conversation. It is persisted in the server. It is stored in a format native to anthropic so that it can be sent to the LLM.

## Backend conversation metadata

This is the metadata that is persisted for a conversation. It includes the conversation_id, the last_updated timestamp, and the conversation_title.


## Responses

A response is a message that is sent by the server to the client.

Responses will have the following fields:

* conversation_id: the id of the conversation.
* conversation_name: the name of the conversation.
* conversation_objects: the objects that are part of the conversation.
* parsing_errors: the errors that occurred when parsing the conversation (if any).

Responses may have the following fields:

* new_messages: the new messages that are part of the conversation.
* error_type: the type of error that occurred.
* error_message: the message of the error.

# Client notions

The client is the one that displays the conversation, and the one that sends messages to the server.

## Frontend conversation

This is the conversation that is displayed to the user. It is a structured version of the conversation, with content blocks parsed into objects.

## Frontend conversation objects

### User message
{
    "source": "user" {
    "type": "user_message",
    "user_message": "Run for the hills!"
}

### Difficulty analysis
{
    "source": "llm",
    "type": "difficulty_analysis",
    "difficulty_analysis": "The difficulty of the problem is 30%."
    "difficulty_target": 30
}

### World analysis

{
    "source": "llm",
    "type": "world_analysis",
    "world_analysis": "Super important stuff to reveal"
    "world_level": "Strong"
}

### World roll

{
    "source": "server",
    "type": "world_roll",
    "world_roll": 34
}

### Difficulty roll

{
    "source": "server",
    "type": "difficulty_roll",
    "world_roll": 34
}

### Resulting scene description
{
    "source": "llm",
    "type": "resulting_scene_description",
    "resulting_scene_description": "You run for the hills and find a safe place to hide."
}

### Tracked operations

{
    "source": "llm",
    "type": "resulting_scene_description",
    "resulting_scene_description": "You run for the hills and find a safe place to hide."
}

### Tracked operations

{
    "source": "llm",
    "type": "tracked_operations",
    "tracked_operations": "MOVE_LOCATION(hills)"
}

### Condition table

{
    "source": "llm",
    "type": "condition_table",
    "condition_table": "Condition: Tired"
}

### Client error

{
    "source": "client",
    "type": "error",
    "error_message": "An error occurred on the client."
}

### Server error

{
    "source": "server",
    "type": "error",
    "error_type": "some_error_type",
    "error_message": "A certain error occurred on the server."
}

### OOC message

An OOC message is a message that is a message from the system to the user that isn't part of the in-game conversation. It can either communicate system status, or provide information to the user that is relevant to the in-game conversation.

{
    "source": "llm",
    "type": "ooc_message",
    "ooc_message": "You do not have a sandwich in your inventory."
}
