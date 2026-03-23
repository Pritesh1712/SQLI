import webview
import threading
import os
import signal
from app import app

def run_flask():
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        # Create and run the PyWebView window
        window = webview.create_window(
            title="SQL Injection Detection",
            url="http://127.0.0.1:5000",
            width=1024,
            height=768
        )
        webview.start(gui='edgechromium')
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Forcefully terminate the Flask server when GUI is closed
        os.kill(os.getpid(), signal.SIGTERM)

