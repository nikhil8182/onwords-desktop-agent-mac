#!/usr/bin/env python3
"""
Onwords Desktop Agent - Mac Edition (GUI Version)
A simple GUI wrapper for the desktop agent.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import os
import sys

# Import the main agent
from agent import DesktopAgent


class AgentGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Onwords Desktop Agent")
        self.root.geometry("600x500")
        self.root.configure(bg="#1a1a2e")
        
        # Message queue for thread-safe updates
        self.msg_queue = queue.Queue()
        
        # Agent instance
        self.agent = None
        self.is_running = False
        
        self.setup_ui()
        self.check_queue()
        
    def setup_ui(self):
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header = tk.Label(
            self.root,
            text="🤖 Onwords Desktop Agent",
            font=("SF Pro Display", 24, "bold"),
            fg="#00d4ff",
            bg="#1a1a2e"
        )
        header.pack(pady=20)
        
        # Status
        self.status_var = tk.StringVar(value="⚪ Not connected")
        status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("SF Pro Text", 12),
            fg="#888",
            bg="#1a1a2e"
        )
        status_label.pack()
        
        # Input frame
        input_frame = tk.Frame(self.root, bg="#1a1a2e")
        input_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(
            input_frame,
            text="What should I do?",
            font=("SF Pro Text", 14),
            fg="#fff",
            bg="#1a1a2e"
        ).pack(anchor=tk.W)
        
        self.task_entry = tk.Entry(
            input_frame,
            font=("SF Pro Text", 14),
            bg="#16213e",
            fg="#fff",
            insertbackground="#fff",
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground="#0f3460",
            highlightcolor="#00d4ff"
        )
        self.task_entry.pack(fill=tk.X, pady=10, ipady=10)
        self.task_entry.bind("<Return>", lambda e: self.start_task())
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(fill=tk.X, padx=20)
        
        self.run_btn = tk.Button(
            btn_frame,
            text="▶ Run Task",
            font=("SF Pro Text", 12, "bold"),
            bg="#00d4ff",
            fg="#000",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.start_task
        )
        self.run_btn.pack(side=tk.LEFT)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ Stop",
            font=("SF Pro Text", 12),
            bg="#e94560",
            fg="#fff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.stop_task,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Log area
        log_frame = tk.Frame(self.root, bg="#1a1a2e")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            log_frame,
            text="Activity Log",
            font=("SF Pro Text", 12),
            fg="#888",
            bg="#1a1a2e"
        ).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("SF Mono", 11),
            bg="#16213e",
            fg="#0f0",
            relief=tk.FLAT,
            height=12
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Initialize agent
        self.init_agent()
        
    def init_agent(self):
        """Initialize the desktop agent."""
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                self.status_var.set("❌ API key not set")
                self.log("ERROR: ANTHROPIC_API_KEY not set in environment")
                self.log("Set it with: export ANTHROPIC_API_KEY='your-key'")
                return
                
            self.agent = DesktopAgent(api_key)
            self.status_var.set("🟢 Ready")
            self.log("Agent initialized successfully")
            self.log(f"Screen: {self.agent.screen_width}x{self.agent.screen_height}")
            
        except Exception as e:
            self.status_var.set("❌ Error")
            self.log(f"ERROR: {str(e)}")
            
    def log(self, message):
        """Add message to log (thread-safe)."""
        self.msg_queue.put(message)
        
    def check_queue(self):
        """Check message queue and update log."""
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self.log_text.insert(tk.END, f"{msg}\n")
            self.log_text.see(tk.END)
        self.root.after(100, self.check_queue)
        
    def start_task(self):
        """Start executing a task."""
        if not self.agent:
            messagebox.showerror("Error", "Agent not initialized. Check API key.")
            return
            
        task = self.task_entry.get().strip()
        if not task:
            return
            
        self.is_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("🔵 Running...")
        self.log(f"\n{'='*40}")
        self.log(f"TASK: {task}")
        self.log(f"{'='*40}")
        
        # Run in separate thread
        thread = threading.Thread(target=self.run_task, args=(task,))
        thread.daemon = True
        thread.start()
        
    def run_task(self, task):
        """Run task in background thread."""
        try:
            # Redirect agent's print to our log
            original_print = print
            def custom_print(*args, **kwargs):
                self.log(" ".join(str(a) for a in args))
            
            import builtins
            builtins.print = custom_print
            
            result = self.agent.think_and_act(task)
            self.log(f"\nRESULT: {result}")
            
            builtins.print = original_print
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, self.task_complete)
            
    def task_complete(self):
        """Called when task completes."""
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("🟢 Ready")
        
    def stop_task(self):
        """Stop the current task."""
        self.is_running = False
        self.log("⚠️ Stop requested...")
        self.status_var.set("🟡 Stopping...")
        # Note: This won't immediately stop PyAutoGUI actions
        # User should use failsafe (mouse to corner) for immediate stop
        
    def run(self):
        """Start the GUI."""
        self.root.mainloop()


def main():
    # Check if running in a GUI environment
    if sys.platform == "darwin":  # macOS
        try:
            app = AgentGUI()
            app.run()
        except tk.TclError:
            print("Cannot open GUI. Make sure you're running from a terminal with display access.")
            print("Falling back to CLI mode...")
            from agent import main as cli_main
            cli_main()
    else:
        print("GUI only supported on macOS. Use agent.py directly.")


if __name__ == "__main__":
    main()
