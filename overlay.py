#!/usr/bin/env python3
"""Floating overlay for agent status"""

import subprocess
import os
from datetime import datetime

class FloatingOverlay:
    def __init__(self):
        self.log_file = "/tmp/agent_overlay_log.txt"
        open(self.log_file, 'w').close()  # Clear

    def start(self):
        """Launch floating terminal window"""
        script = '''
        tell application "Terminal"
            do script "clear && echo '🤖 Onwords Agent' && echo '━━━━━━━━━━━━━━━━━━' && tail -f /tmp/agent_overlay_log.txt"
            set bounds of front window to {1100, 60, 1500, 400}
            set current settings of front window to settings set "Pro"
        end tell
        tell application "System Events"
            tell process "Terminal"
                set frontmost to true
                keystroke "t" using command down
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])

    def log(self, message, level="info"):
        """Write to overlay"""
        icons = {
            "info": "ℹ️ ", "action": "🎬", "think": "💭",
            "success": "✅", "error": "❌", "step": "📍"
        }
        icon = icons.get(level, "")
        timestamp = datetime.now().strftime("%H:%M:%S")

        with open(self.log_file, 'a') as f:
            f.write(f"{icon} [{timestamp}] {message}\n")

    def clear(self):
        open(self.log_file, 'w').close()


# Test it
if __name__ == "__main__":
    overlay = FloatingOverlay()
    overlay.start()
    overlay.log("Agent started", "success")
    overlay.log("Waiting for task...", "info")
