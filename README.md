# MTS Link Webinar Downloader (mtser)

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, standalone Python tool for downloading and processing webinar recordings from MTS Link (`my.mts-link.ru`). Automatically downloads segmented videos, synchronizes audio/video tracks, and creates a single compiled MP4 file.

## ✨ Features

- **🚀 Standalone Python script** - No Docker required, works anywhere Python runs
- **🎯 Dual interface** - Interactive mode for beginners & CLI for automation
- **🔒 Session authentication** - Supports private recordings with session IDs
- **📊 Progress tracking** - Visual progress bars for downloads and processing
- **🎨 Smart compilation** - Handles gaps between segments automatically
- **⚡ Efficient processing** - Multi-threaded encoding with MoviePy
- **📁 Organized output** - Creates structured directories for each webinar
- **🧹 Cleanup options** - Automatic cleanup of temporary files
- **🔧 Easy installation** - One-command setup script available

## 📋 Prerequisites

- Python 3.7 or higher
- 2GB+ free disk space (for typical webinars)
- Stable internet connection

## 🚀 Quick Start

### Installation (Multiple Options)

#### Option 1: One-Command Installation (Recommended)
**For macOS/Linux:**
```bash
git clone https://github.com/SirAndrewGotham/mtser.git
cd mtser
chmod +x install.sh
./install.sh
```

**For Windows:**
```bash
git clone https://github.com/SirAndrewGotham/mtser.git
cd mtser
install.bat
```

#### Option 2: Using setup.py
```bash
git clone https://github.com/SirAndrewGotham/mtser.git
cd mtser
python setup.py
```

#### Option 3: Manual Installation
```bash
git clone https://github.com/SirAndrewGotham/mtser.git
cd mtser

# Create virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Or on Windows
# venv\Scripts\activate

# Install dependencies
pip install httpx tqdm moviepy numpy
```

### Basic Usage

**Interactive mode (recommended for beginners):**
```bash
python mtser.py --interactive
```

**Command-line mode:**
```bash
# Public recording
python mtser.py https://my.mts-link.ru/12345678/987654321/record-new/123456789

# Private recording with session ID
python mtser.py https://my.mts-link.ru/12345678/987654321/record-new/123456789/record-file/1234567890 --session-id your_session_id
```

**Using the alias (after running install.sh):**
```bash
mtser --interactive
```

## 📖 Detailed Usage

### URL Formats Supported

The tool supports both MTS Link URL formats:

1. **Regular meeting** (with record-file):
   ```
   https://my.mts-link.ru/{organization_id}/{room_id}/record-new/{event_sessions}/record-file/{record_id}
   ```

2. **Quick meeting** (without record-file):
   ```
   https://my.mts-link.ru/{organization_id}/{room_id}/record-new/{event_sessions}
   ```

### Getting Session ID

For private recordings, you need a `sessionId` from your browser:

1. Log into MTS Link in your browser
2. Open Developer Tools (F12)
3. Go to Application → Storage → Cookies
4. Find and copy the `sessionId` value
5. Use it with the `--session-id` parameter

### Command Line Options

```bash
usage: mtser.py [-h] [--session-id SESSION_ID] [--output-dir OUTPUT_DIR]
                [--max-duration MAX_DURATION] [--keep-files] [--interactive]
                [--quiet] [--debug]
                [url]

Download and process MTS Link webinar recordings

positional arguments:
  url                   Webinar URL (optional in interactive mode)

options:
  -h, --help            show this help message and exit
  --session-id SESSION_ID
                        Session ID token for private recordings (get from browser cookies)
  --output-dir OUTPUT_DIR
                        Output directory for downloaded files (default: downloads)
  --max-duration MAX_DURATION
                        Maximum video duration in seconds (optional)
  --keep-files          Keep downloaded segment files after processing
  --interactive, -i     Run in interactive mode (ignores other arguments except URL)
  --quiet, -q           Suppress interactive prompts and progress output
  --debug, -d           Enable debug mode for troubleshooting
```

## 🎯 Examples

### Example 1: Download Public Recording
```bash
python mtser.py https://my.mts-link.ru/88314261/9993004207/record-new/9556828372/record-file/1694976671
```

### Example 2: Download with Custom Options
```bash
python mtser.py https://my.mts-link.ru/12345678/987654321/record-new/123456789 \
  --session-id a1b2c3d4e5f6 \
  --output-dir "my_webinars" \
  --max-duration 3600 \
  --keep-files
```

### Example 3: Batch Processing (Shell Script)
```bash
#!/bin/bash
URLS=(
  "https://my.mts-link.ru/123/456/record-new/789"
  "https://my.mts-link.ru/987/654/record-new/321/record-file/123"
)

for url in "${URLS[@]}"; do
  echo "Processing: $url"
  python mtser.py "$url" --quiet --output-dir "batch_downloads"
  echo "Completed: $url"
  echo "---"
done
```

## 📁 Output Structure

```
downloads/ (or your specified output directory)
├── Webinar_Name_2026-01-28_17_06_28/
│   ├── segment_abc123.mp4      # Individual segments (if --keep-files)
│   ├── segment_def456.mp4
│   ├── ...
│   └── Webinar_Name_2026-01-28_17_06_28.mp4  # Final compiled video
├── Another_Webinar_2026-01-29/
│   └── Another_Webinar_2026-01-29.mp4
└── logs/
    └── mtser.log               # Detailed log file
```

## 🔧 How It Works

