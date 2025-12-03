# Web to GIF Portfolio Showcase Generator

🎬 Generate high-quality GIF recordings from React websites with smooth scrolling animations.

## Features

- **Playwright Recording**: Uses Chromium in headless mode for reliable screen capture
- **Fixed Viewport**: 1260x720 resolution for consistent output
- **Smooth Scrolling**: Mouse wheel simulation compatible with GSAP/Lenis animations
- **Network Idle Wait**: Ensures React components and assets are fully loaded
- **Optimized GIF**: MoviePy conversion with quality optimization

## Quick Start

### 1. Setup (one-time)

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (creates venv, installs dependencies, downloads Chromium)
./setup.sh
```

### 2. Configure

Edit `web_to_gif.py` and set your target URL:

```python
TARGET_URL = "https://your-website.com"  # Your React website URL
OUTPUT_GIF = "portfolio.gif"              # Output filename
```

### 3. Run

```bash
# Activate virtual environment
source venv/bin/activate

# Generate the GIF
python web_to_gif.py
```

## Configuration Options

### Scroll Settings

In the `smooth_scroll_page()` function call:

```python
smooth_scroll_page(
    page,
    scroll_step=40,    # Pixels per scroll (smaller = smoother, slower)
    delay=0.025        # Delay between scrolls in seconds
)
```

### GIF Settings

In the `convert_video_to_gif()` function call:

```python
convert_video_to_gif(
    video_path,
    output_gif="portfolio.gif",
    fps=15,       # Frames per second (lower = smaller file)
    optimize=True
)
```

## Output

- **Video**: Temporary `.webm` file in `./recordings/` (deleted by default)
- **GIF**: Final output in project root

## Requirements

- Python 3.8+
- macOS, Linux, or Windows

## Troubleshooting

### "Playwright browsers not installed"
```bash
source venv/bin/activate
playwright install chromium
```

### "Page timeout"
Increase the timeout in `page.goto()`:
```python
page.goto(url, wait_until="networkidle", timeout=120000)  # 2 minutes
```

### "GIF too large"
Reduce FPS or duration:
```python
convert_video_to_gif(video_path, output_gif, fps=10)  # Lower FPS
```

## License

MIT License
