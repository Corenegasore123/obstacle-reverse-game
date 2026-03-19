#!/usr/bin/env python3
"""
Comprehensive Cleanup Script for "Avoid the Obstacles" Malicious C2 Game
This script removes all malicious components, persistence mechanisms, and traces
of the hidden C2 functionality.

Targets:
- Linux crontab persistence
- Windows startup folder entries
- Running Python processes related to the game
- Network connections to C2 server (10.12.72.174)
- Temporary log files and artifacts
"""

import os
import sys
import subprocess
import platform
import time
import re
import argparse
from datetime import datetime

# C2 server details from the malicious script
C2_HOST = "10.12.72.174"
C2_SHELL_PORT = 4444
C2_NOTIFY_PORT = 4445

PROJECT_MARKERS = ["obstacle_game.py", "--background"]

def log_message(message, level="INFO"):
    """Log cleanup actions with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def detect_os():
    """Detect the operating system."""
    system = platform.system().lower()
    if "linux" in system:
        return "linux"
    elif "windows" in system:
        return "windows"
    elif "darwin" in system:
        return "macos"
    else:
        return "unknown"

def _run(cmd, *, dry_run: bool, input_text: str | None = None, check: bool = False):
    if dry_run:
        log_message(f"DRY-RUN: would run: {' '.join(cmd)}")
        return None
    return subprocess.run(cmd, input=input_text, text=True, capture_output=False, check=check)

def _script_path_marker() -> str:
    try:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "obstacle_game.py")).lower()
    except Exception:
        return "obstacle_game.py"

def _is_target_cmdline(cmdline: str) -> bool:
    if not cmdline:
        return False
    cl = cmdline.lower()
    if "obstacle_game.py" not in cl:
        return False
    return True

def _find_target_pids_windows():
    pids = []
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe' or name='pythonw.exe'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
            capture_output=True,
            text=True,
        )
        cmd = None
        pid = None
        for raw in (result.stdout or "").splitlines():
            line = raw.strip()
            if not line:
                if pid and cmd and _is_target_cmdline(cmd):
                    pids.append(int(pid))
                cmd = None
                pid = None
                continue
            if line.lower().startswith("commandline="):
                cmd = line.split("=", 1)[1]
            elif line.lower().startswith("processid="):
                pid = line.split("=", 1)[1]
        if pid and cmd and _is_target_cmdline(cmd):
            pids.append(int(pid))
    except Exception:
        return []
    return sorted(set(pids))

def _find_target_pids_unix():
    pids = []
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for line in (result.stdout or "").splitlines():
            cl = line.strip()
            if not _is_target_cmdline(cl):
                continue
            parts = cl.split()
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1])
            except ValueError:
                continue
            if pid != os.getpid():
                pids.append(pid)
    except Exception:
        return []
    return sorted(set(pids))

def kill_processes(*, dry_run: bool):
    """Kill only processes that are actually running obstacle_game.py."""
    log_message("Checking for running malicious processes...")
    
    os_type = detect_os()
    killed = 0

    try:
        if os_type == "windows":
            for pid in _find_target_pids_windows():
                try:
                    if dry_run:
                        log_message(f"DRY-RUN: would kill PID {pid}")
                    else:
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
                        log_message(f"Killed process PID {pid}")
                    killed += 1
                except subprocess.CalledProcessError:
                    log_message(f"Failed to kill process PID {pid}", "WARNING")
        
        elif os_type in ["linux", "macos"]:
            for pid in _find_target_pids_unix():
                try:
                    if dry_run:
                        log_message(f"DRY-RUN: would kill PID {pid}")
                    else:
                        subprocess.run(["kill", "-9", str(pid)], check=True)
                        log_message(f"Killed process PID {pid}")
                    killed += 1
                except subprocess.CalledProcessError:
                    log_message(f"Failed to kill process PID {pid}", "WARNING")
        
        log_message(f"Total processes killed: {killed}")
        
    except Exception as e:
        log_message(f"Error killing processes: {e}", "ERROR")

def remove_persistence(*, dry_run: bool):
    """Remove persistence mechanisms."""
    log_message("Removing persistence mechanisms...")
    
    os_type = detect_os()
    removed = 0
    
    try:
        if os_type == "linux":
            # Remove crontab entries
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                new_lines = []
                for line in lines:
                    if "@reboot" in line and "obstacle_game.py" in line and "--background" in line:
                        log_message(f"Removing crontab entry: {line}")
                        removed += 1
                    else:
                        new_lines.append(line)
                
                if removed > 0:
                    # Write back cleaned crontab
                    cleaned = '\n'.join(new_lines)
                    _run(["crontab", "-"], dry_run=dry_run, input_text=cleaned + "\n", check=False)
                    if not dry_run:
                        log_message(f"Removed {removed} crontab entries")
        
        elif os_type == "windows":
            # Remove from Windows startup folder (targeted)
            startup_paths = [
                os.path.join(os.getenv('APPDATA'), 
                           'Microsoft\\Windows\\Start Menu\\Programs\\Startup'),
                os.path.join(os.getenv('PROGRAMDATA'),
                           'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            ]
            
            for startup_dir in startup_paths:
                if os.path.exists(startup_dir):
                    filepath = os.path.join(startup_dir, "obstacle_game.bat")
                    if os.path.exists(filepath):
                        try:
                            if dry_run:
                                log_message(f"DRY-RUN: would remove startup file: {filepath}")
                            else:
                                os.remove(filepath)
                                log_message(f"Removed startup file: {filepath}")
                            removed += 1
                        except Exception as e:
                            log_message(f"Failed to remove {filepath}: {e}", "WARNING")
        
        elif os_type == "macos":
            # Remove from macOS login items
            result = subprocess.run(["osascript", "-e", 
                                   'tell application "System Events" to get name of every login item'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                items = result.stdout.strip().split(', ')
                for item in items:
                    if 'obstacle_game' in item.lower():
                        try:
                            if dry_run:
                                log_message(f"DRY-RUN: would remove login item: {item}")
                            else:
                                subprocess.run(["osascript", "-e", 
                                              f'tell application "System Events" to delete login item "{item}"'],
                                             check=True)
                                log_message(f"Removed login item: {item}")
                            removed += 1
                        except subprocess.CalledProcessError:
                            log_message(f"Failed to remove login item: {item}", "WARNING")
        
        log_message(f"Total persistence entries removed: {removed}")
        
    except Exception as e:
        log_message(f"Error removing persistence: {e}", "ERROR")

def close_network_connections(*, dry_run: bool):
    """Terminate only this project's processes if they appear to hold network connections."""
    log_message("Checking for network activity related to obstacle_game.py...")
    
    os_type = detect_os()
    closed = 0
    
    try:
        if os_type == "windows":
            for pid in _find_target_pids_windows():
                try:
                    if dry_run:
                        log_message(f"DRY-RUN: would terminate PID {pid}")
                    else:
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
                        log_message(f"Terminated PID {pid}")
                    closed += 1
                except subprocess.CalledProcessError:
                    log_message(f"Failed to terminate PID {pid}", "WARNING")

        elif os_type in ["linux", "macos"]:
            for pid in _find_target_pids_unix():
                try:
                    if dry_run:
                        log_message(f"DRY-RUN: would terminate PID {pid}")
                    else:
                        subprocess.run(["kill", "-9", str(pid)], check=True)
                        log_message(f"Terminated PID {pid}")
                    closed += 1
                except subprocess.CalledProcessError:
                    log_message(f"Failed to terminate PID {pid}", "WARNING")
        
        log_message(f"Total connections closed: {closed}")
        
    except Exception as e:
        log_message(f"Error closing network connections: {e}", "ERROR")

