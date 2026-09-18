import urllib.request
import json
import threading
import webbrowser
from tkinter import messagebox

APP_VERSION = "1.0.0"
# Using GitHub Releases API as the update server
# Assuming the user will host the code at their github profile
GITHUB_API_URL = "https://api.github.com/repos/fazanw/Multi-Reference-Downloader/releases/latest"
DOWNLOAD_URL = "https://github.com/fazanw/Multi-Reference-Downloader/releases/latest"

def check_for_updates(app_window):
    """
    Checks GitHub for a new release in a background thread.
    If a new version is found, prompts the user to update.
    """
    def _check():
        try:
            req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "").replace("v", "")
                    
                    if latest_version and _is_newer(APP_VERSION, latest_version):
                        app_window.after(1000, lambda: _prompt_update(latest_version))
        except Exception:
            # Silently ignore errors (e.g. no internet, or repo doesn't exist yet)
            pass

    def _is_newer(current, latest):
        try:
            curr_parts = [int(x) for x in current.split(".")]
            lat_parts = [int(x) for x in latest.split(".")]
            return lat_parts > curr_parts
        except Exception:
            return current != latest

    def _prompt_update(latest_version):
        msg = (f"A new version ({latest_version}) of Multi Reference Downloader is available!\n\n"
               f"You are currently running version {APP_VERSION}.\n\n"
               f"Would you like to download the update now?")
               
        if messagebox.askyesno("Update Available", msg):
            webbrowser.open(DOWNLOAD_URL)

    # Run check in background so it doesn't slow down app startup
    threading.Thread(target=_check, daemon=True).start()
