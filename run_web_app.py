"""
Launcher for CryptoPulse Web Application.
Automatically starts the Flask server and opens the browser interface.
"""

import os
import sys
import time
import webbrowser
import threading

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def open_browser():
    time.sleep(1.5)
    print("[INFO] Opening CryptoPulse Web Dashboard in browser...")
    try:
        webbrowser.open("http://127.0.0.1:5000")
    except Exception:
        pass

def main():
    print("=" * 80)
    print("  LAUNCHING CRYPTOPULSE - CRYPTO TRANSACTION & AML TRACKER")
    print("=" * 80)
    print("Project Directory:", os.path.dirname(os.path.abspath(__file__)))
    print("Server URL: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server at any time.\n")

    threading.Thread(target=open_browser, daemon=True).start()

    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
