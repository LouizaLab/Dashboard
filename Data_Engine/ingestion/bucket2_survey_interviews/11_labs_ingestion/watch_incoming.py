#!/usr/bin/env python3
"""
File watcher for 11_labs_ingestion/incoming/ directory.

Monitors for new transcript files (.txt or .json) and logs when detected.
Processing logic can be added later.

Dependencies:
    pip install watchdog

Usage:
    python 11_labs_ingestion/watch_incoming.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Try to import watchdog, provide helpful error if missing
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog library not found.")
    print("Install it with: pip install watchdog")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TranscriptHandler(FileSystemEventHandler):
    """
    Handles file system events for transcript files.
    """

    def __init__(self, incoming_dir):
        """
        Initialize the handler.

        Args:
            incoming_dir: Path to the incoming directory being watched
        """
        self.incoming_dir = Path(incoming_dir)
        self.supported_extensions = {'.txt', '.json'}
        logger.info(f"Initialized watcher for: {self.incoming_dir}")

    def on_created(self, event):
        """
        Called when a file or directory is created.

        Args:
            event: FileSystemEvent object
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process files with supported extensions
        if file_path.suffix.lower() in self.supported_extensions:
            self.handle_new_transcript(file_path)

    def handle_new_transcript(self, file_path):
        """
        Handle a newly detected transcript file.

        Args:
            file_path: Path object to the new file
        """
        try:
            # Get file info
            file_size = file_path.stat().st_size
            file_name = file_path.name

            logger.info(f"📄 New transcript detected: {file_name}")
            logger.info(f"   Location: {file_path}")
            logger.info(f"   Size: {file_size} bytes")
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"   Time: {time_str}")

            # TODO: Add processing logic here
            # Examples:
            # - Validate file format
            # - Extract metadata
            # - Move to processed/ folder
            # - Index in data engine
            # - Send notifications

        except Exception as e:
            error_msg = f"Error handling transcript {file_path}: {e}"
            logger.error(error_msg, exc_info=True)


def watch_incoming_folder(incoming_dir=None):
    """
    Start watching the incoming folder for new transcript files.

    Args:
        incoming_dir: Path to incoming directory (defaults to script location)
    """
    # Get script directory and resolve paths
    script_dir = Path(__file__).parent.resolve()

    if incoming_dir is None:
        incoming_dir = script_dir / "incoming"
    else:
        incoming_dir = Path(incoming_dir).resolve()

    # Ensure incoming directory exists
    if not incoming_dir.exists():
        logger.warning(f"Incoming directory does not exist: {incoming_dir}")
        logger.info(f"Creating directory: {incoming_dir}")
        incoming_dir.mkdir(parents=True, exist_ok=True)

    if not incoming_dir.is_dir():
        logger.error(f"Path is not a directory: {incoming_dir}")
        return

    # Create event handler
    event_handler = TranscriptHandler(incoming_dir)

    # Create observer
    observer = Observer()
    observer.schedule(event_handler, str(incoming_dir), recursive=False)

    # Start watching
    observer.start()
    logger.info(f"👀 Watching for new transcripts in: {incoming_dir}")
    formats = ', '.join(event_handler.supported_extensions)
    logger.info(f"   Supported formats: {formats}")
    logger.info("   Press Ctrl+C to stop")

    try:
        # Keep the script running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping watcher...")
        observer.stop()

    observer.join()
    logger.info("✓ Watcher stopped")


def main():
    """Main entry point."""
    # Allow custom incoming directory via command line argument
    incoming_dir = sys.argv[1] if len(sys.argv) > 1 else None

    watch_incoming_folder(incoming_dir)


if __name__ == "__main__":
    main()
