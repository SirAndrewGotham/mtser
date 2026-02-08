# MTS Link Webinar Downloader - Context Documentation

## 📋 Project Overview

**Project Name**: MTS Link Webinar Downloader (`mtser.py`)  
**Purpose**: A standalone Python tool for downloading, processing, and compiling webinar recordings from the MTS Link platform (https://my.mts-link.ru)  
**Core Functionality**: Automates the download of segmented webinar videos, synchronizes them with proper timing, and creates a single compiled MP4 file  
**Status**: Production-ready with interactive and CLI modes

## 🎯 Core Problem Solved

MTS Link webinars are stored as hundreds of small segmented video/audio files with timing metadata. This tool:
1. **Fetches webinar metadata** from MTS Link API using session authentication
2. **Downloads all segments** with progress tracking
3. **Reassembles segments** with correct timing (adding black/silent gaps where needed)
4. **Compiles final video** with synchronized audio/video tracks
5. **Handles private recordings** requiring session authentication

## 🏗️ Architecture Overview

### Main Components:
1. **MTSLinkerDownloader Class** (`mtser.py`):
    - URL parsing and validation
    - HTTP requests with proper browser headers
    - Session management and authentication
    - File download with progress bars

2. **WebinarProcessor Class** (`mtser.py`):
    - Segment downloading and processing
    - Video/audio clip creation with timing
    - Gap filling (black video/silent audio)
    - Final video compilation using MoviePy

3. **User Interface**:
    - Interactive mode with guided prompts
    - Command-line interface for automation
    - Progress tracking and status reporting

### Key Technical Details:
- **URL Format**: `https://my.mts-link.ru/{org_id}/{room_id}/record-new/{event_sessions}/record-file/{record_id}`
- **API Endpoints**: `/api/event-sessions/{id}/record-files/{id}/flow` and `/api/eventsessions/{id}/record`
- **Authentication**: `sessionId` cookie from browser
- **Media Storage**: Segments stored on `events-storage.webinar.ru`
- **Output**: Single MP4 file with H.264 video and AAC audio

## 📁 Project Structure

```
mtslinker/
├── mtser.py                    # Main executable script
├── requirements.txt           # Python dependencies
├── context.md                 # This documentation
└── downloads/                 # Default output directory
    └── Webinar_Name_2026-01-28/
        ├── segment1.mp4
        ├── segment2.mp4
        └── Webinar_Name_2026-01-28.mp4  # Final compiled video
```

## 🔧 Technical Stack

### Dependencies:
```txt
httpx>=0.24.0           # Modern HTTP client with async support
tqdm>=4.66.0            # Progress bars for downloads
moviepy>=1.0.3          # Video editing and compilation
numpy>=1.24.0           # Numerical operations for audio processing
Pillow>=9.0.0           # Image processing (required by moviepy)
decorator>=5.0.0        # Decorators (required by moviepy)
```

### Installation:
```bash
# Basic installation
pip install httpx tqdm moviepy numpy

# Complete installation
pip install -r requirements.txt
```

## 🚀 Usage Examples

### Interactive Mode (Recommended):
```bash
python mtser.py --interactive
# Follow prompts for URL, session ID, output directory
```

### CLI Mode (Automation):
```bash
# Public recording
python mtser.py https://my.mts-link.ru/88314261/9993004207/record-new/9556828372

# Private recording with session ID
python mtser.py https://my.mts-link.ru/88314261/9993004207/record-new/9556828372/record-file/1694976671 --session-id abc123def456

# With all options
python mtser.py URL --session-id SESSION_ID --output-dir "my_webinars" --max-duration 7200 --keep-files --quiet
```

### Programmatic Usage:
```python
from mtser import MTSLinkerDownloader, WebinarProcessor

# Initialize components
downloader = MTSLinkerDownloader()
processor = WebinarProcessor("downloads")

# Extract IDs and fetch data
event_sessions, record_id = downloader.extract_ids_from_url(url)
json_data = downloader.fetch_webinar_data(api_url, session_id)

# Process webinar
video_clips, audio_clips, duration = processor.download_and_process_segments(json_data, downloader)
processor.compile_final_video(video_clips, audio_clips, duration, "output.mp4")
```

## 🔐 Authentication & Security

### Session ID Acquisition:
1. **Browser Method**:
    - Login to MTS Link in browser
    - Open Developer Tools (F12)
    - Application/Storage → Cookies → `sessionId`

2. **Session Types**:
    - **Public recordings**: No session ID needed
    - **Private recordings**: Session ID required (expires with login session)

3. **Security Notes**:
    - Session IDs are passed as cookies
    - No username/password storage in the tool
    - HTTPS only for all requests
    - Headers mimic real browser behavior

## 📊 Data Flow

```
User Input (URL + session)
        ↓
Extract event_sessions + record_id
        ↓
Fetch JSON metadata from MTS Link API
        ↓
Parse eventLogs for segment URLs + timing
        ↓
Download all segments (1400+ files typical)
        ↓
Process segments into MoviePy clips
        ↓
Create video with gaps (black filler)
        ↓
Create audio with gaps (silent filler)
        ↓
Combine audio/video with synchronization
        ↓
Write final MP4 file (H.264/AAC)
        ↓
Cleanup segment files (optional)
```

## 🎨 User Interface Features

### Interactive Mode:
- **Guided prompts** for each parameter
- **Input validation** with helpful error messages
- **Progress visualization** with emojis and status bars
- **Multiple webinar support** in single session
- **Debug mode** for troubleshooting

### CLI Mode:
- **Argument parsing** with argparse
- **Quiet mode** for scripting/automation
- **Flexible output** directory selection
- **Duration limiting** for partial downloads
- **File management** options

## 🛠️ Development Notes

### Key Algorithms:
1. **Segment Timing**: Uses `relativeTime` from JSON to position clips
2. **Gap Filling**: Inserts black video/silent audio between segments
3. **Clip Sorting**: Sorts by start time before concatenation
4. **Memory Management**: Closes MoviePy clips after use

### Performance Considerations:
- **Memory**: Processes segments sequentially, not all at once
- **Disk**: Temporary segment storage, optional cleanup
- **Network**: HTTP/1.1 with keep-alive, proper timeouts
- **CPU**: Multi-threaded video encoding when available

### Error Handling:
- **Network errors**: Retry logic, timeout handling
- **Invalid data**: Validation at each step, fallback behaviors
- **Missing segments**: Gap filling instead of failure
- **Authentication**: Clear error messages for session issues

## 🔮 Future Development Opportunities

### Web Interface (Django/Flask):
```python
# Potential Django models
class WebinarJob(models.Model):
    url = models.URLField()
    session_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    output_file = models.FileField(upload_to='webinars/')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
```

### Mobile Applications:
- **Android/iOS**: Background download service
- **React Native**: Cross-platform UI for URL input
- **Notifications**: Push notifications on completion
- **Cloud storage**: Upload to Google Drive/Dropbox

### Enhanced Features:
1. **Batch Processing**: Process multiple URLs from CSV
2. **Cloud Integration**: Direct upload to YouTube/Vimeo
3. **Transcription**: Integrate speech-to-text for subtitles
4. **Quality Selection**: Choose resolution/bitrate
5. **Resumable Downloads**: Save progress and resume later
6. **Web Dashboard**: Real-time progress monitoring
7. **API Server**: REST API for integration with other tools
8. **Scheduled Downloads**: Automate regular webinar archiving

### Platform Expansion:
1. **Other Webinar Platforms**: Adapt for Zoom, Teams, etc.
2. **Browser Extension**: One-click download from MTS Link
3. **Desktop App**: PyQt/Tkinter interface with drag-drop
4. **CLI Toolchain**: Integrate with ffmpeg directly for speed

## 📈 Performance Metrics

### Typical Webinar Characteristics:
- **Duration**: 1-3 hours (180-540 minutes)
- **Segments**: 1000-2000 small MP4 files
- **Total Size**: 500MB-2GB uncompressed
- **Processing Time**: 30-90 minutes (download + compilation)
- **Final Size**: 200MB-800MB (compressed)

### Optimization Opportunities:
- **Parallel Downloads**: Download multiple segments simultaneously
- **Compression**: Better H.264 presets for faster encoding
- **Caching**: Reuse downloaded segments for repeated jobs
- **Streaming**: Direct stream-to-file without intermediate storage

## 🔧 Troubleshooting Guide

### Common Issues:
1. **"Access denied" error**: Invalid or expired session ID
2. **No clips found**: Empty webinar or format mismatch
3. **MoviePy import errors**: Version incompatibility
4. **Slow downloads**: Network issues, try with smaller segments
5. **Memory errors**: Very long webinars, use `--max-duration`

### Debug Mode:
```bash
python mtser.py --interactive --debug
# Saves raw JSON data to debug_data.json for inspection
```

## 📚 API Documentation

### MTS Link API Endpoints:
```python
# Metadata endpoint (with record-file)
"https://my.mts-link.ru/api/event-sessions/{event_sessions}/record-files/{record_id}/flow?withoutCuts=false"

# Metadata endpoint (without record-file)
"https://my.mts-link.ru/api/eventsessions/{event_sessions}/record?withoutCuts=false"
```

### Response Structure:
```json
{
  "name": "Webinar Name",
  "duration": 10773.55,
  "eventLogs": [
    {
      "relativeTime": 0.0,
      "data": {
        "url": "https://events-storage.webinar.ru/.../segment1.mp4"
      }
    }
  ]
}
```

## 🤝 Contribution Guidelines

### Code Style:
- **PEP 8 compliance** with Black formatting
- **Type hints** for all function signatures
- **Docstrings** for all classes and methods
- **Error handling** with specific exceptions

### Testing:
```bash
# Unit tests needed
pytest test_url_parsing.py
pytest test_downloader.py
pytest test_processor.py

# Integration test
python test_integration.py --test-url SAMPLE_URL
```

### Version Control:
- **Feature branches** for new development
- **Semantic versioning** for releases
- **CHANGELOG.md** for tracking changes

## 📞 Support & Maintenance

### Monitoring:
- **Logging**: Structured logs in `logs/mtser.log`
- **Metrics**: Download speed, success rate, file sizes
- **Alerts**: Email notifications for failed jobs

### Maintenance Tasks:
1. **Header updates**: Keep browser headers current
2. **API changes**: Monitor MTS Link API modifications
3. **Dependency updates**: Regular package updates
4. **Bug fixes**: Community-reported issues

---

*This document serves as comprehensive context for future development, integration, and maintenance of the MTS Link Webinar Downloader tool. Last updated: 2026-02-01*
