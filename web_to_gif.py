#!/usr/bin/env python3
"""
Web to GIF Portfolio Showcase Generator
========================================
This script uses Playwright (sync API) to record a smooth scrolling video
of a React website and converts it to an optimized GIF using MoviePy.

Features:
- Headless Chromium browser
- Fixed 1260x720 viewport
- Smooth scroll simulation (GSAP/Lenis compatible)
- Network idle wait for React/assets loading
- Preloader wait support
- Optimized GIF output (reduced frames for smaller file size)
"""

import datetime
import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from moviepy import VideoFileClip


def smooth_scroll_page(page, scroll_step=50, delay=0.03, total_scrolls=None):
    """
    Perform smooth scroll simulation using mouse wheel.
    
    This approach triggers GSAP/Lenis scroll animations properly,
    unlike JavaScript scrollTo which might bypass them.
    
    Args:
        page: Playwright page object
        scroll_step: Pixels to scroll per increment (smaller = smoother)
        delay: Time between scroll increments (seconds)
        total_scrolls: Optional limit on scroll iterations
    """
    # Get the total scrollable height
    scroll_height = page.evaluate("document.body.scrollHeight")
    viewport_height = page.evaluate("window.innerHeight")
    
    # Calculate total distance to scroll
    total_scroll_distance = scroll_height - viewport_height
    
    # Calculate number of scroll steps needed
    if total_scrolls is None:
        total_scrolls = int(total_scroll_distance / scroll_step) + 1
    
    print(f"📜 Starting smooth scroll...")
    print(f"   - Page height: {scroll_height}px")
    print(f"   - Viewport: {viewport_height}px")
    print(f"   - Scroll steps: {total_scrolls}")
    
    current_scroll = 0
    
    for i in range(total_scrolls):
        # Use mouse wheel for smooth scrolling (triggers GSAP/Lenis)
        page.mouse.wheel(0, scroll_step)
        time.sleep(delay)
        
        current_scroll += scroll_step
        
        # Progress indicator every 20%
        progress = (i + 1) / total_scrolls * 100
        if (i + 1) % (total_scrolls // 5 or 1) == 0:
            print(f"   - Scroll progress: {progress:.0f}%")
        
        # Check if we've reached the bottom
        current_position = page.evaluate("window.scrollY")
        if current_position >= total_scroll_distance - 10:
            print("   - Reached bottom of page")
            break
    
    # Small pause at the bottom
    time.sleep(0.5)
    print("✅ Smooth scroll completed!")


def record_website_to_video(url, output_video="recording.webm", viewport_width=1260, viewport_height=720, preloader_wait=5):
    """
    Record a website scrolling session to a WebM video file.
    Recording starts AFTER the preloader finishes to save file size.
    
    Args:
        url: Target website URL
        output_video: Output video filename
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
        preloader_wait: Seconds to wait for preloader to finish (BEFORE recording starts)
    
    Returns:
        Path to the recorded video file
    """
    print(f"\n🎬 Preparing website recording...")
    print(f"   - URL: {url}")
    print(f"   - Viewport: {viewport_width}x{viewport_height}")
    print(f"   - Preloader wait: {preloader_wait}s (before recording)")
    
    with sync_playwright() as p:
        # Launch Chromium in headless mode
        browser = p.chromium.launch(headless=True)
        
        # ============================================================
        # PHASE 1: Load page and wait for preloader WITHOUT recording
        # ============================================================
        
        # Create context WITHOUT video recording first
        context_preload = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height}
        )
        
        page_preload = context_preload.new_page()
        
        print(f"\n🌐 Navigating to {url}...")
        
        # Navigate to URL and wait for network to be idle
        page_preload.goto(url, wait_until="networkidle", timeout=60000)
        print("✅ Page loaded (network idle)")
        
        # Wait for preloader animation to finish (NO RECORDING YET!)
        print(f"⏳ Waiting {preloader_wait}s for preloader to finish...")
        time.sleep(preloader_wait)
        print("✅ Preloader wait complete")
        
        # Close preload context
        page_preload.close()
        context_preload.close()
        
        # ============================================================
        # PHASE 2: Start fresh with video recording AFTER preloader
        # ============================================================
        
        print("\n🎥 Starting video recording (preloader skipped)...")
        
        # Create NEW context WITH video recording
        context_record = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            record_video_dir="./recordings",
            record_video_size={"width": viewport_width, "height": viewport_height}
        )
        
        page = context_record.new_page()
        
        # Navigate again - this time the page should be cached/faster
        # and preloader should be done or skipped
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Small wait for any final animations to settle
        time.sleep(1)
        
        print("🎥 Recording in progress...")
        
        # Perform smooth scroll simulation
        # Using larger steps for faster scrolling (reduces total frames)
        smooth_scroll_page(
            page,
            scroll_step=80,    # Larger steps = faster scroll = fewer frames
            delay=0.04         # Slightly longer delay for smooth animation
        )
        
        # Wait a moment at the bottom
        time.sleep(0.8)
        
        # Optional: Scroll back to top
        print("\n📜 Scrolling back to top...")
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        time.sleep(0.3)
        
        # Close page and context to save video
        page.close()
        context_record.close()
        browser.close()
        
        print("✅ Recording stopped")
    
    # Find the recorded video file
    recordings_dir = "./recordings"
    video_files = [f for f in os.listdir(recordings_dir) if f.endswith('.webm')]
    
    if video_files:
        # Get the most recent video
        latest_video = max(
            [os.path.join(recordings_dir, f) for f in video_files],
            key=os.path.getctime
        )
        
        # Rename to desired output name
        final_path = os.path.join(os.path.dirname(latest_video), output_video)
        os.rename(latest_video, final_path)
        
        print(f"📁 Video saved: {final_path}")
        return final_path
    
    return None


