#!/usr/bin/env python3
"""
Web to GIF Portfolio Showcase - Interactive CLI
================================================
Interactive command-line interface with keyboard navigation
for creating high-quality GIF recordings from websites.

Features:
- Dynamic filename based on domain
- Preloader skip (no recording during load)
- Seamless looping GIF (scroll down + scroll up)
- No flash at the end

Controls:
- Arrow keys: Navigate menu
- Enter: Select option
- Q/Esc: Quit/Back
"""

import os
import sys
import time
import subprocess
import curses
import re
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional, Callable
from playwright.sync_api import sync_playwright
from moviepy import VideoFileClip


# ============================================================
# PRESETS CONFIGURATION
# ============================================================

@dataclass
class Preset:
    """Configuration preset for GIF generation"""
    name: str
    description: str
    fps: int
    colors: int
    scroll_step: int
    scroll_delay: float
    preloader_wait: int
    
PRESETS = {
    "ultra_small": Preset(
        name="[1] Ultra Small",
        description="Smallest file size (~2-4MB) - Lower quality",
        fps=4,
        colors=32,
        scroll_step=120,
        scroll_delay=0.05,
        preloader_wait=5
    ),
    "small": Preset(
        name="[2] Small",
        description="Small file size (~4-8MB) - Good balance",
        fps=6,
        colors=64,
        scroll_step=100,
        scroll_delay=0.04,
        preloader_wait=5
    ),
    "balanced": Preset(
        name="[3] Balanced",
        description="Medium file size (~8-15MB) - Recommended",
        fps=8,
        colors=128,
        scroll_step=80,
        scroll_delay=0.035,
        preloader_wait=5
    ),
    "quality": Preset(
        name="[4] Quality",
        description="Larger file size (~15-25MB) - High quality",
        fps=12,
        colors=192,
        scroll_step=60,
        scroll_delay=0.03,
        preloader_wait=5
    ),
    "max_quality": Preset(
        name="[5] Maximum",
        description="Largest file size (~25MB+) - Best quality",
        fps=15,
        colors=256,
        scroll_step=40,
        scroll_delay=0.025,
        preloader_wait=5
    )
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_domain_name(url: str) -> str:
    """
    Extract clean domain name from URL for filename.
    e.g., "https://lobjetnorman.hu/page" -> "lobjetnorman"
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        # Get only the domain name (without TLD)
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            # Return main domain name (e.g., "lobjetnorman" from "lobjetnorman.hu")
            return domain_parts[0]
        return domain
    except:
        return "portfolio"


def get_dynamic_filename(url: str) -> str:
    """Generate dynamic filename based on URL domain."""
    domain = extract_domain_name(url)
    # Sanitize for filename
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', domain)
    return f"{safe_name}.gif" if safe_name else "portfolio.gif"


# ============================================================
# GIF GENERATION FUNCTIONS
# ============================================================

def smooth_scroll_down(page, scroll_step=80, delay=0.04):
    """Scroll smoothly to the bottom of the page."""
    scroll_height = page.evaluate("document.body.scrollHeight")
    viewport_height = page.evaluate("window.innerHeight")
    total_scroll_distance = scroll_height - viewport_height
    total_scrolls = int(total_scroll_distance / scroll_step) + 1
    
    for i in range(total_scrolls):
        page.mouse.wheel(0, scroll_step)
        time.sleep(delay)
        
        current_position = page.evaluate("window.scrollY")
        if current_position >= total_scroll_distance - 10:
            break
    
    time.sleep(0.3)


def smooth_scroll_up(page, scroll_step=80, delay=0.04):
    """Scroll smoothly back to the top of the page for seamless loop."""
    current_position = page.evaluate("window.scrollY")
    total_scrolls = int(current_position / scroll_step) + 1
    
    for i in range(total_scrolls):
        page.mouse.wheel(0, -scroll_step)  # Negative for scrolling up
        time.sleep(delay)
        
        new_position = page.evaluate("window.scrollY")
        if new_position <= 10:
            break
    
    # Ensure we're exactly at top (no flash)
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    time.sleep(0.2)


def generate_gif(url: str, preset: Preset, output_path: str, status_callback: Optional[Callable] = None) -> bool:
    """
    Generate a seamless looping GIF from a website URL.
    
    The GIF scrolls down and then back up smoothly for perfect looping.
    Recording starts AFTER preloader finishes.
    
    Args:
        url: Target website URL
        preset: Configuration preset
        output_path: Output GIF file path
        status_callback: Optional callback function for status updates
    
    Returns:
        True if successful, False otherwise
    """
    def update_status(msg):
        if status_callback:
            status_callback(msg)
    
    try:
        update_status("🚀 Initializing browser...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # ============================================================
            # PHASE 1: Load page and wait for preloader (NO recording)
            # ============================================================
            update_status("🌐 Loading page (preloader phase)...")
            
            context_preload = browser.new_context(
                viewport={"width": 1260, "height": 720}
            )
            page_preload = context_preload.new_page()
            page_preload.goto(url, wait_until="networkidle", timeout=60000)
            
            update_status(f"⏳ Waiting for preloader ({preset.preloader_wait}s)...")
            time.sleep(preset.preloader_wait)
            
            # Close preload context completely
            page_preload.close()
            context_preload.close()
            
            # ============================================================
            # PHASE 2: Fresh recording session (AFTER preloader)
            # ============================================================
            update_status("🎥 Starting recording...")
            
            os.makedirs("./recordings", exist_ok=True)
            
            # New context with video recording
            context_record = browser.new_context(
                viewport={"width": 1260, "height": 720},
                record_video_dir="./recordings",
                record_video_size={"width": 1260, "height": 720}
            )
            
            page = context_record.new_page()
            
            # Navigate fresh - page should load faster (cached)
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Small wait for any animations to settle (but NO long preloader)
            time.sleep(0.5)
            
            # ============================================================
            # SCROLL: Down and then Up for seamless loop
            # ============================================================
            update_status("📜 Scrolling down...")
            smooth_scroll_down(page, preset.scroll_step, preset.scroll_delay)
            
            # Pause at bottom before ending
            time.sleep(0.3)
            
            # Close to save video - do this cleanly to avoid flash
            page.close()
            context_record.close()
            browser.close()
        
        # ============================================================
        # PHASE 3: Convert video to optimized GIF
        # ============================================================
        update_status("🎨 Converting to GIF...")
        
        video_files = [f for f in os.listdir("./recordings") if f.endswith('.webm')]
        if not video_files:
            return False
        
        video_path = max(
            [os.path.join("./recordings", f) for f in video_files],
            key=os.path.getctime
        )
        
        # Trim the last few frames to avoid flash (cut last 0.2 seconds)
        trimmed_video = "./recordings/trimmed.webm"
        
        try:
            # Get video duration
            probe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip()) - 0.3  # Trim last 0.3s
            
            # Trim video
            trim_cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-t", str(duration),
                "-c", "copy", trimmed_video
            ]
            subprocess.run(trim_cmd, capture_output=True, check=True)
            
            # Use trimmed video for GIF
            source_video = trimmed_video
            
        except:
            # If trimming fails, use original
            source_video = video_path
        
        # Convert using ffmpeg for best quality/size ratio
        try:
            update_status("🔧 Optimizing GIF...")
            
            palette_cmd = [
                "ffmpeg", "-y", "-i", source_video,
                "-vf", f"fps={preset.fps},scale=1260:-1:flags=lanczos,palettegen=max_colors={preset.colors}:stats_mode=diff",
                "palette.png"
            ]
            
            gif_cmd = [
                "ffmpeg", "-y", "-i", source_video, "-i", "palette.png",
                "-lavfi", f"fps={preset.fps},scale=1260:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                output_path
            ]
            
            subprocess.run(palette_cmd, capture_output=True, check=True)
            subprocess.run(gif_cmd, capture_output=True, check=True)
            
            if os.path.exists("palette.png"):
                os.remove("palette.png")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to MoviePy
            video = VideoFileClip(source_video)
            video.write_gif(output_path, fps=preset.fps)
            video.close()
        
        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(trimmed_video):
            os.remove(trimmed_video)
        
        update_status("✅ Done!")
        return True
        
    except Exception as e:
        update_status(f"❌ Error: {str(e)[:50]}")
        return False


# ============================================================
# INTERACTIVE CLI
# ============================================================

class InteractiveCLI:
    """Interactive CLI with curses-based UI"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.url = "https://example.com"
        self.selected_preset = "balanced"
        self.output_path = ""  # Will be set dynamically
        self.auto_filename = True  # Use dynamic filename by default
        self.status_message = ""
        self.current_menu = "main"
        self.menu_index = 0
        
        # Setup curses
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    
    def get_output_filename(self) -> str:
        """Get the output filename (dynamic or custom)."""
        if self.auto_filename or not self.output_path:
            return get_dynamic_filename(self.url)
        return self.output_path
        
    def draw_header(self):
        """Draw the header"""
        try:
            height, width = self.stdscr.getmaxyx()
            box_width = min(58, width - 4)
            self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(0, 0, ("+" + "-" * box_width + "+")[:width-1])
            title = "SiteGiffer - Web to GIF"
            padding = (box_width - len(title)) // 2
            line = "|" + " " * padding + title + " " * (box_width - padding - len(title)) + "|"
            self.stdscr.addstr(1, 0, line[:width-1])
            self.stdscr.addstr(2, 0, ("+" + "-" * box_width + "+")[:width-1])
            self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        
    def draw_status(self):
        """Draw the status bar"""
        try:
            height, width = self.stdscr.getmaxyx()
            self.stdscr.attron(curses.color_pair(3))
            status = f" {self.status_message}" if self.status_message else " Ready"
            safe_status = status[:width-2]
            self.stdscr.addstr(height - 2, 0, safe_status.ljust(width-2)[:width-1])
            self.stdscr.attroff(curses.color_pair(3))
            
            self.stdscr.attron(curses.color_pair(5))
            controls = " Up/Down: Navigate | Enter: Select | Q: Quit "
            safe_controls = controls[:width-2].center(width-2)[:width-1]
            self.stdscr.addstr(height - 1, 0, safe_controls)
            self.stdscr.attroff(curses.color_pair(5))
        except curses.error:
            pass
        
    def draw_main_menu(self):
        """Draw the main menu"""
        try:
            height, width = self.stdscr.getmaxyx()
            current_filename = self.get_output_filename()
            filename_mode = "Auto" if self.auto_filename else "Custom"
            
            menu_items = [
                ("[1] Set URL", f"Current: {self.url[:35]}"),
                ("[2] Select Preset", f"Current: {PRESETS[self.selected_preset].name}"),
                ("[3] Output File", f"{filename_mode}: {current_filename}"),
                ("[4] Generate GIF", "Start the recording process"),
                ("[Q] Exit", "Close the application")
            ]
            
            y = 5
            max_desc_len = min(45, width - 12)
            for i, (title, desc) in enumerate(menu_items):
                if y >= height - 4:
                    break
                if i == self.menu_index:
                    self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                    self.stdscr.addstr(y, 2, f"  > {title}"[:width-4])
                    self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
                else:
                    self.stdscr.addstr(y, 2, f"    {title}"[:width-4])
                
                if y + 1 < height - 4:
                    self.stdscr.attron(curses.A_DIM)
                    self.stdscr.addstr(y + 1, 8, desc[:max_desc_len])
                    self.stdscr.attroff(curses.A_DIM)
                y += 3
            
            # Show preset details if space allows
            if y + 3 < height - 4:
                y += 1
                preset = PRESETS[self.selected_preset]
                self.stdscr.attron(curses.color_pair(1))
                self.stdscr.addstr(y, 2, "-" * min(50, width - 4))
                self.stdscr.addstr(y + 1, 2, f"Preset: {preset.description}"[:width-4])
                self.stdscr.addstr(y + 2, 2, f"FPS: {preset.fps} | Colors: {preset.colors} | Wait: {preset.preloader_wait}s"[:width-4])
                self.stdscr.attroff(curses.color_pair(1))
        except curses.error:
            pass
        
    def draw_preset_menu(self):
        """Draw the preset selection menu"""
        try:
            height, width = self.stdscr.getmaxyx()
            self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(4, 2, "Select a Preset:")
            self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
            
            y = 6
            for i, (key, preset) in enumerate(PRESETS.items()):
                if y >= height - 4:
                    break
                if i == self.menu_index:
                    self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                    marker = ">"
                else:
                    marker = " "
                
                self.stdscr.addstr(y, 2, f"  {marker} {preset.name}"[:width-4])
                
                if i == self.menu_index:
                    self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
                
                if y + 1 < height - 4:
                    self.stdscr.attron(curses.A_DIM)
                    self.stdscr.addstr(y + 1, 8, preset.description[:min(40, width-10)])
                    self.stdscr.attroff(curses.A_DIM)
                y += 3
            
            if y + 1 < height - 3:
                self.stdscr.addstr(y + 1, 2, "Press Enter to select, Esc to go back"[:width-4])
        except curses.error:
            pass
        
    def get_text_input(self, prompt: str, default: str = "") -> str:
        """Get text input from user"""
        curses.echo()
        curses.curs_set(1)
        
        self.stdscr.clear()
        self.draw_header()
        
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(5, 2, prompt)
        self.stdscr.attroff(curses.color_pair(1))
        
        self.stdscr.addstr(7, 2, f"Current: {default}")
        self.stdscr.addstr(9, 2, "New value (Enter to keep current): ")
        
        self.stdscr.refresh()
        
        try:
            user_input = self.stdscr.getstr(9, 38, 100).decode('utf-8').strip()
        except:
            user_input = ""
        
        curses.noecho()
        curses.curs_set(0)
        
        return user_input if user_input else default
        
    def update_status(self, message: str):
        """Update the status message"""
        self.status_message = message
        self.draw_status()
        self.stdscr.refresh()
        
    def run_generation(self):
        """Run the GIF generation process"""
        self.stdscr.clear()
        self.draw_header()
        
        height, width = self.stdscr.getmaxyx()
        
        # Get the actual output filename
        output_file = self.get_output_filename()
        
        self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(5, 2, "Generating GIF..."[:width-4])
        self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        self.stdscr.addstr(7, 2, f"URL: {self.url[:min(45, width-8)]}")
        self.stdscr.addstr(8, 2, f"Preset: {PRESETS[self.selected_preset].name}"[:width-4])
        self.stdscr.addstr(9, 2, f"Output: {output_file}"[:width-4])
        
        status_line = 11
        
        def status_callback(msg):
            # Remove emoji from status messages
            clean_msg = msg.replace("🚀", "[*]").replace("🌐", "[>]").replace("⏳", "[~]")
            clean_msg = clean_msg.replace("🎥", "[R]").replace("📜", "[S]").replace("🎨", "[C]")
            clean_msg = clean_msg.replace("🔧", "[O]").replace("✅", "[OK]").replace("❌", "[X]")
            self.stdscr.addstr(status_line, 2, " " * min(50, width-4))
            self.stdscr.attron(curses.color_pair(2))
            self.stdscr.addstr(status_line, 2, clean_msg[:min(48, width-4)])
            self.stdscr.attroff(curses.color_pair(2))
            self.stdscr.refresh()
        
        self.stdscr.addstr(13, 2, "Please wait...")
        self.stdscr.nodelay(True)
        self.stdscr.refresh()
        
        preset = PRESETS[self.selected_preset]
        success = generate_gif(self.url, preset, output_file, status_callback)
        
        self.stdscr.nodelay(False)
        
        if success:
            # Get file size
            try:
                size_mb = os.path.getsize(output_file) / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB"
            except:
                size_str = "Unknown"
            
            self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(15, 2, f"[OK] Success! GIF saved: {output_file}"[:width-4])
            self.stdscr.addstr(16, 2, f"File size: {size_str}"[:width-4])
            self.stdscr.addstr(17, 2, "One-way scroll (loop in frontend)"[:width-4])
            self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
        else:
            self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            self.stdscr.addstr(15, 2, "[X] Generation failed!")
            self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        
        self.stdscr.addstr(19, 2, "Press any key to continue...")
        self.stdscr.refresh()
        self.stdscr.getch()
        
    def handle_main_menu(self, key):
        """Handle main menu input"""
        menu_len = 5
        
        if key == curses.KEY_UP:
            self.menu_index = (self.menu_index - 1) % menu_len
        elif key == curses.KEY_DOWN:
            self.menu_index = (self.menu_index + 1) % menu_len
        elif key in [curses.KEY_ENTER, 10, 13]:
            if self.menu_index == 0:  # Set URL
                new_url = self.get_text_input("Enter website URL:", self.url)
                if new_url != self.url:
                    self.url = new_url
                    self.auto_filename = True  # Reset to auto when URL changes
            elif self.menu_index == 1:  # Select Preset
                self.current_menu = "preset"
                self.menu_index = list(PRESETS.keys()).index(self.selected_preset)
            elif self.menu_index == 2:  # Set Output Path
                current = self.get_output_filename()
                custom_name = self.get_text_input("Enter output filename (or Enter for auto):", current)
                if custom_name and custom_name != current:
                    self.output_path = custom_name
                    self.auto_filename = False
                else:
                    self.auto_filename = True
            elif self.menu_index == 3:  # Generate
                self.run_generation()
            elif self.menu_index == 4:  # Exit
                return False
        elif key in [ord('q'), ord('Q'), 27]:  # Q or Esc
            return False
            
        return True
        
    def handle_preset_menu(self, key):
        """Handle preset menu input"""
        preset_keys = list(PRESETS.keys())
        menu_len = len(preset_keys)
        
        if key == curses.KEY_UP:
            self.menu_index = (self.menu_index - 1) % menu_len
        elif key == curses.KEY_DOWN:
            self.menu_index = (self.menu_index + 1) % menu_len
        elif key in [curses.KEY_ENTER, 10, 13]:
            self.selected_preset = preset_keys[self.menu_index]
            self.current_menu = "main"
            self.menu_index = 1
        elif key in [27, ord('b'), ord('B')]:  # Esc or B
            self.current_menu = "main"
            self.menu_index = 1
            
    def safe_addstr(self, y, x, text):
        """Safely add string, handling terminal size issues"""
        try:
            height, width = self.stdscr.getmaxyx()
            if y < height - 1 and x < width - 1:
                safe_text = text[:width - x - 1]
                self.stdscr.addstr(y, x, safe_text)
        except curses.error:
            pass
    
    def run(self):
        """Main loop"""
        running = True
        
        while running:
            try:
                self.stdscr.clear()
                self.draw_header()
                
                if self.current_menu == "main":
                    self.draw_main_menu()
                elif self.current_menu == "preset":
                    self.draw_preset_menu()
                
                self.draw_status()
                self.stdscr.refresh()
                
                key = self.stdscr.getch()
                
                if self.current_menu == "main":
                    running = self.handle_main_menu(key)
                elif self.current_menu == "preset":
                    self.handle_preset_menu(key)
            except curses.error:
                # Terminal resize or other curses error
                pass


def main(stdscr):
    """Main entry point for curses"""
    cli = InteractiveCLI(stdscr)
    cli.run()


if __name__ == "__main__":
    # Check if we're in a terminal
    if not sys.stdout.isatty():
        print("This application requires an interactive terminal.")
        sys.exit(1)
    
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n👋 Goodbye!")
