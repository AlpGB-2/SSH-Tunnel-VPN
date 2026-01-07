import paramiko
import os
import subprocess
import time

# --- CONFIGURATION ---
HOME_IP = "192.168.1.75" # CHANGE THIS BEFORE SCHOOL
SSH_USER = "alpbayrak"
SSH_PASS = "9999"
LOCAL_PROXY_PORT = 9090
# ---------------------

def get_active_interfaces():
    """Returns a list of network services that are currently 'Hardware Port' active."""
    active_services = []
    try:
        # Get all network services
        output = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode()
        services = [s.strip() for s in output.split('\n') if s and "*" not in s]
        
        for service in services:
            # Check if the service has an IP address (meaning it's active)
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
        except Exception as e:
            print(f"[!] Failed to set proxy on {service}: {e}")

def start_tunnel():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    active_services = get_active_interfaces()
    if not active_services:
        print("[!] No active internet connection (WiFi or Ethernet) detected!")
        return

    try:
        print(f"Connecting to {HOME_IP}...")
        client.connect(HOME_IP, username=SSH_USER, password=SSH_PASS)
        
        # Apply proxy to all active interfaces (WiFi, Ethernet, etc.)
        set_proxy_state(active_services, True)
        
        print(f"[*] SUCCESS! Tunneled services: {', '.join(active_services)}")
        print("[*] Press Ctrl+C to stop and revert settings.")
        
        while True:
            if not client.get_transport().is_active():
                print("[!] Connection lost.")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Stopping...")
    except Exception as e:
        print(f"[!] Tunnel Error: {e}")
    finally:
        # Re-detect interfaces to ensure we clean up everything
        set_proxy_state(active_services, False)
        client.close()

if __name__ == "__main__":
    start_tunnel()