def convert_video_to_gif(video_path, output_gif="portfolio.gif", fps=8, optimize=True, colors=128, lossy=80):
    """
    Convert a video file to an optimized GIF using MoviePy and gifsicle/ffmpeg.
    
    Args:
        video_path: Path to input video file
        output_gif: Output GIF filename
        fps: Frames per second for the GIF (lower = smaller file, 8 is good balance)
        optimize: Whether to optimize the GIF
        colors: Number of colors in palette (64-256, lower = smaller)
        lossy: Lossy compression level (0-200, higher = smaller but lower quality)
    
    Returns:
        Path to the generated GIF file
    """
    print(f"\n🎨 Converting video to GIF...")
    print(f"   - Input: {video_path}")
    print(f"   - Output: {output_gif}")
    print(f"   - FPS: {fps}")
    print(f"   - Colors: {colors}")
    
    # Load the video
    video = VideoFileClip(video_path)
    
    # Get video info
    duration = video.duration
    total_frames = int(duration * fps)
    print(f"   - Duration: {duration:.2f} seconds")
    print(f"   - Estimated frames: {total_frames}")
    
    # Create temporary GIF first
    temp_gif = "temp_portfolio.gif"
    
    # Convert to GIF with reduced FPS (MoviePy 2.x API)
    video.write_gif(
        temp_gif,
        fps=fps
    )
    
    # Close the video clip
    video.close()
    
    # Optimize GIF using ffmpeg for better compression
    print("\n🔧 Optimizing GIF with ffmpeg...")
    
    try:
        # Use ffmpeg for palette optimization (much smaller file)
        palette_cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"fps={fps},scale=1260:-1:flags=lanczos,palettegen=max_colors={colors}:stats_mode=diff",
            "palette.png"
        ]
        
        gif_cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", "palette.png",
            "-lavfi", f"fps={fps},scale=1260:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            output_gif
        ]
        
        subprocess.run(palette_cmd, capture_output=True, check=True)
        subprocess.run(gif_cmd, capture_output=True, check=True)
        
        # Clean up palette and temp gif
        if os.path.exists("palette.png"):
            os.remove("palette.png")
        if os.path.exists(temp_gif):
            os.remove(temp_gif)
            
        print("✅ FFmpeg optimization complete!")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to MoviePy output if ffmpeg fails
        print("⚠️  FFmpeg not available, using MoviePy output")
        if os.path.exists(temp_gif):
            os.rename(temp_gif, output_gif)
    
    # Get file sizes
    video_size = os.path.getsize(video_path) / (1024 * 1024)
    gif_size = os.path.getsize(output_gif) / (1024 * 1024)
    
    print(f"\n✅ GIF created successfully!")
    print(f"   - Video size: {video_size:.2f} MB")
    print(f"   - GIF size: {gif_size:.2f} MB")
    print(f"   - Output: {output_gif}")
    
    return output_gif


def create_portfolio_gif(url, output_gif="portfolio.gif", cleanup=True, preloader_wait=5, fps=8, colors=128):
    """
    Main function to create a portfolio GIF from a website URL.
    
    Args:
        url: Target website URL
        output_gif: Output GIF filename
        cleanup: Whether to delete intermediate video file
        preloader_wait: Seconds to wait for preloader animation
        fps: Frames per second (8 is good for small file size)
        colors: Number of colors in GIF palette (64-256)
    
    Returns:
        Path to the generated GIF file
    """
    print("=" * 60)
    print("🚀 Web to GIF Portfolio Showcase Generator")
    print("=" * 60)
    
    # Step 1: Record the website
    video_path = record_website_to_video(url, preloader_wait=preloader_wait)
    
    if not video_path:
        print("❌ Error: Failed to record video")
        return None
    
    # Step 2: Convert to GIF with optimization
    gif_path = convert_video_to_gif(video_path, output_gif, fps=fps, colors=colors)
    
    # Step 3: Cleanup (optional)
    if cleanup and os.path.exists(video_path):
        os.remove(video_path)
        print(f"🗑️  Cleaned up: {video_path}")
    
    print("\n" + "=" * 60)
    print("🎉 Portfolio GIF generation complete!")
    print(f"📁 Output file: {gif_path}")
    print("=" * 60)
    
    return gif_path


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    # ============================================================
    # CONFIGURATION - Adjust these settings
    # ============================================================
    
    TARGET_URL = "https://lobjetnorman.hu"  # Your React website URL
    OUTPUT_GIF = "portfolio.gif"
    
    # Optimization settings for smaller file size
    PRELOADER_WAIT = 5    # Seconds to wait for preloader animation
    GIF_FPS = 6           # Frames per second (6-8 is good, lower = smaller)
    GIF_COLORS = 64       # Color palette size (64-256, lower = smaller)
    
    # ============================================================
    
    # Create the portfolio GIF
    result = create_portfolio_gif(
        url=TARGET_URL,
        output_gif=OUTPUT_GIF,
        cleanup=True,              # Set to False to keep the .webm video file
        preloader_wait=PRELOADER_WAIT,
        fps=GIF_FPS,
        colors=GIF_COLORS
    )
    
    if result:
        print(f"\n✨ Success! Your portfolio GIF is ready: {result}")
    else:
        print("\n❌ Failed to generate GIF")
