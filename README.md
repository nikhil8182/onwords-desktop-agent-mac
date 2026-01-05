# 🤖 Onwords Desktop Agent - Mac Edition

An AI-powered desktop automation agent that can see and control your Mac. Built for Onwords Smart Solutions.

## Features

- **Vision-based control**: Uses Claude's vision to understand what's on screen
- **Full desktop control**: Mouse, keyboard, scrolling, dragging
- **Mac-native**: Uses macOS APIs for reliable screen capture and input
- **Safety first**: Failsafe (move mouse to corner to abort) and confirmation for destructive actions
- **Iterative**: Captures screen → thinks → acts → repeats until task complete

## Quick Start

### 1. Setup

```bash
# Clone/download the folder, then:
cd mac-agent
chmod +x setup.sh
./setup.sh
```

### 2. Set API Key

```bash
# Add to your ~/.zshrc
export ANTHROPIC_API_KEY='your-api-key-here'
source ~/.zshrc
```

### 3. Grant Permissions (REQUIRED!)

Go to **System Settings → Privacy & Security** and enable:

| Permission | Location | Why Needed |
|------------|----------|------------|
| **Screen Recording** | Privacy → Screen Recording | To capture screenshots |
| **Accessibility** | Privacy → Accessibility | To control mouse/keyboard |

Enable these for **Terminal.app** (or iTerm2/whatever you use).

### 4. Run

```bash
./run.sh
```

## Usage Examples

```
🎯 What should I do? > Open Safari and go to google.com

🎯 What should I do? > Create a new folder on the desktop called "Projects"

🎯 What should I do? > Open Notes and create a new note with today's date

🎯 What should I do? > Take a screenshot and save it

🎯 What should I do? > Open System Settings and turn on Dark Mode
```

## Available Actions

The agent can perform these actions:

| Action | Description | Example |
|--------|-------------|---------|
| `click` | Single click | Click button at coordinates |
| `double_click` | Double click | Open file/folder |
| `right_click` | Right click | Context menu |
| `type` | Type ASCII text | Enter text in field |
| `type_unicode` | Type any text | Hindi, emoji, etc. |
| `hotkey` | Keyboard shortcut | Cmd+C, Cmd+V |
| `key` | Press single key | Enter, Tab, Escape |
| `move` | Move mouse | Hover over element |
| `scroll` | Scroll up/down | Navigate long pages |
| `drag` | Click and drag | Move files, select text |
| `wait` | Pause | Wait for UI to load |
| `open_app` | Open application | Launch Safari, Notes |
| `spotlight` | Open Spotlight | Quick app/file search |
| `run_command` | Run terminal command | Execute scripts |
| `screenshot` | Save screenshot | Debug/logging |

## Safety Features

1. **Failsafe**: Move mouse to any corner of the screen to immediately abort
2. **Action pause**: 0.5s pause between actions (configurable)
3. **Max iterations**: Stops after 10 steps (configurable)
4. **Confirmation**: Won't execute destructive commands without asking
5. **Visible actions**: All actions are logged to terminal

## Troubleshooting

### "Permission denied" or screen capture fails
→ Enable Screen Recording permission in System Settings

### Mouse/keyboard not working
→ Enable Accessibility permission in System Settings

### "Module not found" error
→ Make sure virtual environment is activated: `source venv/bin/activate`

### Agent clicking wrong locations
→ Screen resolution might have changed. Restart the agent.

### Agent stuck in loop
→ Move mouse to corner (failsafe) or Ctrl+C to stop

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  User Request                    │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Screen Capture                      │
│         (screencapture → base64)                │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Claude API (Vision)                 │
│   Analyzes screenshot + decides next action     │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Action Executor                     │
│         (PyAutoGUI + subprocess)                │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
                 Loop until
               task complete
```

## Configuration

Edit `agent.py` to customize:

```python
# Safety settings
pyautogui.FAILSAFE = True      # Corner abort (keep True!)
pyautogui.PAUSE = 0.5          # Seconds between actions

# In DesktopAgent.__init__:
self.model = "claude-sonnet-4-20250514"  # Or use opus for complex tasks

# In think_and_act():
max_iterations = 10            # Max steps before stopping
```

## API Cost Estimate

Each iteration sends ~1 screenshot to Claude. Approximate costs:
- Simple task (3-5 iterations): ~$0.03-0.05
- Complex task (10 iterations): ~$0.10-0.15

## Future Improvements

- [ ] GUI interface (menu bar app)
- [ ] Task recording/playback
- [ ] Custom action macros
- [ ] Multi-monitor support
- [ ] Voice commands via Whisper
- [ ] Integration with Onwords ecosystem

## License

Internal use - Onwords Smart Solutions

---

Built with ❤️ for Onwords by Claude
