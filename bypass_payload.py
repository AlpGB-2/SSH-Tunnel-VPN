import requests
import subprocess
import os
import time

# --- DYNAMIC CONFIG ---
# URL to the text file where your Home Mac reports its IP
IP_FILE_URL = "https://raw.githubusercontent.com/AlpGB-2/SSH-Tunnel-VPN/main/home_ip.txt"
SSH_USER = "alpbayrak"
LOCAL_PROXY_PORT = 9090

def get_latest_home_ip():
    try:
        # Pull the IP that your Home Mac just reported
        r = requests.get(IP_FILE_URL)
        return r.text.strip()
    except:
        print("[!] Could not fetch public IP, falling back to local.")
        return "192.168.1.75" # Fallback to local IP if fetch fails

def get_active_interfaces():
    """Identifies active network services (Wi-Fi, Ethernet, etc.)."""
    active_services = []
    try:
        output = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode()
        services = [s.strip() for s in output.split('\n') if s and "*" not in s]
        for service in services:
            info = subprocess.check_output(["networksetup", "-getinfo", service]).decode()
            if "IP address:" in info and "is not set" not in info:
                active_services.append(service)
    except Exception as e:
        print(f"[!] Error detecting interfaces: {e}")
    return active_services

def set_proxy_state(services, state):
    status = "on" if state else "off"
    for service in services:
        print(f"[*] Turning System SOCKS Proxy {status} for: {service}...")
        try:
            subprocess.run(["networksetup", "-setsocksfirewallproxy", service, "127.0.0.1", str(LOCAL_PROXY_PORT)])
            subprocess.run(["networksetup", "-setsocksfirewallproxystate", service, status])
            # Force all traffic (including DNS) through the proxy
            subprocess.run(["networksetup", "-setproxybypassdomains", service, "Empty"])
        except Exception as e:
            print(f"[!] Failed to set proxy on {service}: {e}")

def start_tunnel():
    home_ip = get_latest_home_ip()
    active_services = get_active_interfaces()
    
    if not active_services:
        print("[!] No active internet connection detected!")
        return

    try:
        # Apply proxy to all active interfaces
        set_proxy_state(active_services, True)
        
        print(f"[*] Opening Tunnel to {home_ip}...")
        # -D 9090: Creates local SOCKS5 proxy
        # -N: Keeps the pipe open without executing remote commands
        cmd = f"ssh -D {LOCAL_PROXY_PORT} -N {SSH_USER}@{home_ip}"
        
        print("[!] BE READY: Type your home Mac password if prompted.")
        os.system(cmd)
        
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    except Exception as e:
        print(f"[!] Tunnel Error: {e}")
    finally:
        # Cleanup: Turn proxy off so internet isn't broken
        set_proxy_state(active_services, False)

if __name__ == "__main__":
    start_tunnel()
