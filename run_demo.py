"""
MedFlow AI - Unified System Launcher
Launches both the FastAPI REST/WebSocket backend and the Streamlit Operations Dashboard.
"""

import sys
import time
import subprocess
from pathlib import Path

# Fix Windows console UTF-8 output if supported
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent

def run_system():
    print("=" * 70)
    print("  [+] STARTING MEDFLOW AI AUTONOMOUS EMERGENCY OPERATIONS CENTER")
    print("=" * 70)
    print(f"Project Directory: {ROOT_DIR}")
    
    python_exe = sys.executable
    
    # 1. Start FastAPI Backend in subprocess
    print("\n[1/2] Launching FastAPI Backend on http://localhost:8000 ...")
    backend_cmd = [
        python_exe, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0", "--port", "8000"
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR))
    time.sleep(2)
    
    # 2. Start Streamlit Frontend in subprocess
    print("[2/2] Launching Interactive Operations Dashboard on http://localhost:8501 ...")
    frontend_cmd = [
        python_exe, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501", "--server.headless", "true"
    ]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(ROOT_DIR))
    
    print("\n" + "=" * 70)
    print("  [OK] MEDFLOW AI RUNNING SUCCESSFULLY!")
    print("  [*] Dashboard URL:      http://localhost:8501")
    print("  [*] API Docs (Swagger): http://localhost:8000/docs")
    print("  [*] WebSocket Channel:  ws://localhost:8000/ws/operations")
    print("=" * 70)
    print("Press Ctrl+C to terminate both servers safely.\n")
    
    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down MedFlow AI...")
        frontend_proc.terminate()
        backend_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    run_system()
