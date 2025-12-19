#!/usr/bin/env python3
"""
AegisAI - Unified Startup Script
Starts both backend and frontend servers
"""

import os
import sys
import subprocess
import time
import signal
import threading
import socket
from pathlib import Path

# Get the script directory
SCRIPT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
WEBSITE_DIR = SCRIPT_DIR / "website"
KEY_FILE = SCRIPT_DIR / "aegis-key.json"

# Global process references
backend_process = None
frontend_process = None


def cleanup():
    """Stop both servers"""
    print("\n🛑 Shutting down servers...")
    if backend_process:
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
        except:
            try:
                backend_process.kill()
            except:
                pass
    
    if frontend_process:
        try:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        except:
            try:
                frontend_process.kill()
            except:
                pass
    
    print("✅ Servers stopped")
    sys.exit(0)


def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    cleanup()


def check_port(port):
    """Check if a port is available"""
    # Try socket binding first (most reliable)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except OSError:
        sock.close()
        # Also check using netstat on Windows for confirmation
        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["netstat", "-ano"], 
                    capture_output=True, 
                    text=True, 
                    shell=True,
                    timeout=2
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        return False  # Port is definitely in use
            except:
                pass
        return False


def kill_process_on_port(port):
    """Kill process using the specified port (Windows)"""
    try:
        if sys.platform == "win32":
            # Use netstat to find processes
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            pids_found = []
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    # Parse the PID from the line (last column)
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit() and pid not in pids_found:
                            pids_found.append(pid)
            
            if pids_found:
                print(f"   Found {len(pids_found)} process(es) on port {port}: {', '.join(pids_found)}")
                killed_any = False
                for pid in pids_found:
                    try:
                        # Try graceful termination first
                        subprocess.run(
                            ["taskkill", "/PID", pid],
                            capture_output=True,
                            shell=True,
                            timeout=2
                        )
                        time.sleep(0.5)
                        # Force kill if still running
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True,
                            shell=True,
                            timeout=2
                        )
                        print(f"   ✅ Killed process {pid}")
                        killed_any = True
                    except subprocess.TimeoutExpired:
                        print(f"   ⚠️  Timeout killing process {pid}")
                    except Exception as e:
                        print(f"   ⚠️  Could not kill process {pid}: {e}")
                
                if killed_any:
                    # Wait for port to be released and verify
                    for attempt in range(8):  # Try up to 8 times (8 seconds)
                        time.sleep(1)
                        if check_port(port):
                            print(f"   ✅ Port {port} is now free (after {attempt + 1}s)")
                            return True
                    
                    print(f"   ⚠️  Port {port} may still be in use after cleanup")
                    return False
                else:
                    print(f"   ❌ Could not kill any processes on port {port}")
                    return False
            else:
                print(f"   ⚠️  No process found listening on port {port}")
                # Port might be in TIME_WAIT state, just wait
                return False
    except Exception as e:
        print(f"   ⚠️  Error checking port {port}: {e}")
        return False
    return False


def check_venv():
    """Check if virtual environment exists"""
    if not VENV_PYTHON.exists():
        print("❌ Virtual environment not found. Please run setup first:")
        print("   python3 -m venv .venv")
        print("   .venv\\Scripts\\activate")
        print("   pip install -r requirements.txt")
        sys.exit(1)


def check_node_modules():
    """Check if frontend dependencies are installed"""
    node_modules = WEBSITE_DIR / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=WEBSITE_DIR, check=True, shell=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install frontend dependencies")
            print("   Please run 'npm install' in the website directory manually")
            sys.exit(1)


def start_backend():
    """Start the backend server"""
    global backend_process
    
    # Set environment variable
    env = os.environ.copy()
    if KEY_FILE.exists():
        env["GOOGLE_APPLICATION_CREDENTIALS"] = str(KEY_FILE.resolve())
        print("✅ Google credentials configured")
    else:
        print("⚠️  Warning: aegis-key.json not found")
    
    # Change to script directory and start backend
    os.chdir(SCRIPT_DIR)
    sys.path.insert(0, str(SCRIPT_DIR))
    
    print("🔧 Starting backend server (port 8080)...")
    
    # Check if venv Python exists, otherwise use system Python
    python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    
    # Create log file for backend output
    log_file = SCRIPT_DIR / "backend.log"
    
    # Start uvicorn with output redirection to capture errors
    try:
        with open(log_file, 'w') as log:
            backend_process = subprocess.Popen(
                [python_exe, "-m", "uvicorn", "src.backend.main:app", 
                 "--host", "0.0.0.0", "--port", "8080"],
                env=env,
                cwd=SCRIPT_DIR,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" and hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None
    
    return backend_process


def start_frontend():
    """Start the frontend server"""
    global frontend_process
    
    print("🎨 Starting frontend server (port 8080)...")
    
    # On Windows, use shell=True and cmd.exe
    if sys.platform == "win32":
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=WEBSITE_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
        )
    else:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=WEBSITE_DIR
        )
    
    return frontend_process


