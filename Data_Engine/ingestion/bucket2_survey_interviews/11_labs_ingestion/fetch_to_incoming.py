#!/usr/bin/env python3
"""
Fetch ElevenLabs transcripts and save them to 11_labs_ingestion/incoming/

This script attempts to fetch transcripts from the ElevenLabs API.
Since agent conversations may not be available via REST API, it also
provides instructions for manual export.

Usage:
    python 11_labs_ingestion/fetch_to_incoming.py
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.elevenlabs.io/v1"


class TranscriptManager:
    """Manages transcript files and index."""

    def __init__(self, output_dir: Path):
        """Initialize transcript manager."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.output_dir / "downloaded_ids.json"
        self.downloaded_ids = self._load_index()

    def _load_index(self) -> set:
        """Load set of already downloaded transcript IDs."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get("downloaded_ids", []))
            except Exception as e:
                logger.warning(f"Could not load index file: {e}")
        return set()

    def _save_index(self):
        """Save downloaded IDs to index file."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump({"downloaded_ids": list(self.downloaded_ids)}, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save index file: {e}")

    def is_downloaded(self, item_id: str) -> bool:
        """Check if transcript is already downloaded."""
        return item_id in self.downloaded_ids

    def get_filename(self, item_id: str, timestamp: datetime = None, suffix: str = "txt") -> Path:
        """Generate filename for transcript."""
        if timestamp:
            date_str = timestamp.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        filename = f"{item_id}__{date_str}.{suffix}"
        return self.output_dir / filename

    def save_transcript(
        self,
        item_id: str,
        metadata: Dict[str, Any],
        text: str,
        suffix: str = "txt"
    ) -> bool:
        """Save transcript to file."""
        # Check if already downloaded
        if self.is_downloaded(item_id):
            logger.info(f"⏭️  Skipping {item_id} (already downloaded)")
            return False

        # Generate filename
        timestamp = None
        if metadata.get("date_unix"):
            try:
                timestamp = datetime.fromtimestamp(metadata["date_unix"])
            except:
                pass
        elif metadata.get("created_at"):
            try:
                timestamp = datetime.fromisoformat(str(metadata["created_at"]).replace('Z', '+00:00'))
            except:
                pass

        filepath = self.get_filename(item_id, timestamp, suffix)

        # Check if file already exists
        if filepath.exists():
            logger.info(f"⏭️  Skipping {item_id} (file exists: {filepath.name})")
            self.downloaded_ids.add(item_id)
            self._save_index()
            return False

        # Build content with metadata header
        content_parts = []

        # Add metadata
        if metadata.get("agent_name"):
            content_parts.append(f"Agent: {metadata['agent_name']}\n")
        if metadata.get("voice_name"):
            content_parts.append(f"Voice: {metadata['voice_name']}\n")
        if metadata.get("model_id"):
            content_parts.append(f"Model: {metadata['model_id']}\n")
        if metadata.get("duration"):
            content_parts.append(f"Duration: {metadata['duration']}\n")
        if metadata.get("message_count"):
            content_parts.append(f"Messages: {metadata['message_count']}\n")
        if metadata.get("call_status"):
            content_parts.append(f"Status: {metadata['call_status']}\n")
        if timestamp:
            content_parts.append(f"Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        content_parts.append(f"ID: {item_id}\n")
        content_parts.append("\n" + "="*70 + "\n")
        content_parts.append("Transcript:\n")
        content_parts.append("="*70 + "\n\n")

        # Add transcript text
        content_parts.append(text)

        # Write file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(''.join(content_parts))

            # Update index
            self.downloaded_ids.add(item_id)
            self._save_index()

            logger.info(f"✅ Saved: {filepath.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving {item_id}: {e}")
            return False


def extract_transcript_text(item: Dict[str, Any]) -> str:
    """Extract transcript text from history item or conversation."""
    # Try dialogue field first (for conversation transcripts)
    dialogue = item.get("dialogue")
    if dialogue:
        if isinstance(dialogue, list):
            dialogue_parts = []
            for msg in dialogue:
                if isinstance(msg, dict):
                    role = msg.get("role") or msg.get("speaker") or "Speaker"
                    text = msg.get("text") or msg.get("content") or msg.get("message") or ""
                    if text:
                        dialogue_parts.append(f"{role}: {text}")
                elif isinstance(msg, str):
                    dialogue_parts.append(msg)
            return "\n\n".join(dialogue_parts)
        elif isinstance(dialogue, str):
            return dialogue

    # Try messages field
    messages = item.get("messages") or item.get("turns") or []
    if isinstance(messages, list) and messages:
        dialogue_parts = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role") or msg.get("speaker") or "Speaker"
                text = msg.get("text") or msg.get("content") or msg.get("message") or ""
                if text:
                    dialogue_parts.append(f"{role}: {text}")
            elif isinstance(msg, str):
                dialogue_parts.append(msg)
        if dialogue_parts:
            return "\n\n".join(dialogue_parts)

    # Fallback to text field
    text = item.get("text") or item.get("transcript") or ""
    if text:
        return text

    # Last resort: return JSON representation
    return json.dumps(item, indent=2)


def try_fetch_agent_conversations(api_key: str) -> List[Dict[str, Any]]:
    """Try to fetch agent conversations using various endpoints."""
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    conversations = []
    endpoints_to_try = [
        f"{BASE_URL}/agents/conversations",
        f"{BASE_URL}/conversations",
        f"{BASE_URL}/v2/agents/conversations",
        f"{BASE_URL}/v2/conversations",
    ]

    # Try to get agents first
    agents = []
    try:
        agents_response = requests.get(f"{BASE_URL}/agents", headers=headers, timeout=10)
        if agents_response.status_code == 200:
            agents_data = agents_response.json()
            agents = agents_data.get("agents") or agents_data.get("data") or []
            if isinstance(agents_data, list):
                agents = agents_data
            if agents:
                logger.info(f"Found {len(agents)} agent(s)")
                # Add agent-specific endpoints
                for agent in agents[:5]:  # Try first 5 agents
                    agent_id = agent.get("agent_id") or agent.get("id")
                    if agent_id:
                        endpoints_to_try.insert(0, f"{BASE_URL}/agents/{agent_id}/conversations")
                        endpoints_to_try.insert(0, f"{BASE_URL}/v2/agents/{agent_id}/conversations")
    except:
        pass

    # Try each endpoint
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                convos = (
                    data.get("conversations") or
                    data.get("data") or
                    (data if isinstance(data, list) else [])
                )
                if convos:
                    conversations = convos
                    logger.info(f"✓ Found {len(conversations)} conversation(s) using: {endpoint}")
                    return conversations
        except:
            continue

    return conversations


def fetch_from_history(api_key: str, manager: TranscriptManager) -> Dict[str, int]:
    """Fetch transcripts from /v1/history endpoint."""
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    stats = {"saved": 0, "skipped": 0, "failed": 0}

    try:
        # Fetch history with pagination
        all_items = []
        last_id = None
        page_size = 100

        while True:
            params = {"page_size": page_size}
            if last_id:
                params["start_after_history_item_id"] = last_id

            response = requests.get(f"{BASE_URL}/history", headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            items = data.get("history", [])
            if not items:
                break

            all_items.extend(items)
            last_id = data.get("last_history_item_id")

            if not data.get("has_more", False):
                break

        if not all_items:
            logger.info("No history items found")
            return stats

        logger.info(f"✓ Found {len(all_items)} history item(s)")

        # Process each item
        for item in all_items:
            item_id = item.get("history_item_id") or item.get("id")
            if not item_id:
                continue

            # Check if already downloaded
            if manager.is_downloaded(item_id):
                stats["skipped"] += 1
                continue

            try:
                # Extract transcript text
                text = extract_transcript_text(item)

                if not text or len(text.strip()) == 0:
                    stats["failed"] += 1
                    continue

                # Prepare metadata
                metadata = {
                    "voice_name": item.get("voice_name"),
                    "model_id": item.get("model_id"),
                    "date_unix": item.get("date_unix"),
                    "created_at": item.get("created_at"),
                }

                # Save transcript
                if manager.save_transcript(item_id, metadata, text):
                    stats["saved"] += 1
                else:
                    stats["skipped"] += 1

            except Exception as e:
                logger.error(f"Error processing {item_id}: {e}")
                stats["failed"] += 1

    except Exception as e:
        logger.error(f"Error fetching history: {e}")

    return stats


def main():
    """Main entry point."""
    # Get script directory and set output
    script_dir = Path(__file__).parent.resolve()
    incoming_dir = script_dir / "incoming"

    # Ensure directory exists
    incoming_dir.mkdir(parents=True, exist_ok=True)

    # Get API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not set.")
        logger.error("Set it with: export ELEVENLABS_API_KEY='your-key-here'")
        sys.exit(1)

    logger.info("="*70)
    logger.info("Fetching ElevenLabs Transcripts")
    logger.info("="*70)
    logger.info(f"Output directory: {incoming_dir.absolute()}")
    logger.info("")

    manager = TranscriptManager(incoming_dir)
    total_stats = {"saved": 0, "skipped": 0, "failed": 0}

    # Try to fetch agent conversations first
    logger.info("Attempting to fetch agent conversations...")
    conversations = try_fetch_agent_conversations(api_key)

    if conversations:
        logger.info(f"Processing {len(conversations)} conversation(s)...")
        for convo in conversations:
            convo_id = convo.get("conversation_id") or convo.get("id")
            if not convo_id:
                continue

            if manager.is_downloaded(convo_id):
                total_stats["skipped"] += 1
                continue

            try:
                # Try to fetch full conversation details
                # (This would need the actual endpoint that works)
                text = extract_transcript_text(convo)
                if text:
                    metadata = {
                        "agent_name": convo.get("agent_name"),
                        "duration": convo.get("duration"),
                        "message_count": convo.get("message_count"),
                        "call_status": convo.get("call_status"),
                        "created_at": convo.get("created_at"),
                    }
                    if manager.save_transcript(convo_id, metadata, text):
                        total_stats["saved"] += 1
                    else:
                        total_stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error processing conversation {convo_id}: {e}")
                total_stats["failed"] += 1
    else:
        logger.warning("⚠️  Could not fetch agent conversations via API")
        logger.info("This is expected - agent conversations may not be available via REST API")
        logger.info("")

    # Fetch from history endpoint (TTS history)
    logger.info("Fetching from history endpoint...")
    history_stats = fetch_from_history(api_key, manager)
    total_stats["saved"] += history_stats["saved"]
    total_stats["skipped"] += history_stats["skipped"]
    total_stats["failed"] += history_stats["failed"]

    # Print summary
    logger.info("")
    logger.info("="*70)
    logger.info("Summary")
    logger.info("="*70)
    logger.info(f"✅ Saved:    {total_stats['saved']}")
    logger.info(f"⏭️  Skipped:  {total_stats['skipped']}")
    logger.info(f"❌ Failed:   {total_stats['failed']}")
    logger.info("")

    if total_stats['saved'] == 0 and not conversations:
        logger.info("="*70)
        logger.info("Manual Export Instructions")
        logger.info("="*70)
        logger.info("Since agent conversations aren't available via REST API:")
        logger.info("1. Go to https://elevenlabs.io/app/agents/conversations")
        logger.info("2. Export conversations manually (if export feature exists)")
        logger.info("3. Save exported files to: 11_labs_ingestion/incoming/")
        logger.info("4. The watcher will detect them automatically")
        logger.info("")
        logger.info("Alternatively, you can:")
        logger.info("- Copy/paste conversation transcripts manually")
        logger.info("- Use browser automation to extract conversations")
        logger.info("- Contact ElevenLabs support for API access to conversations")
        logger.info("")

    if total_stats['saved'] > 0:
        logger.info(f"📁 Transcripts saved to: {incoming_dir.absolute()}")
        logger.info("👀 The watcher script will detect these automatically!")


if __name__ == "__main__":
    main()
