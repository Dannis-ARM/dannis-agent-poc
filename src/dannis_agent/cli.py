"""Command line interface for the ReAct Agent."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from colorama import Fore, Style
from dotenv import load_dotenv

from .agent import ReActAgent, save_log
from .memory import SessionManager

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


def main():
    parser = argparse.ArgumentParser(description="ReAct Agent Demo")
    parser.add_argument("query", nargs="*", help="User query (if not provided, enter interactive mode)")
    parser.add_argument("--unsafe", action="store_true", help="Disable safety restrictions (use with caution)")
    parser.add_argument("--quiet", action="store_true", help="Disable verbose output")
    parser.add_argument("--max-iter", type=int, default=10, help="Max iterations (default: 10)")
    parser.add_argument("--no-log", action="store_true", help="Don't save conversation log")
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming output")
    parser.add_argument("--list-sessions", action="store_true", help="List recent sessions")
    parser.add_argument("--resume", type=str, metavar="SESSION_ID", help="Resume a specific session")
    parser.add_argument("--resume-last", action="store_true", help="Resume the most recent session")
    parser.add_argument("--new-session", action="store_true", help="Start a new session (default)")

    args = parser.parse_args()

    load_dotenv()

    api_key = os.getenv("DOUBAO_API_KEY")
    if not api_key:
        print(f"{Fore.RED}Error: DOUBAO_API_KEY not set in .env{Style.RESET_ALL}")
        sys.exit(1)

    base_url = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding")
    model = os.getenv("DOUBAO_MODEL", "doubao-seed-2-0-code-preview-latest")

    session_mgr = SessionManager()

    # Handle --list-sessions
    if args.list_sessions:
        sessions = session_mgr.list_sessions()
        if sessions:
            print(f"\n{Fore.CYAN}Recent sessions:{Style.RESET_ALL}")
            for i, sid in enumerate(sessions, 1):
                sf = session_mgr.memory_dir / f"session-{sid}.jsonl"
                size = sf.stat().st_size
                print(f"  {i}. {sid}  ({size} bytes)")
        else:
            print(f"{Fore.YELLOW}No sessions found.{Style.RESET_ALL}")
        return

    # Resolve session ID
    if args.resume:
        session_id = args.resume
        if not session_mgr.session_exists(session_id):
            print(f"{Fore.RED}Error: Session {session_id} not found.{Style.RESET_ALL}")
            sys.exit(1)
    elif args.resume_last:
        session_id = session_mgr.get_latest_session()
        if not session_id:
            print(f"{Fore.YELLOW}No previous sessions to resume. Starting new session.{Style.RESET_ALL}")
            session_id = session_mgr.create_new_session()
    else:
        session_id = session_mgr.create_new_session()

    agent = ReActAgent(
        api_key=api_key,
        base_url=base_url,
        model=model,
        unsafe_mode=args.unsafe,
        verbose=not args.quiet,
        streaming=not args.no_streaming
    )

    # Load existing session messages into agent
    existing_messages = session_mgr.to_agent_messages(session_id)
    if existing_messages:
        agent.messages = existing_messages
        if not args.quiet:
            print(f"{Fore.CYAN}Resumed session: {session_id} ({len(existing_messages)} messages){Style.RESET_ALL}")

    if args.query:
        query = " ".join(args.query)
        result = agent.run(query, max_iterations=args.max_iter)
        # Save to session
        timestamp = datetime.now().isoformat()
        session_mgr.append_message(session_id, "user", query, timestamp)
        session_mgr.append_message(session_id, "assistant", result, timestamp)
        if not args.no_log:
            save_log(agent.messages)
        print()
    else:
        if not args.resume and not args.resume_last:
            print(f"{Fore.CYAN}Session: {session_id}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╔════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║     ReAct Agent Interactive Mode       ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║  Type 'exit' or 'quit' to exit         ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚════════════════════════════════════════╝{Style.RESET_ALL}")
        print()

        while True:
            try:
                query = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    break

                timestamp = datetime.now().isoformat()
                result = agent.run(query, max_iterations=args.max_iter)
                # Save to session
                session_mgr.append_message(session_id, "user", query, timestamp)
                session_mgr.append_message(session_id, "assistant", result, timestamp)
                print()
            except KeyboardInterrupt:
                print("\n^C")
                break
            except EOFError:
                print()
                break

        if not args.no_log:
            save_log(agent.messages)


if __name__ == "__main__":
    main()
