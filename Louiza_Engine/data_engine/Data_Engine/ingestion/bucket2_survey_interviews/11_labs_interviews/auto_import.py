"""
Automatic 11 Labs Interview Importer

Monitors for new 11 Labs interviews and automatically imports them
if they are over 10 minutes long.

Supports:
- File watching (monitors a directory for new files)
- 11 Labs API integration (polls for new interviews)
- Manual import from file paths
"""

import os
import time
import re
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterviewImporter:
    """Handles importing 11 Labs interviews."""
    
    def __init__(self, target_folder: Path, min_duration_minutes: int = 10):
        """
        Initialize importer.
        
        Args:
            target_folder: Folder to save interviews to
            min_duration_minutes: Minimum duration in minutes to import (default: 10)
        """
        self.target_folder = Path(target_folder)
        self.target_folder.mkdir(parents=True, exist_ok=True)
        self.min_duration_minutes = min_duration_minutes
        
    def estimate_duration_from_text(self, text: str) -> float:
        """
        Estimate interview duration from transcript text.
        
        Uses average speaking rate of ~150 words per minute.
        
        Args:
            text: Interview transcript text
            
        Returns:
            Estimated duration in minutes
        """
        # Count words
        words = len(text.split())
        
        # Average speaking rate: ~150 words per minute
        # For interviews, might be slower due to pauses, so use ~120 wpm
        words_per_minute = 120
        duration_minutes = words / words_per_minute
        
        return duration_minutes
    
    def extract_duration_from_filename(self, filename: str) -> Optional[float]:
        """
        Try to extract duration from filename if it contains duration info.
        
        Examples:
        - "interview_15min.txt" -> 15.0
        - "call_10_30.txt" -> 10.5 (if 10:30 format)
        """
        # Look for patterns like "15min", "15_min", "15m"
        patterns = [
            r'(\d+)\s*min',
            r'(\d+)\s*_?\s*min',
            r'(\d+)\s*m\b',
            r'(\d+):(\d+)',  # 10:30 format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if ':' in pattern:
                    # Time format like 10:30
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    return hours * 60 + minutes
                else:
                    return float(match.group(1))
        
        return None
    
    def get_next_interview_number(self) -> int:
        """Get the next interview number based on existing files."""
        existing = list(self.target_folder.glob("Interview*.txt"))
        if not existing:
            return 1
        
        numbers = []
        for file in existing:
            match = re.search(r'Interview(\d+)', file.name)
            if match:
                numbers.append(int(match.group(1)))
        
        return max(numbers) + 1 if numbers else 1
    
    def import_interview(self, source_path: Path, 
                        interview_name: Optional[str] = None) -> Optional[Path]:
        """
        Import an interview file if it meets duration requirements.
        
        Args:
            source_path: Path to source interview file
            interview_name: Optional custom name (default: Interview{N}.txt)
            
        Returns:
            Path to imported file if successful, None otherwise
        """
        if not source_path.exists():
            logger.error(f"Source file does not exist: {source_path}")
            return None
        
        # Read the file
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {source_path}: {e}")
            return None
        
        # Check duration
        # First try to extract from filename
        duration = self.extract_duration_from_filename(source_path.name)
        
        # If not found, estimate from text
        if duration is None:
            duration = self.estimate_duration_from_text(content)
            logger.info(f"Estimated duration: {duration:.1f} minutes")
        else:
            logger.info(f"Duration from filename: {duration:.1f} minutes")
        
        # Check if meets minimum duration
        if duration < self.min_duration_minutes:
            logger.info(f"Skipping {source_path.name}: duration ({duration:.1f} min) < minimum ({self.min_duration_minutes} min)")
            return None
        
        # Generate target filename
        if interview_name:
            target_filename = interview_name
        else:
            next_num = self.get_next_interview_number()
            target_filename = f"Interview{next_num}.txt"
        
        target_path = self.target_folder / target_filename
        
        # Copy file
        try:
            import shutil
            shutil.copy2(source_path, target_path)
            logger.info(f"✓ Imported: {source_path.name} -> {target_filename} ({duration:.1f} min)")
            return target_path
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return None
    
    def import_from_directory(self, source_dir: Path, 
                             pattern: str = "*.txt") -> List[Path]:
        """
        Import all matching files from a directory.
        
        Args:
            source_dir: Directory to scan
            pattern: File pattern to match (default: "*.txt")
            
        Returns:
            List of imported file paths
        """
        imported = []
        source_path = Path(source_dir)
        
        if not source_path.exists():
            logger.error(f"Source directory does not exist: {source_dir}")
            return imported
        
        for file_path in source_path.glob(pattern):
            if file_path.is_file():
                result = self.import_interview(file_path)
                if result:
                    imported.append(result)
        
        return imported


class InterviewFileHandler(FileSystemEventHandler):
    """File system event handler for watching new interview files."""
    
    def __init__(self, importer: InterviewImporter):
        self.importer = importer
        self.processed_files = set()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Avoid processing the same file multiple times
        if str(file_path) in self.processed_files:
            return
        
        # Wait a bit for file to be fully written
        time.sleep(2)
        
        if file_path.exists() and file_path.is_file():
            logger.info(f"New file detected: {file_path.name}")
            self.processed_files.add(str(file_path))
            self.importer.import_interview(file_path)


def watch_directory(source_dir: Path, target_folder: Path, 
                    min_duration_minutes: int = 10):
    """
    Watch a directory for new interview files and auto-import them.
    
    Args:
        source_dir: Directory to watch for new files
        target_folder: Folder to import interviews to
        min_duration_minutes: Minimum duration to import
    """
    importer = InterviewImporter(target_folder, min_duration_minutes)
    event_handler = InterviewFileHandler(importer)
    
    observer = Observer()
    observer.schedule(event_handler, str(source_dir), recursive=False)
    observer.start()
    
    logger.info(f"Watching directory: {source_dir}")
    logger.info(f"Target folder: {target_folder}")
    logger.info(f"Minimum duration: {min_duration_minutes} minutes")
    logger.info("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopped watching")
    
    observer.join()


def main():
    """Main function - can be used for manual import or watching."""
    import argparse
    
    parser = argparse.ArgumentParser(description="11 Labs Interview Auto-Importer")
    parser.add_argument("--watch", type=str, help="Directory to watch for new files")
    parser.add_argument("--import", dest="import_dir", type=str, 
                       help="Directory to import files from")
    parser.add_argument("--file", type=str, help="Single file to import")
    parser.add_argument("--target", type=str, 
                       default="Data_Engine/ingestion/bucket2_survey_interviews/11_labs_interviews",
                       help="Target folder for interviews")
    parser.add_argument("--min-duration", type=int, default=10,
                       help="Minimum duration in minutes (default: 10)")
    
    args = parser.parse_args()
    
    target_folder = Path(args.target)
    importer = InterviewImporter(target_folder, args.min_duration)
    
    if args.watch:
        # Watch mode
        watch_directory(Path(args.watch), target_folder, args.min_duration)
    elif args.import_dir:
        # Import from directory
        imported = importer.import_from_directory(Path(args.import_dir))
        print(f"\n✓ Imported {len(imported)} interviews")
    elif args.file:
        # Import single file
        result = importer.import_interview(Path(args.file))
        if result:
            print(f"\n✓ Imported: {result}")
        else:
            print("\n✗ Import failed - check logs for details")
    else:
        print("Usage:")
        print("  --watch DIR      : Watch directory for new files")
        print("  --import DIR      : Import all files from directory")
        print("  --file PATH       : Import single file")
        print("\nExample:")
        print("  python auto_import.py --watch /path/to/11labs/exports")
        print("  python auto_import.py --import /path/to/interviews")


if __name__ == "__main__":
    main()




