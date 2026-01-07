import paramiko
import threading
import select
import socketserver

# --- CONFIGURATION (Change these to your home info) ---
HOME_IP = "192.168.1.75" 
SSH_PORT = 22
SSH_USER = "alpbayrak"
SSH_PASS = "9999"
REMOTE_BIND_ADDRESS = "127.0.0.1"
REMOTE_PORT = 8080 # This is the port Spotify will use
# ------------------------------------------------------

def forward_handler(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        return

    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0: break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0: break
            sock.send(data)
    chan.close()
    sock.close()

def start_tunnel():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to home server at {HOME_IP}...")
    client.connect(HOME_IP, SSH_PORT, SSH_USER, SSH_PASS)
    
    # This creates a SOCKS proxy tunnel
    transport = client.get_transport()
    transport.request_port_forward('', REMOTE_PORT)
    
    print(f"Tunnel Open! Set your browser/Spotify proxy to localhost:{REMOTE_PORT}")
    
    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        thr = threading.Thread(target=forward_handler, args=(chan, 'localhost', 80))
        thr.setDaemon(True)
        thr.start()

if __name__ == "__main__":
    start_tunnel()