### Technical Process
1. **URL Parsing**: Extracts `event_sessions` and `record_id` from the URL
2. **Metadata Fetch**: Retrieves webinar metadata from MTS Link API
3. **Segment Download**: Downloads all video/audio segments (typically 1000+ files)
4. **Timing Analysis**: Processes `relativeTime` from metadata for synchronization
5. **Gap Filling**: Inserts black video and silent audio between segments
6. **Compilation**: Combines all segments into a single MP4 file using MoviePy
7. **Cleanup**: Optionally removes temporary segment files

### Advanced Features
- **Browser-like headers**: Mimics real browser behavior to avoid blocking
- **Resumable downloads**: Supports Range headers for large files
- **Memory efficient**: Processes segments sequentially to avoid memory issues
- **Error recovery**: Handles network interruptions gracefully
- **Format detection**: Automatically identifies video vs audio segments

## 🐛 Troubleshooting

### Common Issues

1. **"Access denied" error**
   - Ensure you're using a valid, non-expired `sessionId`
   - Check that the webinar isn't restricted to specific users

2. **No video/audio clips found**
   - The webinar might be empty or have no recordings
   - Try with `--debug` flag to save raw data for inspection
   - Verify the URL format is correct

3. **MoviePy import errors**
   ```bash
   pip uninstall moviepy
   pip install moviepy==1.0.3
   ```

4. **Slow downloads**
   - Check your internet connection
   - The server might be rate limiting; try again later
   - Consider using `--max-duration` for partial downloads

5. **Memory errors with long webinars**
   - Use `--max-duration` to limit processing
   - Ensure you have sufficient RAM (4GB+ recommended)
   - Close other memory-intensive applications

### Debug Mode
For detailed troubleshooting:
```bash
python mtser.py --interactive --debug
# This saves raw JSON data to debug_data.json for inspection
```

Check the log file:
```bash
tail -f logs/mtser.log
```

## 🛠️ Installation Files

The project includes multiple installation options:

### `install.sh` (macOS/Linux)
- Creates virtual environment automatically
- Installs all dependencies
- Makes the script executable
- Provides alias setup for easy usage

### `install.bat` (Windows)
- Creates virtual environment
- Installs dependencies
- Provides activation instructions

### `setup.py`
- Interactive setup script
- Checks Python version
- Installs all required packages
- Creates executable shortcuts

### `requirements.txt`
- List of all required Python packages
- Can be used with `pip install -r requirements.txt`

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup
1. Fork the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Code Guidelines
- Follow PEP 8 style guide
- Use type hints for function signatures
- Add docstrings for all public functions
- Write tests for new features
- Update the documentation as needed

### Testing
```bash
# Run basic tests
python -m pytest tests/

# Test specific functionality
python tests/test_url_parsing.py
```

### Submitting Changes
1. Create a feature branch
2. Make your changes
3. Add or update tests
4. Update documentation
5. Submit a pull request

## 📊 Performance Tips

### For Large Webinars
- Use `--max-duration` to download only portions
- Increase chunk size for faster downloads (modify `chunk_size` in code)
- Use SSD storage for faster file operations
- Close other network-intensive applications

### For Multiple Downloads
- Run multiple instances with different output directories
- Use shell scripts for batch processing
- Monitor disk space for large downloads

## 🔮 Roadmap & Future Features

### Planned Features
- [ ] Parallel segment downloads
- [ ] YouTube/Dropbox integration
- [ ] Web interface (Flask/Django)
- [ ] Mobile application
- [ ] Scheduled downloads
- [ ] Email notifications
- [ ] Transcript generation

### Integration Opportunities
- **CMS Integration**: WordPress/Drupal plugins
- **Learning Management Systems**: Moodle, Canvas integration
- **Cloud Storage**: Direct upload to cloud services
- **Video Platforms**: Automatic YouTube/Vimeo publishing

## 📚 API Reference

### Programmatic Usage
```python
from mtser import MTSLinkerDownloader, WebinarProcessor

# Initialize
downloader = MTSLinkerDownloader()
processor = WebinarProcessor("output_dir")

# Process webinar
event_sessions, record_id = downloader.extract_ids_from_url(url)
json_data = downloader.fetch_webinar_data(api_url, session_id)

if json_data:
    video_clips, audio_clips, duration = processor.download_and_process_segments(json_data, downloader)
    processor.compile_final_video(video_clips, audio_clips, duration, "output.mp4")
```

### Internal API Endpoints
- Metadata: `https://my.mts-link.ru/api/event-sessions/{id}/record-files/{id}/flow?withoutCuts=false`
- Segments: `https://events-storage.webinar.ru/api-storage/files/wowza/{year}/{month}/{day}/{hash}.mp4`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Andrew Gotham**

- GitHub: [@SirAndrewGotham](https://github.com/SirAndrewGotham)
- Email: [andreogotema@gmail.com](mailto:andreogotema@gmail.com)
- Telegram: [@SirAndrewGotham](https://t.me/SirAndrewGotham)

## 🙏 Acknowledgments

- **MoviePy team** for the excellent video editing library
- **httpx developers** for the modern HTTP client
- **tqdm team** for the beautiful progress bars
- **MTS Link** users for testing and feedback

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/SirAndrewGotham/mtser/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SirAndrewGotham/mtser/discussions)
- **Email**: [andreogotema@gmail.com](mailto:andreogotema@gmail.com)
- **Telegram**: [@SirAndrewGotham](https://t.me/SirAndrewGotham)

## ⭐ Show Your Support

If this project helped you, please give it a ⭐ on GitHub!

---

**Note**: This tool is for personal/educational use. Always respect copyright laws and terms of service. Ensure you have permission to download and use webinar recordings.

*Last updated: 2026-02-01*