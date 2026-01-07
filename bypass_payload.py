import os
import subprocess
import time

# --- CONFIGURATION ---
HOME_IP = "192.168.1.75" 
SSH_USER = "alpbayrak"
LOCAL_PROXY_PORT = 9090
# ---------------------

def set_proxy(state, services):
    status = "on" if state else "off"
    for s in services:
        subprocess.run(["networksetup", "-setsocksfirewallproxy", s, "127.0.0.1", str(LOCAL_PROXY_PORT)])
        subprocess.run(["networksetup", "-setsocksfirewallproxystate", s, status])
        subprocess.run(["networksetup", "-setproxybypassdomains", s, "Empty"])

def start_tunnel():
    # 1. Get active interfaces
    output = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode()
    services = [s.strip() for s in output.split('\n') if s and "*" not in s and "is not set" not in subprocess.check_output(["networksetup", "-getinfo", s.strip()]).decode()]
    
    try:
        # 2. Turn on system proxy
        set_proxy(True, services)
        
        print(f"[*] Opening Tunnel to {HOME_IP}...")
        # -D 9090: Creates the SOCKS5 proxy on port 9090
        # -N: Do not execute a remote command (keep tunnel open)
        # -o ConnectTimeout=5: Don't hang forever if home is offline
        cmd = f"ssh -D {LOCAL_PROXY_PORT} -N {SSH_USER}@{HOME_IP}"
        
        print("[!] BE READY: Type your home Mac password in the terminal if asked.")
        os.system(cmd)
        
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        set_proxy(False, services)

if __name__ == "__main__":
    start_tunnel()
