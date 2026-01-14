#!/usr/bin/env python3
"""
ElevenLabs Transcript Fetcher

Automatically fetches interview transcripts from ElevenLabs API
and saves them to the local 11_labs_interviews/ directory.

Usage:
    export ELEVENLABS_API_KEY="your-api-key"
    python scripts/fetch_transcripts.py

    # Or fetch specific interview IDs:
    python scripts/fetch_transcripts.py --ids interview1 interview2

    # Or use config file:
    python scripts/fetch_transcripts.py --config config.json
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Install with: pip install requests")
    sys.exit(1)


# Configuration
OUTPUT_DIR = Path("./11_labs_interviews")
INDEX_FILE = OUTPUT_DIR / "downloaded_ids.json"
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class TranscriptMetadata:
    """Metadata for a transcript."""
    interview_id: str
    timestamp: Optional[datetime] = None
    title: Optional[str] = None
    duration_seconds: Optional[float] = None


class ElevenLabsClient:
    """Client for interacting with ElevenLabs API."""
    
    def __init__(self, api_key: str):
        """
        Initialize ElevenLabs API client.
        
        Args:
            api_key: ElevenLabs API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make API request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base URL)
            **kwargs: Additional request arguments
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{ELEVENLABS_API_BASE}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"Resource not found: {endpoint}")
                return {}
            elif response.status_code == 401:
                raise ValueError("Invalid API key. Check ELEVENLABS_API_KEY environment variable.")
            else:
                logger.error(f"HTTP error {response.status_code}: {e}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def list_transcripts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all available transcripts from ElevenLabs history.
        
        Args:
            limit: Maximum number of transcripts to return (None for all)
            
        Returns:
            List of transcript metadata dictionaries
        """
        logger.info("Fetching list of transcripts from ElevenLabs...")
        
        transcripts = []
        last_history_item_id = None
        
        try:
            while True:
                # Use the /history endpoint (confirmed working)
                endpoint = "history"
                params = {}
                if last_history_item_id:
                    params["start_after_history_item_id"] = last_history_item_id
                
                response_data = self._make_request("GET", endpoint, params=params)
                
                if not response_data:
                    break
                
                # Extract history items
                history_items = response_data.get("history", [])
                if isinstance(history_items, list):
                    transcripts.extend(history_items)
                elif isinstance(history_items, dict):
                    transcripts.append(history_items)
                
                # Check for pagination
                has_more = response_data.get("has_more", False)
                last_history_item_id = response_data.get("last_history_item_id")
                
                if not has_more or not last_history_item_id or (limit and len(transcripts) >= limit):
                    break
            
            logger.info(f"Found {len(transcripts)} transcript(s)")
            return transcripts[:limit] if limit else transcripts
            
        except Exception as e:
            logger.error(f"Error listing transcripts: {e}")
            return []
    
    def get_transcript(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcript text and metadata for a specific interview.
        
        Args:
            interview_id: Interview/transcript ID
            
        Returns:
            Dictionary with transcript data, or None if not found
        """
        logger.debug(f"Fetching transcript: {interview_id}")
        
        # Try different possible endpoints
        endpoints_to_try = [
            f"transcripts/{interview_id}",
            f"transcripts/{interview_id}/text",
            f"conversations/{interview_id}",
            f"interviews/{interview_id}",
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = self._make_request("GET", endpoint)
                if response:
                    return response
            except Exception:
                continue
        
        logger.warning(f"Could not fetch transcript {interview_id}")
        return None
    
    def get_transcript_text(self, interview_id: str) -> Optional[str]:
        """
        Get transcript text content.
        
        Args:
            interview_id: Interview/transcript ID
            
        Returns:
            Transcript text, or None if not found
        """
        data = self.get_transcript(interview_id)
        if not data:
            return None
        
        # Extract text from various possible response formats
        text = (
            data.get("text") or
            data.get("transcript") or
            data.get("content") or
            data.get("text_content") or
            ""
        )
        
        # If text is in a nested structure
        if isinstance(text, dict):
            text = text.get("text") or text.get("content") or ""
        
        return text.strip() if text else None


class TranscriptManager:
    """Manages transcript files and index."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize transcript manager.
        
        Args:
            output_dir: Directory to save transcripts
        """
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
    
    def is_downloaded(self, interview_id: str) -> bool:
        """Check if transcript is already downloaded."""
        return interview_id in self.downloaded_ids
    
    def get_filename(self, interview_id: str, timestamp: Optional[datetime] = None) -> Path:
        """
        Generate filename for transcript.
        
        Args:
            interview_id: Interview ID
            timestamp: Optional timestamp for filename
            
        Returns:
            Path to transcript file
        """
        if timestamp:
            date_str = timestamp.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"{interview_id}__{date_str}.txt"
        return self.output_dir / filename
    
    def save_transcript(
        self,
        interview_id: str,
        text: str,
        metadata: Optional[TranscriptMetadata] = None
    ) -> bool:
        """
        Save transcript to file.
        
        Args:
            interview_id: Interview ID
            text: Transcript text
            metadata: Optional metadata
            
        Returns:
            True if saved, False if skipped
        """
        # Check if already downloaded
        if self.is_downloaded(interview_id):
            logger.info(f"⏭️  Skipping {interview_id} (already downloaded)")
            return False
        
        # Generate filename
        timestamp = metadata.timestamp if metadata else None
        filepath = self.get_filename(interview_id, timestamp)
        
        # Check if file already exists
        if filepath.exists():
            logger.info(f"⏭️  Skipping {interview_id} (file exists: {filepath.name})")
            self.downloaded_ids.add(interview_id)
            self._save_index()
            return False
        
        # Write transcript file
        try:
            # Add metadata header if available
            content_parts = []
            
            if metadata:
                if metadata.title:
                    content_parts.append(f"Title: {metadata.title}\n")
                if metadata.duration_seconds:
                    minutes = int(metadata.duration_seconds // 60)
                    seconds = int(metadata.duration_seconds % 60)
                    content_parts.append(f"Duration: {minutes}m {seconds}s\n")
                if metadata.timestamp:
                    content_parts.append(f"Date: {metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                content_parts.append(f"Interview ID: {interview_id}\n")
                content_parts.append("\n" + "="*70 + "\n")
                content_parts.append("Transcript:\n")
                content_parts.append("="*70 + "\n\n")
            
            content_parts.append(text)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(''.join(content_parts))
            
            # Update index
            self.downloaded_ids.add(interview_id)
            self._save_index()
            
            logger.info(f"✅ Saved: {filepath.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving {interview_id}: {e}")
            return False


def parse_metadata(transcript_data: Dict[str, Any]) -> TranscriptMetadata:
    """
    Parse metadata from transcript API response.
    
    Args:
        transcript_data: Raw API response data from ElevenLabs history
        
    Returns:
        TranscriptMetadata object
    """
    # ElevenLabs history items use history_item_id
    interview_id = (
        transcript_data.get("history_item_id") or
        transcript_data.get("id") or
        transcript_data.get("interview_id") or
        transcript_data.get("conversation_id") or
        ""
    )
    
    # Parse timestamp (ElevenLabs uses unix timestamp or ISO format)
    timestamp = None
    timestamp_value = (
        transcript_data.get("created_unix") or
        transcript_data.get("created_at") or
        transcript_data.get("timestamp") or
        transcript_data.get("date") or
        None
    )
    
    if timestamp_value:
        try:
            # Try unix timestamp (integer)
            if isinstance(timestamp_value, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp_value)
            else:
                # Try ISO format string
                timestamp_str = str(timestamp_value)
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common string formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        timestamp = datetime.strptime(str(timestamp_value), fmt)
                        break
                    except:
                        continue
            except:
                pass
    
    # Get title/name from various possible fields
    title = (
        transcript_data.get("text")[:50] + "..." if transcript_data.get("text") else None or
        transcript_data.get("title") or
        transcript_data.get("name") or
        transcript_data.get("conversation_name") or
        None
    )
    
    # Duration in seconds
    duration_seconds = (
        transcript_data.get("duration") or
        transcript_data.get("duration_seconds") or
        None
    )
    
    return TranscriptMetadata(
        interview_id=interview_id,
        timestamp=timestamp,
        title=title,
        duration_seconds=duration_seconds
    )


def fetch_and_save_transcripts(
    client: ElevenLabsClient,
    manager: TranscriptManager,
    interview_ids: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Fetch and save transcripts.
    
    Args:
        client: ElevenLabs API client
        manager: Transcript manager
        interview_ids: Optional list of specific IDs to fetch
        
    Returns:
        Dictionary with counts: saved, skipped, failed
    """
    stats = {"saved": 0, "skipped": 0, "failed": 0}
    
    # Get list of transcripts to fetch
    if interview_ids:
        transcript_list = [{"history_item_id": tid} for tid in interview_ids]
        logger.info(f"Fetching {len(interview_ids)} specified transcript(s)")
    else:
        transcript_list = client.list_transcripts()
        if not transcript_list:
            logger.warning("No transcripts found. If using specific IDs, pass them with --ids")
            return stats
    
    # Fetch and save each transcript
    for transcript_info in transcript_list:
        interview_id = (
            transcript_info.get("history_item_id") or
            transcript_info.get("id") or
            transcript_info.get("interview_id") or
            transcript_info.get("conversation_id") or
            ""
        )
        
        if not interview_id:
            logger.warning("Skipping transcript with no ID")
            continue
        
        # Check if already downloaded
        if manager.is_downloaded(interview_id):
            stats["skipped"] += 1
            continue
        
        # Use the transcript_info directly (it's already from history API)
        try:
            # The transcript_info IS the history item, so use it directly
            transcript_data = transcript_info
            
            # Extract transcript from dialogue field (contains actual conversation)
            text = ""
            dialogue = transcript_info.get("dialogue")
            
            if dialogue:
                # Dialogue is typically a list of conversation turns
                if isinstance(dialogue, list):
                    dialogue_parts = []
                    for turn in dialogue:
                        if isinstance(turn, dict):
                            # Extract speaker and text
                            speaker = turn.get("role") or turn.get("speaker") or turn.get("name") or "Speaker"
                            turn_text = turn.get("text") or turn.get("content") or turn.get("message") or ""
                            if turn_text:
                                dialogue_parts.append(f"{speaker}: {turn_text}")
                        elif isinstance(turn, str):
                            dialogue_parts.append(turn)
                    text = "\n\n".join(dialogue_parts)
                elif isinstance(dialogue, dict):
                    # If dialogue is a dict, try to extract text
                    text = dialogue.get("text") or dialogue.get("transcript") or json.dumps(dialogue, indent=2)
                elif isinstance(dialogue, str):
                    text = dialogue
            
            # If no dialogue, fall back to text field (but that's usually just the prompt)
            if not text or len(text.strip()) == 0:
                text = transcript_info.get("text") or ""
                if text:
                    logger.info(f"Using 'text' field for {interview_id} (no dialogue found - this might be a prompt, not a transcript)")
            
            # If still no text, log available fields
            if not text or len(text.strip()) == 0:
                available_keys = list(transcript_info.keys())
                logger.warning(f"No transcript text found for {interview_id}. Available fields: {available_keys}")
                text = f"[Transcript ID: {interview_id}]\n[No transcript available - this might be a text-to-speech generation, not an interview]\n"
                for key, value in transcript_info.items():
                    if key not in ["dialogue", "text"] and not isinstance(value, (dict, list)) and value:
                        text += f"{key}: {value}\n"
            
            # Parse metadata
            metadata = parse_metadata(transcript_data)
            metadata.interview_id = interview_id  # Ensure ID is set
            
            # Save transcript
            if manager.save_transcript(interview_id, text, metadata):
                stats["saved"] += 1
            else:
                stats["skipped"] += 1
                
        except Exception as e:
            logger.error(f"Error processing {interview_id}: {e}")
            stats["failed"] += 1
    
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch ElevenLabs interview transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all available transcripts
  python scripts/fetch_transcripts.py
  
  # Fetch specific interview IDs
  python scripts/fetch_transcripts.py --ids interview1 interview2
  
  # Use custom output directory
  python scripts/fetch_transcripts.py --output ./custom_folder
        """
    )
    
    parser.add_argument(
        "--ids",
        nargs="+",
        help="Specific interview IDs to fetch"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_DIR),
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="ElevenLabs API key (overrides ELEVENLABS_API_KEY env var)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get API key
    api_key = args.api_key or os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not set. Set it as an environment variable or use --api-key")
        sys.exit(1)
    
    # Initialize components
    output_dir = Path(args.output)
    client = ElevenLabsClient(api_key)
    manager = TranscriptManager(output_dir)
    
    logger.info("="*70)
    logger.info("ElevenLabs Transcript Fetcher")
    logger.info("="*70)
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info(f"Already downloaded: {len(manager.downloaded_ids)} transcript(s)")
    logger.info("")
    
    # Fetch and save transcripts
    try:
        stats = fetch_and_save_transcripts(
            client,
            manager,
            interview_ids=args.ids
        )
        
        # Print summary
        logger.info("")
        logger.info("="*70)
        logger.info("Summary")
        logger.info("="*70)
        logger.info(f"✅ Saved:    {stats['saved']}")
        logger.info(f"⏭️  Skipped:  {stats['skipped']}")
        logger.info(f"❌ Failed:   {stats['failed']}")
        logger.info("")
        
        if stats['saved'] > 0:
            logger.info(f"📁 Transcripts saved to: {output_dir.absolute()}")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

