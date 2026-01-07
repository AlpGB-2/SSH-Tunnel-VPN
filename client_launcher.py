import tkinter as tk
from tkinter import scrolledtext, simpledialog
import threading
import requests
import os
import subprocess
import sys
import uuid
import runpy

# --- CONFIGURATION ---
GITHUB_URL = "https://raw.githubusercontent.com/AlpGB-2/SSH-Tunnel-VPN/main/bypass_payload.py"
# ---------------------

class VPNApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AlpVPN")
        self.root.geometry("550x450")
        self.process = None

        # UI Elements
        tk.Label(root, text="AlpVPN Pro", font=("Arial", 20, "bold")).pack(pady=10)
        self.status_label = tk.Label(root, text="Status: Disconnected", fg="red", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=65, height=15, font=("Courier", 11), bg="#1e1e1e", fg="#ffffff")
        self.log_area.pack(pady=10, padx=10)

        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=10)

        self.start_btn = tk.Button(self.btn_frame, text="Connect", command=self.start_vpn, width=15, height=2, bg="#2ecc71")
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = tk.Button(self.btn_frame, text="Stop", command=self.stop_vpn, state=tk.DISABLED, width=15, height=2)
        self.stop_btn.grid(row=0, column=1, padx=10)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_vpn(self):
        user_pass = simpledialog.askstring("Sudo Required", "Enter Mac Password:", show='*')
        if not user_pass: 
            return

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Connecting...", fg="orange")
        
        threading.Thread(target=self.run_payload, args=(user_pass,), daemon=True).start()

    def run_payload(self, password):
        # Save to home folder to ensure write permissions
        temp_file = os.path.join(os.path.expanduser("~"), "vpn_engine_headless.py")
        
        try:
            self.log("[*] Downloading latest engine...")
            r = requests.get(GITHUB_URL + f"?cb={uuid.uuid4().hex}", timeout=10)
            with open(temp_file, "w") as f:
                f.write(r.text)
            
            os.chmod(temp_file, 0o755)
            # Remove quarantine flags on macOS
            subprocess.run(["xattr", "-c", temp_file], stderr=subprocess.DEVNULL)
            
            env = os.environ.copy()
            env["VPN_PASS"] = password
            env["PYTHONUNBUFFERED"] = "1"

            self.log("[✓] Engine Ready. Launching tunnel...")

            # Use sys.executable (which is the .app in bundled mode) 
            # and pass the script path as an argument.
            self.process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )

            self.status_label.config(text="Status: Connected", fg="green")

            for line in self.process.stdout:
                self.log(line.strip())

        except Exception as e:
            self.log(f"[!!] Error: {e}")
            self.stop_vpn()

    def stop_vpn(self):
        if self.process:
            self.process.terminate()
            self.process = None
        
        self.status_label.config(text="Status: Disconnected", fg="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("[*] VPN Stopped.")

# --- THE FIX FOR BUNDLED APPS ---
if __name__ == "__main__":
    # In a bundled .app, sys.executable is the app itself.
    # When we launch the subprocess, we check if the argument is our script.
    if len(sys.argv) > 1 and "vpn_engine_headless.py" in sys.argv[1]:
        try:
            # Execute the script logic and exit immediately to prevent GUI launch
            runpy.run_path(sys.argv[1], run_name="__main__")
            sys.exit(0)
        except Exception as e:
            print(f"Engine Error: {e}")
            sys.exit(1)
    else:
        # Standard launch path
        root = tk.Tk()
        app = VPNApp(root)
        root.mainloop()