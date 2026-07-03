# Context

## Glossary

### Agent
A ReAct pattern AI assistant that uses tools to accomplish tasks.

### Memory
The ability of an Agent to remember past conversations and interactions.

### Short-term Memory
Temporary memory that lasts only for the duration of a single interactive session. All messages within the session are retained in memory and passed to the LLM for context.

### Session
A single interactive session, starting when the Agent enters interactive mode and ending when the user exits.

### Session ID
A unique identifier for an interactive session, automatically generated on startup in the format `YYYYMMDD-HHMMSS`.

### Session File
A JSONL file (`memory/session-{SESSION_ID}.jsonl`) storing all messages for a specific session in chronological order.

### Session History
All messages exchanged during a single interactive session.

### Resume Session
The ability to continue a previous session by loading its session file.

### Current Session
The active session that the Agent is currently participating in.

### Session Management CLI
Command-line arguments for session handling:
- Default: start a new session
- `--list-sessions`: list recent sessions
- `--resume SESSION_ID`: resume a specific session
- `--resume-last`: resume the most recent session

### Session Message Format
Simplified message format stored in session files:
- `role`: "user" or "assistant"
- `content`: the actual message content
- `timestamp`: ISO format timestamp of when the message was sent
Only user queries and final assistant answers are stored, not intermediate ReAct steps.

### Full Session Restore
When resuming a session, all historical messages are loaded into the Agent's context and passed to the LLM, providing complete conversation history. No truncation or summarization is applied.

### Continuous Conversation
Within a single session, each subsequent user query includes all previous conversation history as context for the LLM.
