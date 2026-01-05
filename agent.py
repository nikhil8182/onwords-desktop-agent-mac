#!/usr/bin/env python3
"""
Onwords Desktop Agent - Mac Edition
An AI-powered desktop automation agent that can see and control your Mac.
"""

import pyautogui
import base64
import json
import time
import subprocess
from io import BytesIO
from PIL import ImageGrab, Image
import os
from datetime import datetime
from providers import create_provider, AIProvider
from overlay import FloatingOverlay
from voice_input import listen_for_command

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.5  # Pause between actions

class DesktopAgent:
    # USD to INR exchange rate (approximately)
    USD_TO_INR = 83.5
    
    def __init__(
        self,
        provider_type: str = "claude",
        api_key: str = None,
        model: str = None
    ):
        """
        Initialize the desktop agent with an AI provider.

        Args:
            provider_type: 'claude' or 'gemini' (default: 'claude')
            api_key: API key for the provider (defaults to env vars)
            model: Optional model name (uses provider default if not provided)
        """
        self.provider_type = provider_type.lower()

        # Get API key from parameter or environment variable
        if not api_key:
            if self.provider_type == "claude":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.provider_type in ["gemini", "google"]:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        if not api_key:
            if self.provider_type == "claude":
                raise ValueError("Please set ANTHROPIC_API_KEY environment variable or pass api_key")
            else:
                raise ValueError("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable or pass api_key")

        # Create provider
        self.provider = create_provider(self.provider_type, api_key, model)
        self.provider_name = self.provider.get_provider_name()

        self.screen_width, self.screen_height = pyautogui.size()
        self.conversation_history = []
        self.screenshots_dir = "screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Track usage and costs
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.usage_history = []  # Store usage per iteration

        # Initialize overlay
        self.overlay = FloatingOverlay()
        self.overlay.start()

        self.overlay.log(f"Using {self.provider_name.upper()} provider", "success")
        self.overlay.log(f"Screen: {self.screen_width}x{self.screen_height}", "info")
        self.overlay.log("Failsafe: Move mouse to top-left corner to abort", "info")

        print(f"🤖 Using {self.provider_name.upper()} provider")
        print(f"🖥️  Screen size: {self.screen_width}x{self.screen_height}")
        print(f"🛡️  Failsafe enabled: Move mouse to top-left corner to abort")
        print(f"⏸️  Action pause: {pyautogui.PAUSE}s between actions")

    def capture_screen(self, save=False) -> str:
        """Capture the screen and return base64 encoded image."""
        # Use screencapture on Mac for better quality
        temp_path = "/tmp/screenshot_temp.png"
        subprocess.run(["screencapture", "-x", temp_path], check=True)

        with Image.open(temp_path) as img:
            # Resize for API (max 1568px on longest side for efficiency)
            max_size = 1568
            ratio = min(max_size / img.width, max_size / img.height)
            if ratio < 1:
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            base64_image = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

            if save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"{self.screenshots_dir}/screen_{timestamp}.png"
                img.save(save_path)
                self.overlay.log(f"Screenshot saved: {save_path}", "info")

        return base64_image

    def execute_action(self, action: dict) -> str:
        """Execute a single action and return result."""
        action_type = action.get("type")
        result = ""

        try:
            if action_type == "click":
                x, y = action["x"], action["y"]
                button = action.get("button", "left")
                clicks = action.get("clicks", 1)
                pyautogui.click(x, y, clicks=clicks, button=button)
                result = f"Clicked at ({x}, {y}) with {button} button"

            elif action_type == "double_click":
                x, y = action["x"], action["y"]
                pyautogui.doubleClick(x, y)
                result = f"Double-clicked at ({x}, {y})"

            elif action_type == "right_click":
                x, y = action["x"], action["y"]
                pyautogui.rightClick(x, y)
                result = f"Right-clicked at ({x}, {y})"

            elif action_type == "type":
                text = action["text"]
                interval = action.get("interval", 0.02)
                pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)
                result = f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"

            elif action_type == "type_unicode":
                # For non-ASCII text on Mac
                text = action["text"]
                subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'])
                result = f"Typed (unicode): {text[:50]}{'...' if len(text) > 50 else ''}"

            elif action_type == "hotkey":
                keys = action["keys"]
                pyautogui.hotkey(*keys)
                result = f"Pressed hotkey: {'+'.join(keys)}"

            elif action_type == "key":
                key = action["key"]
                presses = action.get("presses", 1)
                pyautogui.press(key, presses=presses)
                result = f"Pressed key: {key}"

            elif action_type == "move":
                x, y = action["x"], action["y"]
                duration = action.get("duration", 0.3)
                pyautogui.moveTo(x, y, duration=duration)
                result = f"Moved mouse to ({x}, {y})"

            elif action_type == "scroll":
                amount = action["amount"]
                x, y = action.get("x"), action.get("y")
                if x and y:
                    pyautogui.scroll(amount, x, y)
                else:
                    pyautogui.scroll(amount)
                result = f"Scrolled {'down' if amount < 0 else 'up'} by {abs(amount)}"

            elif action_type == "drag":
                start_x, start_y = action["start_x"], action["start_y"]
                end_x, end_y = action["end_x"], action["end_y"]
                duration = action.get("duration", 0.5)
                pyautogui.moveTo(start_x, start_y)
                pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
                result = f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"

            elif action_type == "screenshot":
                self.capture_screen(save=True)
                result = "Screenshot captured and saved"

            elif action_type == "wait":
                seconds = action.get("seconds", 1)
                time.sleep(seconds)
                result = f"Waited {seconds} seconds"

            elif action_type == "open_app":
                app_name = action["app"]
                subprocess.run(["open", "-a", app_name])
                time.sleep(1)  # Wait for app to open
                result = f"Opened application: {app_name}"

            elif action_type == "run_command":
                command = action["command"]
                output = subprocess.run(command, shell=True, capture_output=True, text=True)
                result = f"Ran command: {command}\nOutput: {output.stdout[:200]}"

            elif action_type == "spotlight":
                # Open Spotlight search
                pyautogui.hotkey("command", "space")
                time.sleep(0.3)
                if "query" in action:
                    pyautogui.typewrite(action["query"])
                result = f"Opened Spotlight" + (f" with query: {action.get('query', '')}" if "query" in action else "")

            else:
                result = f"Unknown action type: {action_type}"

        except Exception as e:
            result = f"Error executing {action_type}: {str(e)}"

        self.overlay.log(result, "action")
        return result

    def get_system_prompt(self) -> str:
        return f"""You are a desktop automation agent controlling a Mac computer.

SCREEN INFO:
- Resolution: {self.screen_width}x{self.screen_height}
- You will see screenshots of the current screen state

AVAILABLE ACTIONS (respond with JSON):
{{
    "thinking": "Your reasoning about what you see and what to do",
    "actions": [
        {{"type": "click", "x": 100, "y": 200, "button": "left", "clicks": 1}},
        {{"type": "double_click", "x": 100, "y": 200}},
        {{"type": "right_click", "x": 100, "y": 200}},
        {{"type": "type", "text": "Hello world"}},
        {{"type": "type_unicode", "text": "नमस्ते"}},
        {{"type": "hotkey", "keys": ["command", "c"]}},
        {{"type": "key", "key": "enter", "presses": 1}},
        {{"type": "move", "x": 100, "y": 200}},
        {{"type": "scroll", "amount": -3, "x": 500, "y": 500}},
        {{"type": "drag", "start_x": 100, "start_y": 100, "end_x": 200, "end_y": 200}},
        {{"type": "wait", "seconds": 2}},
        {{"type": "open_app", "app": "Safari"}},
        {{"type": "spotlight", "query": "Calculator"}},
        {{"type": "run_command", "command": "ls -la"}},
        {{"type": "screenshot"}}
    ],
    "status": "continue" | "complete" | "need_help",
    "message": "What you did or need"
}}

MAC KEYBOARD SHORTCUTS:
- command+c/v/x: Copy/Paste/Cut
- command+tab: Switch apps
- command+space: Spotlight
- command+q: Quit app
- command+w: Close window
- command+s: Save
- command+shift+3: Screenshot
- control+command+space: Emoji picker

GUIDELINES:
1. Always analyze the screenshot carefully before acting
2. Click on the CENTER of buttons/elements
3. Wait for UI to respond after clicks before next action
4. Use Spotlight (command+space) to open apps quickly
5. Be precise with coordinates - estimate based on what you see
6. If something fails, try an alternative approach
7. Set status to "complete" when the task is done
8. Set status to "need_help" if you're stuck or need clarification

SAFETY:
- Never execute destructive commands without explicit confirmation
- Don't access sensitive files/folders unless specifically asked
- If unsure, ask for clarification instead of guessing"""

    def think_and_act(self, user_request: str, max_iterations: int = 10) -> str:
        """Main loop: observe screen, think, act, repeat."""

        self.overlay.log(f"Task: {user_request}", "step")
        print(f"\n🎯 Task: {user_request}\n")
        print("=" * 50)

        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            self.overlay.log(f"Step {iteration}/{max_iterations}", "step")
            print(f"\n📍 Step {iteration}/{max_iterations}")

            # Capture current screen state
            self.overlay.log("Capturing screen...", "info")
            screenshot_b64 = self.capture_screen()

            # Build message with screenshot
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""Current task: {user_request}

