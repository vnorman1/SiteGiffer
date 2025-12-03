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


def record_website_to_video(url, output_video="recording.webm", viewport_width=1260, viewport_height=720):
    """
    Record a website scrolling session to a WebM video file.
    
    Args:
        url: Target website URL
        output_video: Output video filename
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
    
    Returns:
        Path to the recorded video file
    """
    print(f"\n🎬 Starting website recording...")
    print(f"   - URL: {url}")
    print(f"   - Viewport: {viewport_width}x{viewport_height}")
    
    with sync_playwright() as p:
        # Launch Chromium in headless mode
        browser = p.chromium.launch(headless=True)
        
        # Create browser context with video recording enabled
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            record_video_dir="./recordings",
            record_video_size={"width": viewport_width, "height": viewport_height}
        )
        
        # Create new page
        page = context.new_page()
        
        print(f"\n🌐 Navigating to {url}...")
        
        # Navigate to URL and wait for network to be idle
        # This ensures React components and assets are fully loaded
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        print("✅ Page loaded (network idle)")
        
        # Additional wait for any late-loading animations/scripts
        time.sleep(2)
        
        print("\n🎥 Recording started...")
        
        # Wait a moment before starting scroll (capture initial state)
        time.sleep(1)
        
        # Perform smooth scroll simulation
        # Using small increments to trigger GSAP/Lenis animations
        smooth_scroll_page(
            page,
            scroll_step=40,    # Small steps for smooth animation
            delay=0.025        # Short delay between steps
        )
        
        # Wait a moment at the bottom
        time.sleep(1.5)
        
        # Optional: Scroll back to top smoothly
        print("\n📜 Scrolling back to top...")
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        time.sleep(0.5)
        
        # Close page and context to save video
        page.close()
        context.close()
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


def convert_video_to_gif(video_path, output_gif="portfolio.gif", fps=15, optimize=True):
    """
    Convert a video file to an optimized GIF using MoviePy.
    
    Args:
        video_path: Path to input video file
        output_gif: Output GIF filename
        fps: Frames per second for the GIF (lower = smaller file)
        optimize: Whether to optimize the GIF
    
    Returns:
        Path to the generated GIF file
    """
    print(f"\n🎨 Converting video to GIF...")
    print(f"   - Input: {video_path}")
    print(f"   - Output: {output_gif}")
    print(f"   - FPS: {fps}")
    
    # Load the video
    video = VideoFileClip(video_path)
    
    # Get video info
    duration = video.duration
    print(f"   - Duration: {duration:.2f} seconds")
    
    # Convert to GIF (MoviePy 2.x API)
    video.write_gif(
        output_gif,
        fps=fps
    )
    
    # Close the video clip
    video.close()
    
    # Get file sizes
    video_size = os.path.getsize(video_path) / (1024 * 1024)
    gif_size = os.path.getsize(output_gif) / (1024 * 1024)
    
    print(f"\n✅ GIF created successfully!")
    print(f"   - Video size: {video_size:.2f} MB")
    print(f"   - GIF size: {gif_size:.2f} MB")
    print(f"   - Output: {output_gif}")
    
    return output_gif


def create_portfolio_gif(url, output_gif="portfolio.gif", cleanup=True):
    """
    Main function to create a portfolio GIF from a website URL.
    
    Args:
        url: Target website URL
        output_gif: Output GIF filename
        cleanup: Whether to delete intermediate video file
    
    Returns:
        Path to the generated GIF file
    """
    print("=" * 60)
    print("🚀 Web to GIF Portfolio Showcase Generator")
    print("=" * 60)
    
    # Step 1: Record the website
    video_path = record_website_to_video(url)
    
    if not video_path:
        print("❌ Error: Failed to record video")
        return None
    
    # Step 2: Convert to GIF
    gif_path = convert_video_to_gif(video_path, output_gif)
    
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
    # Configuration
    TARGET_URL = "https://lobjetnorman.hu"  # Replace with your React website URL
    OUTPUT_GIF = "portfolio.gif"
    
    # Create the portfolio GIF
    result = create_portfolio_gif(
        url=TARGET_URL,
        output_gif=OUTPUT_GIF,
        cleanup=True  # Set to False to keep the .webm video file
    )
    
    if result:
        print(f"\n✨ Success! Your portfolio GIF is ready: {result}")
    else:
        print("\n❌ Failed to generate GIF")