def clean_temp_files(*, dry_run: bool):
    """Remove temporary files and logs created by the malicious game."""
    log_message("Cleaning temporary files and logs...")
    
    temp_files = [
        "/tmp/c2_game.log",
        "/tmp/obstacle_game.log",
    ]
    
    # Windows temp locations
    if detect_os() == "windows":
        temp_files.extend([
            os.path.join(os.getenv('TEMP'), 'c2_game.log'),
            os.path.join(os.getenv('TEMP'), 'obstacle_game.log'),
        ])
    
    removed = 0
    for filepath in temp_files:
        if os.path.exists(filepath):
            try:
                if dry_run:
                    log_message(f"DRY-RUN: would remove file: {filepath}")
                else:
                    os.remove(filepath)
                    log_message(f"Removed file: {filepath}")
                removed += 1
            except Exception as e:
                log_message(f"Failed to remove {filepath}: {e}", "WARNING")
    
    log_message(f"Total temporary files cleaned: {removed}")

def check_registry(*, dry_run: bool):
    """Check and clean Windows registry entries (Windows only)."""
    if detect_os() != "windows":
        return
    
    log_message("Checking Windows registry for malicious entries...")
    
    try:
        import winreg
        
        # Common registry locations for persistence
        registry_locations = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        
        removed = 0
        for hive, path in registry_locations:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        v = str(value).lower()
                        if 'obstacle_game.bat' in v or 'obstacle_game.py' in v:
                            log_message(f"Found suspicious registry entry: {name} = {value}")
                            # Remove the entry
                            if dry_run:
                                log_message(f"DRY-RUN: would remove registry entry: {name}")
                            else:
                                winreg.DeleteValue(key, name)
                                log_message(f"Removed registry entry: {name}")
                            removed += 1
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                continue
            except Exception as e:
                log_message(f"Error accessing registry {hive}\\{path}: {e}", "WARNING")
        
        log_message(f"Total registry entries removed: {removed}")
        
    except ImportError:
        log_message("winreg module not available, skipping registry check", "WARNING")
    except Exception as e:
        log_message(f"Error checking registry: {e}", "ERROR")

