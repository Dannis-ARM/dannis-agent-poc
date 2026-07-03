# ADR 0001: Session Management with Resume

Date: 2025-07-03

## Status

Proposed

## Context

The current ReAct Agent has no memory between runs. Each query is independent,
even in interactive mode. Users want the ability to resume conversations across
restarts.

## Decision

Implement session management with the following characteristics:

1. **Session Files**: Store each session in a separate JSONL file at
   `memory/session-{SESSION_ID}.jsonl`

2. **Session ID Format**: `YYYYMMDD-HHMMSS` (timestamp of session start)

3. **Session Content**: Only store user queries and final assistant answers,
   not intermediate ReAct steps (Thought/Action/Observation)

4. **Session Management CLI**:
   - Default: start a new session
   - `--list-sessions`: list recent sessions
   - `--resume SESSION_ID`: resume a specific session
   - `--resume-last`: resume the most recent session

5. **Full Restore**: When resuming, load all historical messages into the
   Agent's context with no truncation

6. **Continuous Conversation**: Within a single session, each subsequent
   user query automatically includes all previous conversation history

7. **Separate SessionManager Class**: Handle session persistence separately
   from ReActAgent logic to keep concerns separated

## Consequences

### Positive

- Clear separation of concerns between agent logic and session persistence
- Sessions are human-readable JSONL files
- Easy to inspect or manually edit session history
- No breaking changes to ReActAgent API

### Negative

- Duplicates some functionality with the existing `logs/` directory
- No automatic cleanup of old sessions
- No truncation could potentially hit context window limits for very long sessions
- Intermediate ReAct steps are not persisted, making debugging harder

## Alternatives Considered

1. **Single JSONL file for all sessions**: Rejected for performance and
   complexity with concurrent sessions

2. **Store full ReAct steps**: Rejected to keep session files focused on
   user-facing conversation

3. **Integrate into ReActAgent**: Rejected to keep Agent class focused on
   its core ReAct logic

4. **Truncated restore**: Rejected for now to keep things simple; can be added
   later if needed