def monitor_processes():
    """Monitor both processes"""
    try:
        while True:
            time.sleep(1)
            
            if backend_process and backend_process.poll() is not None:
                print("❌ Backend process exited unexpectedly")
                # Read and display error log
                log_file = SCRIPT_DIR / "backend.log"
                if log_file.exists():
                    print("\n📋 Backend error log:")
                    print("-" * 50)
                    try:
                        with open(log_file, 'r') as f:
                            print(f.read())
                    except:
                        pass
                    print("-" * 50)
                cleanup()
            
            if frontend_process and frontend_process.poll() is not None:
                print("❌ Frontend process exited unexpectedly")
                cleanup()
                
    except KeyboardInterrupt:
        cleanup()


def show_port_usage(port):
    """Show what's using a port"""
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            print(f"\n   Current processes on port {port}:")
            found_any = False
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    print(f"   {line.strip()}")
                    found_any = True
            if not found_any:
                print("   (none found)")
        except:
            pass


def main():
    """Main entry point"""
    print("🚀 Starting AegisAI...\n")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check prerequisites
    check_venv()
    check_node_modules()
    
    # Check if backend port is available (using 8080 now)
    print("🔍 Checking ports...")
    if not check_port(8080):
        print("⚠️  Port 8080 is already in use")
        show_port_usage(8080)
        print("\n   Attempting to find and kill the process...")
        killed = kill_process_on_port(8080)
        
        # Wait a bit and verify
        time.sleep(2)
        if not check_port(8080):
            print("\n❌ Port 8080 is still in use after cleanup attempt.")
            show_port_usage(8080)
            print("\n   Please run these commands manually to free the port:")
            print("   netstat -ano | findstr :8080")
            print("   taskkill /F /PID <pid_from_above>")
            print("\n   Or close the application using port 8080 and try again.")
            sys.exit(1)
        else:
            print("✅ Port 8080 is now free")
    else:
        print("✅ Port 8080 is available")
    
    # Check if frontend port is available (using 3000 now)
    if not check_port(3000):
        print("⚠️  Port 3000 is already in use")
        print("   Attempting to find and kill the process...")
        if kill_process_on_port(3000):
            # Verify port is now free
            if not check_port(3000):
                print("❌ Port 3000 is still in use after killing process.")
                print("   Please close the application using it manually and try again.")
                sys.exit(1)
        else:
            response = input("   Could not automatically free port 3000. Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ Cannot start frontend on port 3000")
                sys.exit(1)
    
    # Final port check right before starting
    print("\n🔍 Final port check before starting backend...")
    if not check_port(8080):
        print("❌ Port 8080 was taken between checks!")
        print("   Attempting emergency cleanup...")
        kill_process_on_port(8080)
        time.sleep(2)
        if not check_port(8080):
            print("❌ Cannot start backend - port 8080 is still in use")
            print("   Another process may have grabbed the port.")
            sys.exit(1)
    
    # Start servers
    print("\n🚀 Starting servers...")
    start_backend()
    if not backend_process:
        print("❌ Failed to start backend server")
        sys.exit(1)
    
    # Wait for backend to start and verify it's running
    print("⏳ Waiting for backend to initialize...")
    max_wait = 10  # Maximum seconds to wait
    waited = 0
    backend_ready = False
    
    while waited < max_wait:
        time.sleep(1)
        waited += 1
        
        # Check if process exited
        if backend_process.poll() is not None:
            # Process exited, check the log
            print("❌ Backend failed to start")
            log_file = SCRIPT_DIR / "backend.log"
            if log_file.exists():
                print("\n📋 Backend error log:")
                print("-" * 50)
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        print(content)
                        # Check for port binding error
                        if "10048" in content or "address already in use" in content.lower() or "error while attempting to bind" in content.lower():
                            print("\n💡 Tip: Port 8000 is still in use. Try:")
                            print("   1. Close any other applications using port 8000")
                            print("   2. Wait a few seconds and try again")
                            print("   3. Run: netstat -ano | findstr :8000  to find the process")
                            print("   4. Run: taskkill /F /PID <pid>  to kill it")
                except:
                    pass
                print("-" * 50)
            sys.exit(1)
        
        # Try to connect to health endpoint
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:8080/health", timeout=1)
            if response.getcode() == 200:
                print("✅ Backend is running and responding")
                backend_ready = True
                break
        except:
            pass  # Not ready yet, keep waiting
    
    if not backend_ready:
        if backend_process.poll() is None:
            print("⚠️  Backend process is running but not responding to health checks")
            print("   It may still be initializing. Continuing anyway...")
        else:
            print("❌ Backend failed to start within timeout period")
            sys.exit(1)
    
    start_frontend()
    time.sleep(3)  # Wait for frontend to start
    
    print("\n✅ AegisAI is running!")
    print("   Backend:  http://localhost:8080")
    print("   Frontend: http://localhost:3000")
    print("\nPress Ctrl+C to stop both servers\n")
    
    # Monitor processes
    monitor_processes()


if __name__ == "__main__":
    main()

