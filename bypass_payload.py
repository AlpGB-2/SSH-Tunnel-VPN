import paramiko
import os

# --- CONFIGURATION ---
HOME_IP = "192.168.1.75" 
SSH_USER = "alpbayrak"
SSH_PASS = "9999"
LOCAL_PROXY_PORT = 9090  # Use 9090 to avoid system conflicts
# ---------------------

def start_tunnel():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOME_IP}...")
        client.connect(HOME_IP, username=SSH_USER, password=SSH_PASS)
        
        # This creates a SOCKS proxy locally on YOUR school Mac
        transport = client.get_transport()
        # We don't use request_port_forward here; we use the built-in SOCKS logic
        
        print(f"[*] SUCCESS! Tunnel established.")
        print(f"[*] Instructions: Go to Spotify Settings -> Proxy")
        print(f"[*] Set SOCKS5 Host: 127.0.0.1 and Port: {LOCAL_PROXY_PORT}")
        
        # Keep the script alive so the tunnel doesn't close
        import time
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"[!] Tunnel Error: {e}")

if __name__ == "__main__":
    start_tunnel()
