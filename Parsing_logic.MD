If role is user:
    Check each content item
        If type is text:
            It's a user message
                Create user message object
        else if type is tool_result:
            It's a tool result message
                Create tool result object
        else type is unrecognized
                Create unrecognized type object

If role is assistant:
    Check each content item
        If type is text:
            Split the text into sections by '#'
                For each section:
                    For any text before the first '#':
                        It's an undeclared text message
                            Create undeclared text message object
                    If the section starts with '# OOC Message':
                        It's an OOC message
                            Create OOC message object
                    If the section starts with '# Difficulty analysis':
                        It's a difficulty analysis message
                            Create difficulty analysis message object
                    If the section starts with '# Difficulty target':
                        It's a difficulty target message
                            Create difficulty target message object
                    If the section starts with '# World analysis':
                        It's a world analysis message
                            Create world analysis message object
                    If the section starts with '# World level':
                        It's a world level message
                            Create world level message object
                    If the section starts with '# Resulting Scene Description':
                        It's a resulting scene description message
                            Create resulting scene description message object
                    If the section starts with '# Tracked operations':
                        It's a tracked operations message
                            Create tracked operations message object
                    If the section starts with '# Condition table':
                        It's a condition table message
                            Create condition table message object
                    If the section starts with '# OOC Message':
                        It's an OOC message
                            Create OOC message object
                    Else:
                        It's an unrecognized message
                            Create unrecognized section object
        else if type is tool_use:
            It's a tool use message
                Create tool use object



Bonus: Tell LLM not to use '#' other than for our sectioning system.