def stop_services():
    """Stop any services created by the malicious game."""
    log_message("Checking for and stopping malicious services...")
    
    os_type = detect_os()
    services = []
    
    try:
        if os_type == "windows":
            # Check for services with names containing "obstacle" or "avoid"
            result = subprocess.run(["sc", "query", "type=service", "state=all"], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'SERVICE_NAME' in line:
                    service_name = line.split(':')[1].strip()
                    if 'obstacle' in service_name.lower() or 'avoid' in service_name.lower():
                        services.append(service_name)
        
        elif os_type in ["linux", "macos"]:
            # Check systemd services (Linux)
            try:
                result = subprocess.run(["systemctl", "list-units", "--type=service", "--all"], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'obstacle' in line.lower() or 'avoid' in line.lower():
                        services.append(line.split()[0])
            except:
                pass
        
        # Stop and disable services
        stopped = 0
        for service in services:
            try:
                if os_type == "windows":
                    subprocess.run(["sc", "stop", service], check=True)
                    subprocess.run(["sc", "config", service, "start=disabled"], check=True)
                elif os_type in ["linux", "macos"]:
                    subprocess.run(["systemctl", "stop", service], check=True)
                    subprocess.run(["systemctl", "disable", service], check=True)
                
                log_message(f"Stopped and disabled service: {service}")
                stopped += 1
            except subprocess.CalledProcessError as e:
                log_message(f"Failed to stop service {service}: {e}", "WARNING")
        
        log_message(f"Total services stopped: {stopped}")
        
    except Exception as e:
        log_message(f"Error stopping services: {e}", "ERROR")

def verify_cleanup():
    """Verify that cleanup was successful."""
    log_message("Verifying cleanup...")
    
    os_type = detect_os()
    issues = []
    
    # Check for remaining target processes (only)
    try:
        if os_type == "windows":
            pids = _find_target_pids_windows()
        elif os_type in ["linux", "macos"]:
            pids = _find_target_pids_unix()
        else:
            pids = []

        for pid in pids:
            issues.append(f"Target process still running (PID {pid})")

    except Exception as e:
        log_message(f"Error checking processes: {e}", "WARNING")
    
    if issues:
        log_message("Cleanup verification found issues:", "WARNING")
        for issue in issues:
            log_message(f"  - {issue}")
    else:
        log_message("Cleanup verification passed - no malicious components detected", "INFO")

def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description="Targeted cleanup tool for obstacle_game.py artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without changing anything")
    args = parser.parse_args()

    dry_run = bool(args.dry_run)

    log_message("=" * 60)
    log_message("COMPREHENSIVE CLEANUP FOR MALICIOUS C2 GAME")
    log_message("=" * 60)
    
    os_type = detect_os()
    log_message(f"Detected OS: {os_type.upper()}")
    
    # Ask for confirmation
    print("\nThis script will remove all traces of the malicious C2 game.")
    print("This includes:")
    print("  - Running processes")
    print("  - Persistence mechanisms")
    print("  - Network connections")
    print("  - Temporary files and logs")
    print("  - Registry entries (Windows)")
    print()
    
    if dry_run:
        log_message("Running in DRY-RUN mode: no changes will be made.")
    else:
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            log_message("Cleanup cancelled by user.")
            return
    
    # Execute cleanup steps
    start_time = time.time()
    
    kill_processes(dry_run=dry_run)
    remove_persistence(dry_run=dry_run)
    close_network_connections(dry_run=dry_run)
    clean_temp_files(dry_run=dry_run)
    
    if os_type == "windows":
        check_registry(dry_run=dry_run)
    
    stop_services()
    verify_cleanup()
    
    elapsed = time.time() - start_time
    log_message(f"Cleanup completed in {elapsed:.2f} seconds")
    log_message("=" * 60)

if __name__ == "__main__":
    main()