Previous actions in this session: {json.dumps(self.conversation_history[-5:]) if self.conversation_history else "None yet"}

Analyze the screenshot and decide what action(s) to take next. Respond with JSON only."""
                        }
                    ]
                }
            ]

            # Get AI response using provider
            self.overlay.log(f"Thinking ({self.provider_name})...", "think")
            print(f"   🤔 Thinking ({self.provider_name})...")
            system_prompt = self.get_system_prompt()

            result = self.provider.generate_response(
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=2048
            )

            # Extract usage data
            input_tokens = result["input_tokens"]
            output_tokens = result["output_tokens"]
            cost = result["cost"]
            response_text = result["text"]

            # Update totals
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cost += cost

            # Store usage for this iteration
            usage_data = {
                "iteration": iteration,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": cost
            }
            self.usage_history.append(usage_data)

            # Display usage and cost for this move
            self.overlay.log(f"Cost: ${cost:.6f} | Tokens: {input_tokens + output_tokens:,}", "info")
            print(f"   💰 Step {iteration} Cost: ${cost:.6f} | Input: {input_tokens:,} tokens | Output: {output_tokens:,} tokens")
            print(f"   📊 Cumulative: ${self.total_cost:.6f} | Total tokens: {self.total_input_tokens + self.total_output_tokens:,}")

            # Parse JSON response
            try:
                # Handle potential markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]

                result = json.loads(response_text.strip())
            except json.JSONDecodeError:
                self.overlay.log("Failed to parse AI response", "error")
                print(f"   ⚠️  Failed to parse response: {response_text[:200]}")
                continue

            # Show thinking
            if "thinking" in result:
                self.overlay.log(result['thinking'][:100] + "...", "think")
                print(f"   💭 {result['thinking'][:150]}...")

            # Execute actions
            if "actions" in result and result["actions"]:
                self.overlay.log(f"Executing {len(result['actions'])} action(s)", "action")
                print(f"   🎬 Executing {len(result['actions'])} action(s):")
                for action in result["actions"]:
                    action_result = self.execute_action(action)
                    self.conversation_history.append({
                        "action": action,
                        "result": action_result,
                        "step": iteration,
                        "usage": usage_data  # Include usage data with each action
                    })
                    time.sleep(0.3)  # Brief pause between actions

            # Check status
            status = result.get("status", "continue")
            message = result.get("message", "")

            if status == "complete":
                self.overlay.log(f"Task completed: {message}", "success")
                print(f"\n✅ Task completed: {message}")
                print(f"\n📈 Final Usage Summary:")
                print(f"   Total Input Tokens: {self.total_input_tokens:,}")
                print(f"   Total Output Tokens: {self.total_output_tokens:,}")
                print(f"   Total Tokens: {self.total_input_tokens + self.total_output_tokens:,}")
                total_cost_inr = self.total_cost * self.USD_TO_INR
                print(f"   Total Cost: ${self.total_cost:.6f} (₹{total_cost_inr:.4f})")
                return f"Task completed: {message}"

            elif status == "need_help":
                self.overlay.log(f"Need help: {message}", "error")
                print(f"\n❓ Need help: {message}")
                return f"Need clarification: {message}"

            # Small delay before next iteration
            time.sleep(0.5)

        self.overlay.log(f"Reached max iterations ({max_iterations})", "error")
        print(f"\n⚠️  Reached maximum iterations ({max_iterations})")
        print(f"\n📈 Final Usage Summary:")
        print(f"   Total Input Tokens: {self.total_input_tokens:,}")
        print(f"   Total Output Tokens: {self.total_output_tokens:,}")
        print(f"   Total Tokens: {self.total_input_tokens + self.total_output_tokens:,}")
        total_cost_inr = self.total_cost * self.USD_TO_INR
        print(f"   Total Cost: ${self.total_cost:.6f} (₹{total_cost_inr:.4f})")
        return "Reached maximum iterations without completing task"


def main():
    """Interactive CLI for the desktop agent."""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     🤖 Onwords Desktop Agent - Mac Edition            ║
    ╠═══════════════════════════════════════════════════════╣
    ║  Commands:                                            ║
    ║    • Type task or 'voice' for voice input             ║
    ║    • 'quit' to exit                                   ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    try:
        # Try Claude first, then Gemini
        api_key = os.getenv("ANTHROPIC_API_KEY")
        provider_type = "claude"

        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            provider_type = "gemini"

        agent = DesktopAgent(provider_type=provider_type, api_key=api_key)
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nTo set your API key:")
        print("  For Claude: export ANTHROPIC_API_KEY='your-key-here'")
        print("  For Gemini: export GOOGLE_API_KEY='your-key-here'")
        return

    while True:
        try:
            user_input = input("\n🎯 Task (or 'voice'): ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            # Voice input option
            if user_input.lower() in ["voice", "v", "speak"]:
                user_input = listen_for_command()
                if not user_input:
                    continue
                print(f"🎯 Running: {user_input}")

            agent.overlay.clear()
            agent.overlay.log(f"Task: {user_input}", "step")
            result = agent.think_and_act(user_input)
            agent.overlay.log(f"Result: {result}", "success")
            print(f"\n📋 Result: {result}")

        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break
        except pyautogui.FailSafeException:
            print("\n🛑 Failsafe! Mouse moved to corner.")
            agent.overlay.log("ABORTED - Failsafe triggered", "error")


if __name__ == "__main__":
    main()
