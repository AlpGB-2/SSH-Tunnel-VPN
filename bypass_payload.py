import os
import subprocess
import requests
import pexpect
import time
import sys

# --- CONFIGURATION ---
# The URL where your Home Mac reports its public IP
IP_FILE_URL = "https://raw.githubusercontent.com/AlpGB-2/SSH-Tunnel-VPN/main/home_ip.txt"
SSH_USER = "alpbayrak"
LOCAL_PROXY_PORT = 9090
# ---------------------

def get_latest_home_ip():
    """Fetches the current home IP from GitHub."""
    try:
        r = requests.get(IP_FILE_URL, timeout=5)
        return r.text.strip()
    except Exception as e:
        print(f"[!] Could not fetch IP from GitHub: {e}")
        return "192.168.1.75"  # Fallback to local if fetch fails

def get_active_services():
    """Finds all network services currently connected to the internet."""
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
    """Toggles the SOCKS proxy on or off for all active services."""
    status = "on" if state else "off"
    for service in services:
        print(f"[*] Turning SOCKS Proxy {status} for: {service}...")
        try:
            # Set the proxy address and port
            subprocess.run(["networksetup", "-setsocksfirewallproxy", service, "127.0.0.1", str(LOCAL_PROXY_PORT)])
            # Toggle the state
            subprocess.run(["networksetup", "-setsocksfirewallproxystate", service, status])
            # Clear bypass domains to ensure all traffic goes through the tunnel
            subprocess.run(["networksetup", "-setproxybypassdomains", service, "Empty"])
        except Exception as e:
            print(f"[!] Failed to adjust {service}: {e}")

def run_tunnel():
    home_ip = get_latest_home_ip()
    active_services = get_active_services()
    # Get the password passed from the GUI Launcher
    vpn_password = os.environ.get("VPN_PASS", "")

    if not active_services:
        print("[!] No active internet connection (Ethernet/Wi-Fi) found!")
        return

    try:
        # 1. Enable Proxy
        set_proxy_state(active_services, True)
        
        print(f"[*] Connecting to Home Mac at {home_ip}...")
        
        # 2. Start SSH Tunnel with Pexpect to handle password
        ssh_cmd = f"ssh -D {LOCAL_PROXY_PORT} -N {SSH_USER}@{home_ip} -o StrictHostKeyChecking=no"
        child = pexpect.spawn(ssh_cmd, encoding='utf-8')
        
        # Watch for the password prompt
        index = child.expect(['[Pp]assword:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        
        if index == 0:
            child.sendline(vpn_password)
            print("[✓] Password sent. Tunnel is now ACTIVE.")
            # Keep the process alive
            child.expect(pexpect.EOF)
        else:
            print("[!] SSH connection failed or timed out.")

    except KeyboardInterrupt:
        print("\n[*] User interrupted. Shutting down...")
    except Exception as e:
        print(f"[!!] Tunnel Error: {e}")
    finally:
        # 3. Cleanup: Always turn off proxy so internet isn't broken
        print("[*] Reverting network settings...")
        set_proxy_state(active_services, False)

if __name__ == "__main__":
    run_tunnel()
