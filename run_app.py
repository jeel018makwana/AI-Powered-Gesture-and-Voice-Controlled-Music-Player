import subprocess
import threading
import webbrowser
from backend.app import app
from backend.voice_control import start_voice

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Start browser after server is ready
    threading.Timer(2, open_browser).start()
    threading.Timer(3, start_voice).start()
    # Start Flask in main thread
    app.run(host="127.0.0.1", port=5000, debug=False)
