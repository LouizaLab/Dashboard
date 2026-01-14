#!/usr/bin/env python3
"""
Helper script to manually add conversation transcripts.

Since agent conversations aren't available via REST API, use this script
to format and save manually copied transcripts.

Usage:
    python 11_labs_ingestion/add_manual_transcript.py
    
    Then follow the prompts to enter conversation details.
"""

import sys
from pathlib import Path
from datetime import datetime

def main():
    """Interactive script to add manual transcripts."""
    script_dir = Path(__file__).parent.resolve()
    incoming_dir = script_dir / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print("Manual Transcript Adder")
    print("="*70)
    print()

    # Get conversation details
    conversation_id = input("Conversation ID (or press Enter to generate): ").strip()
    if not conversation_id:
        conversation_id = f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    date_str = input(f"Date (YYYY-MM-DD) [default: {datetime.now().strftime('%Y-%m-%d')}]: ").strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')

    agent_name = input("Agent name (optional): ").strip()
    duration = input("Duration (e.g., 4:03, optional): ").strip()
    message_count = input("Message count (optional): ").strip()
    call_status = input("Call status (e.g., Successful, optional): ").strip()

    print()
    print("Paste the transcript content below.")
    print("Press Enter, then paste, then press Ctrl+D (Mac/Linux) or Ctrl+Z+Enter (Windows) to finish:")
    print("-"*70)

    # Read transcript content
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    transcript_text = '\n'.join(lines).strip()

    if not transcript_text:
        print("Error: No transcript content provided")
        sys.exit(1)

    # Create filename
    filename = f"{conversation_id}__{date_str}.txt"
    filepath = incoming_dir / filename

    # Build content
    content_parts = []

    # Add metadata
    if agent_name:
        content_parts.append(f"Agent: {agent_name}\n")
    if duration:
        content_parts.append(f"Duration: {duration}\n")
    if message_count:
        content_parts.append(f"Messages: {message_count}\n")
    if call_status:
        content_parts.append(f"Status: {call_status}\n")
    content_parts.append(f"Date: {date_str}\n")
    content_parts.append(f"ID: {conversation_id}\n")
    content_parts.append("\n" + "="*70 + "\n")
    content_parts.append("Transcript:\n")
    content_parts.append("="*70 + "\n\n")
    content_parts.append(transcript_text)

    # Write file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(content_parts))

        print()
        print("="*70)
        print("✓ Success!")
        print("="*70)
        print(f"File saved: {filepath}")
        print(f"Size: {filepath.stat().st_size} bytes")
        print()
        print("The watcher will detect this file automatically if it's running.")
        print("Or process it manually by moving to processed/ folder.")

    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

