#!/usr/bin/env python3
"""
mtser.py
A standalone tool for downloading and processing MTS Link webinar recordings.
Supports both command line and interactive modes.
"""

import os
import sys
import re
import json
import argparse
import logging
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

import httpx
import tqdm
import numpy as np

# Try different import methods for moviepy
try:
    # Try new moviepy structure first
    from moviepy import VideoFileClip, AudioFileClip, ColorClip, CompositeAudioClip, concatenate_videoclips
    from moviepy.audio.AudioClip import AudioArrayClip
except ImportError:
    try:
        # Try old moviepy structure
        from moviepy.editor import VideoFileClip, AudioFileClip, ColorClip, CompositeAudioClip, concatenate_videoclips
        from moviepy.audio.AudioClip import AudioArrayClip
    except ImportError:
        print("Error: moviepy is not installed or has incompatible version.")
        print("Please install moviepy with: pip install moviepy")
        sys.exit(1)


class MTSLinkerDownloader:
    """Handles downloading of webinar data and media files."""

    def __init__(self, timeout: float = 60.0):
        self.timeout = httpx.Timeout(timeout)
        self.session = httpx.Client(
            timeout=self.timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Origin': 'https://my.mts-link.ru',
                'Referer': 'https://my.mts-link.ru/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Connection': 'keep-alive',
            },
            follow_redirects=True
        )

    def extract_ids_from_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract event_sessions and record_id from MTS Link URL."""
        patterns = [
            r'^https://my\.mts-link\.ru/(?:[^/]+/)?\d+/\d+/record-new/(\d+)(?:/record-file/(\d+))?$',
            r'^https://my\.mts-link\.ru/\d+/\d+/record-new/(\d+)(?:/record-file/(\d+))?$'
        ]

        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                event_sessions = match.group(1)
                record_id = match.group(2) if match.group(2) else None
                return event_sessions, record_id

        return None, None

    def validate_url(self, url: str) -> bool:
        """Validate if URL matches MTS Link pattern."""
        patterns = [
            r'^https://my\.mts-link\.ru/(?:[^/]+/)?\d+/\d+/record-new/\d+(?:/record-file/\d+)?$',
        ]

        for pattern in patterns:
            if re.match(pattern, url):
                return True

        return False

    def construct_json_url(self, event_sessions: str, record_id: Optional[str]) -> str:
        """Construct the API URL for webinar metadata."""
        if record_id:
            return f'https://my.mts-link.ru/api/event-sessions/{event_sessions}/record-files/{record_id}/flow?withoutCuts=false'
        return f'https://my.mts-link.ru/api/eventsessions/{event_sessions}/record?withoutCuts=false'

    def fetch_webinar_data(self, url: str, session_id: Optional[str] = None) -> Dict:
        """Fetch webinar metadata from MTS Link API."""
        cookies = {}
        if session_id:
            cookies['sessionId'] = session_id

        try:
            response = self.session.get(url, cookies=cookies)
            response.raise_for_status()

            # Check for access errors
            try:
                data = response.json()
                if data.get("error", {}).get("code") == 403:
                    logging.error("Access denied. Session ID may be required or invalid.")
                    return None
                return data
            except json.JSONDecodeError:
                logging.error("Invalid JSON response from server")
                return None

        except httpx.HTTPError as e:
            logging.error(f"HTTP error fetching webinar data: {e}")
            return None

    def download_file(self, url: str, save_path: Path) -> bool:
        """Download a single file with progress bar."""
        if save_path.exists():
            logging.info(f"File already exists: {save_path.name}")
            return True

        try:
            # Add video-specific headers for media downloads
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'video/mp4,video/webm,video/ogg,application/octet-stream,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://my.mts-link.ru/',
                'Origin': 'https://events-storage.webinar.ru',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
                'Range': 'bytes=0-',  # Support for resumable downloads
            }

            with self.session.stream('GET', url, headers=headers) as response:
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))

                # Ensure directory exists
                save_path.parent.mkdir(parents=True, exist_ok=True)

                with open(save_path, 'wb') as f:
                    with tqdm.tqdm(
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            desc=f'Downloading {save_path.name}',
                            leave=False
                    ) as pbar:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))

                return True

        except Exception as e:
            logging.error(f"Error downloading {url}: {e}")
            if save_path.exists():
                save_path.unlink()  # Remove partial download
            return False

    def close(self):
        """Close the HTTP session."""
        self.session.close()


class WebinarProcessor:
    """Processes downloaded webinar segments into a final video."""

    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, name: str) -> str:
        """Sanitize string to be safe for filenames."""
        return re.sub(r'[<>:"/\\|?*\s]+', '_', name).strip('_')

    def download_and_process_segments(self, json_data: Dict, downloader: MTSLinkerDownloader) -> Tuple[List, List, float]:
        """Download all segments and process them into video and audio clips."""
        video_clips = []
        audio_clips = []

        total_duration = float(json_data.get('duration', 0))
        if total_duration <= 0:
            raise ValueError("Invalid duration in webinar data")

        event_logs = json_data.get('eventLogs', [])

        # Debug: Log the structure of event_logs
        if event_logs and isinstance(event_logs, list) and len(event_logs) > 0:
            logging.debug(f"First event_log entry type: {type(event_logs[0])}")
            if isinstance(event_logs[0], dict):
                logging.debug(f"First event_log keys: {event_logs[0].keys()}")

        # First pass: download all files
        for event in event_logs:
            if not isinstance(event, dict):
                continue

            data = event.get('data')
            if not data or not isinstance(data, dict):
                continue

            url = data.get('url')
            if not url:
                continue

            # Extract filename from URL
            url_parts = url.split('?')[0]
            filename = os.path.basename(url_parts)
            if not filename:
                # If no filename in URL, generate one from the URL hash
                import hashlib
                filename_hash = hashlib.md5(url.encode()).hexdigest()[:16]
                filename = f"segment_{filename_hash}.mp4"

            filepath = self.output_dir / filename

            if not filepath.exists():
                logging.info(f"Downloading: {filename}")
                downloader.download_file(url, filepath)

        # Second pass: process downloaded files
        for event in event_logs:
            if not isinstance(event, dict):
                continue

            data = event.get('data')
            if not data or not isinstance(data, dict):
                continue

            url = data.get('url')
            start_time = event.get('relativeTime', 0)

            if not url:
                continue

            # Extract filename from URL
            url_parts = url.split('?')[0]
            filename = os.path.basename(url_parts)
            if not filename:
                # If no filename in URL, generate one from the URL hash
                import hashlib
                filename_hash = hashlib.md5(url.encode()).hexdigest()[:16]
                filename = f"segment_{filename_hash}.mp4"

            filepath = self.output_dir / filename

            if not filepath.exists():
                logging.warning(f"File not found: {filename}")
                continue

            try:
                # Try to load as video
                video_clip = VideoFileClip(str(filepath)).with_start(start_time)
                video_clips.append(video_clip)
            except Exception as e:
                # If not video, try audio
                try:
                    audio_clip = AudioFileClip(str(filepath)).with_start(start_time)
                    audio_clips.append(audio_clip)
                except Exception as audio_error:
                    logging.warning(f"Could not load {filename} as video or audio: {e}")

        return video_clips, audio_clips, total_duration

    def create_video_with_gaps(self, total_duration: float, video_clips: List) -> VideoFileClip:
        """Create final video with black gaps for missing segments."""
        if not video_clips:
            # Create blank video if no video clips
            return ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=total_duration)

        clips = []
        current_time = 0.0

        # Sort clips by start time
        video_clips.sort(key=lambda x: x.start)

        for video in video_clips:
            if video.start > current_time:
                gap_duration = video.start - current_time
                if gap_duration > 0:
                    gap_clip = ColorClip(
                        size=(1920, 1080),
                        color=(0, 0, 0),
                        duration=gap_duration
                    ).with_start(current_time)
                    clips.append(gap_clip)

            clips.append(video)
            current_time = max(current_time, video.end)

        # Fill remaining gap at the end
        if current_time < total_duration:
            remaining_duration = total_duration - current_time
            if remaining_duration > 0:
                gap_clip = ColorClip(
                    size=(1920, 1080),
                    color=(0, 0, 0),
                    duration=remaining_duration
                ).with_start(current_time)
                clips.append(gap_clip)

        if not clips:
            return ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=total_duration)

        return concatenate_videoclips(clips, method="compose")

    def create_audio_with_gaps(self, total_duration: float, audio_clips: List) -> CompositeAudioClip:
        """Create final audio with silence for gaps."""
        if not audio_clips:
            # Create silent audio
            silent_audio = AudioArrayClip(
                np.zeros((int(total_duration * 44100), 2)),
                fps=44100
            )
            return CompositeAudioClip([silent_audio])

        segments = []
        current_time = 0.0

        # Sort audio clips by start time
        audio_clips.sort(key=lambda x: x.start)

        for audio in audio_clips:
            if audio.start > current_time:
                gap_duration = audio.start - current_time
                if gap_duration > 0:
                    silence = AudioArrayClip(
                        np.zeros((int(gap_duration * 44100), 2)),
                        fps=44100
                    ).with_start(current_time)
                    segments.append(silence)

            segments.append(audio)
            current_time = max(current_time, audio.end)

        # Fill remaining silence at the end
        if current_time < total_duration:
            remaining_duration = total_duration - current_time
            if remaining_duration > 0:
                silence = AudioArrayClip(
                    np.zeros((int(remaining_duration * 44100), 2)),
                    fps=44100
                ).with_start(current_time)
                segments.append(silence)

        return CompositeAudioClip(segments)

    def compile_final_video(
            self,
            video_clips: List,
            audio_clips: List,
            total_duration: float,
            output_filename: str,
            max_duration: Optional[float] = None
    ) -> bool:
        """Compile all segments into final video file."""
        try:
            logging.info("Creating video with gaps...")
            final_video = self.create_video_with_gaps(total_duration, video_clips)

            if audio_clips:
                logging.info("Creating audio with gaps...")
                final_audio = self.create_audio_with_gaps(total_duration, audio_clips)
                final_video = final_video.with_audio(final_audio)

            # Apply duration limit if specified
            if max_duration and final_video.duration > max_duration:
                logging.info(f"Truncating video to {max_duration} seconds")
                final_video = final_video.subclip(0, max_duration)

            # Write final video
            output_path = self.output_dir / output_filename
            logging.info(f"Writing final video to: {output_path}")

            # Try different parameter combinations for moviepy compatibility
            try:
                # Try with modern parameters first
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    fps=24,
                    preset='medium',
                    threads=os.cpu_count() or 4
                )
            except TypeError as e:
                # If that fails, try with minimal parameters
                logging.warning(f"Falling back to minimal parameters: {e}")
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    fps=24
                )

            # Clean up clips to free memory
            final_video.close()
            for clip in video_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()

            return True

        except Exception as e:
            logging.error(f"Error compiling final video: {e}")
            return False


def setup_logging(log_dir: str = "logs", quiet: bool = False, debug: bool = False):
    """Setup logging configuration."""
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(exist_ok=True)

    log_level = logging.DEBUG if debug else (logging.WARNING if quiet else logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_dir_path / 'mtser.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def get_user_input():
    """Get webinar URL and session ID interactively from user."""
    print("\n" + "="*60)
    print("MTS Link Webinar Downloader - Interactive Mode")
    print("="*60)

    # Get webinar URL
    while True:
        url = input("\n📋 Enter MTS Link webinar URL: ").strip()

        if not url:
            print("❌ URL cannot be empty. Please try again.")
            continue

        downloader = MTSLinkerDownloader()
        if downloader.validate_url(url):
            downloader.close()
            break
        else:
            print("❌ Invalid URL format. Please enter a valid MTS Link webinar URL.")
            print("   Example formats:")
            print("   - https://my.mts-link.ru/12345678/987654321/record-new/123456789/record-file/1234567890")
            print("   - https://my.mts-link.ru/12345678/987654321/record-new/123456789")
            downloader.close()

    # Get session ID (optional)
    session_id = None
    use_session = input("\n🔒 Is this a private recording requiring session ID? (y/N): ").strip().lower()

    if use_session in ['y', 'yes']:
        session_id = input("   Enter session ID (from browser cookies): ").strip()
        if not session_id:
            print("   ℹ️  No session ID provided. Will try without it.")
            session_id = None

    # Get output directory
    output_dir = input("\n📁 Enter output directory (press Enter for 'downloads'): ").strip()
    if not output_dir:
        output_dir = "downloads"

    # Get max duration (optional)
    max_duration_input = input("\n⏱️  Enter maximum video duration in seconds (press Enter for no limit): ").strip()
    max_duration = None
    if max_duration_input:
        try:
            max_duration = float(max_duration_input)
            if max_duration <= 0:
                print("   ℹ️  Invalid duration. Using no limit.")
                max_duration = None
        except ValueError:
            print("   ℹ️  Invalid number. Using no limit.")
            max_duration = None

    # Ask about keeping files
    keep_files_input = input("\n🗑️  Keep downloaded segment files after processing? (y/N): ").strip().lower()
    keep_files = keep_files_input in ['y', 'yes']

    # Ask about debug mode
    debug_input = input("\n🐛 Enable debug mode for troubleshooting? (y/N): ").strip().lower()
    debug = debug_input in ['y', 'yes']

    return {
        'url': url,
        'session_id': session_id,
        'output_dir': output_dir,
        'max_duration': max_duration,
        'keep_files': keep_files,
        'debug': debug
    }


def download_webinar(args: Dict):
    """Main download function that processes the webinar."""
    # Initialize downloader
    downloader = MTSLinkerDownloader()

    try:
        # Extract IDs from URL
        logging.info(f"Processing URL: {args['url']}")
        event_sessions, record_id = downloader.extract_ids_from_url(args['url'])

        if not event_sessions:
            logging.error("Invalid URL format. Please check the webinar link.")
            return False

        logging.info(f"Event sessions: {event_sessions}, Record ID: {record_id}")

        # Construct API URL and fetch metadata
        json_url = downloader.construct_json_url(event_sessions, record_id)
        logging.info(f"Fetching webinar data from: {json_url}")

        json_data = downloader.fetch_webinar_data(json_url, args.get('session_id'))

        if not json_data:
            logging.error("Failed to fetch webinar data. Check URL and session ID.")
            return False

        # Get webinar name and create output directory
        webinar_name = json_data.get('name', 'Unnamed_Webinar')
        processor = WebinarProcessor(args['output_dir'])
        safe_name = processor.sanitize_filename(webinar_name)

        webinar_dir = Path(args['output_dir']) / safe_name
        webinar_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"Webinar: {webinar_name}")
        logging.info(f"Saving to: {webinar_dir}")

        # Count total segments
        event_logs = json_data.get('eventLogs', [])

        # Count only valid segments with URLs
        total_segments = 0
        for event in event_logs:
            if isinstance(event, dict):
                data = event.get('data')
                if data and isinstance(data, dict):
                    url = data.get('url')
                    if url:
                        total_segments += 1

        if not args.get('quiet', False):
            print(f"\n📥 Found {total_segments} segments to download")

        # Download and process segments
        if not args.get('quiet', False):
            print("\n🔄 Downloading and processing webinar segments...")

        video_clips, audio_clips, total_duration = processor.download_and_process_segments(json_data, downloader)

        logging.info(f"Found {len(video_clips)} video clips and {len(audio_clips)} audio clips")
        if not args.get('quiet', False):
            print(f"  Found: {len(video_clips)} video clips, {len(audio_clips)} audio clips")
            print(f"  Total duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")

        # Check if we found any clips
        if len(video_clips) == 0 and len(audio_clips) == 0:
            logging.error("No video or audio clips were found. The webinar might be empty or inaccessible.")
            if not args.get('quiet', False):
                print("\n❌ No video or audio content found. The webinar might be:")
                print("   - Empty (no recordings)")
                print("   - Protected (requires valid session ID)")
                print("   - In a format not supported by this tool")

            # Debug: Save the JSON data for inspection
            if args.get('debug', False):
                debug_file = webinar_dir / "debug_data.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                logging.info(f"Debug data saved to: {debug_file}")

            return False

        # Compile final video
        output_filename = f"{safe_name}.mp4"
        if not args.get('quiet', False):
            print(f"\n🎬 Creating final video: {output_filename}")

        success = processor.compile_final_video(
            video_clips,
            audio_clips,
            total_duration,
            output_filename,
            args.get('max_duration')
        )

        if success:
            final_path = webinar_dir / output_filename
            file_size = final_path.stat().st_size if final_path.exists() else 0
            file_size_mb = file_size / (1024 * 1024)

            if not args.get('quiet', False):
                print(f"\n✅ Successfully created: {final_path}")
                print(f"   File size: {file_size_mb:.2f} MB")

            # Clean up segment files if not keeping them
            if not args.get('keep_files', False):
                if not args.get('quiet', False):
                    print("\n🧹 Cleaning up segment files...")
                deleted_count = 0
                for filepath in webinar_dir.glob("*"):
                    if filepath.name != output_filename and not filepath.name.endswith('.json'):
                        try:
                            if filepath.exists():
                                filepath.unlink()
                                deleted_count += 1
                        except Exception as e:
                            logging.warning(f"Could not delete {filepath}: {e}")
                if not args.get('quiet', False):
                    print(f"   Deleted {deleted_count} segment files")

            return True
        else:
            if not args.get('quiet', False):
                print("\n❌ Failed to create final video")
            return False

    except KeyboardInterrupt:
        if not args.get('quiet', False):
            print("\n\n⏹️  Download interrupted by user")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        if not args.get('quiet', False):
            print(f"\n❌ Error: {e}")
        return False
    finally:
        downloader.close()


def main():
    """Main entry point with support for both CLI and interactive modes."""
    parser = argparse.ArgumentParser(
        description='Download and process MTS Link webinar recordings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://my.mts-link.ru/12345678/987654321/record-new/123456789
  %(prog)s --session-id abc123 https://my.mts-link.ru/12345678/987654321/record-new/123456789/record-file/1234567890
  
Interactive mode:
  %(prog)s --interactive
        """
    )

    # URL argument (optional when using interactive mode)
    parser.add_argument(
        'url',
        nargs='?',  # Makes URL optional
        help='Webinar URL (optional in interactive mode)'
    )

    parser.add_argument(
        '--session-id',
        help='Session ID token for private recordings (get from browser cookies)'
    )

    parser.add_argument(
        '--output-dir',
        default='downloads',
        help='Output directory for downloaded files (default: downloads)'
    )

    parser.add_argument(
        '--max-duration',
        type=float,
        help='Maximum video duration in seconds (optional)'
    )

    parser.add_argument(
        '--keep-files',
        action='store_true',
        help='Keep downloaded segment files after processing'
    )

    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Run in interactive mode (ignores other arguments except URL)'
    )

    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress interactive prompts and progress output'
    )

    parser.add_argument(
        '--debug',
        '-d',
        action='store_true',
        help='Enable debug mode for troubleshooting'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(quiet=args.quiet, debug=args.debug)

    # Interactive mode
    if args.interactive or (not args.url and not args.quiet):
        print("\n🌐 MTS Link Webinar Downloader")
        print("   (Press Ctrl+C at any time to cancel)\n")

        while True:
            user_args = get_user_input()
            user_args['quiet'] = False  # Never quiet in interactive mode

            print("\n" + "-"*60)
            print("Starting download...")
            print("-"*60)

            success = download_webinar(user_args)

            if success:
                print("\n✨ Download completed successfully!")
            else:
                print("\n⚠️  Download completed with errors.")

            # Ask if user wants to download another webinar
            another = input("\n📥 Download another webinar? (y/N): ").strip().lower()
            if another not in ['y', 'yes']:
                print("\n👋 Goodbye!")
                break

            print("\n" + "="*60)

    # CLI mode
    elif args.url:
        if not args.quiet:
            print(f"\n🌐 Processing: {args.url}")
            if args.session_id:
                print(f"🔒 Using session ID: {args.session_id[:10]}...")
            print("="*60)

        cli_args = {
            'url': args.url,
            'session_id': args.session_id,
            'output_dir': args.output_dir,
            'max_duration': args.max_duration,
            'keep_files': args.keep_files,
            'quiet': args.quiet,
            'debug': args.debug
        }

        success = download_webinar(cli_args)

        if not args.quiet:
            if success:
                print("\n✨ Download completed successfully!")
            else:
                print("\n⚠️  Download completed with errors.")
                sys.exit(1)

    else:
        # No URL provided and not in interactive mode
        parser.print_help()
        print("\n💡 Tip: Run with --interactive flag for guided mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
