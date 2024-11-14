import socket
import tqdm
import os
import threading

def process_handler(client_socket, address):
    print(f"[+] {address} is connected.")

    # receive and parse file metadata
    received = b""
    while SEPARATOR.encode() not in received:
        # keep receiving until the SEPARATOR is found
        received += client_socket.recv(BUFFER_SIZE)

    try:
        # split only once at the first occurrence of SEPARATOR
        received = received.decode('utf-8', errors='ignore')
        filename, filesize = received.split(SEPARATOR, 1)
        filesize = int(filesize)
    except (UnicodeDecodeError, ValueError) as e:
        print(f"Error while decoding metadata: {e}")
        client_socket.close()
        return

    # remove absolute path if there is
    filename = os.path.basename(filename)

    # start receiving the file from the socket
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        bytes_received = 0  # track how much was already received
        while bytes_received < filesize:
            bytes_read = client_socket.recv(BUFFER_SIZE)
            if not bytes_read:
                # nothing is received, file transmission is done
                break
            f.write(bytes_read)
            bytes_received += len(bytes_read)
            progress.update(len(bytes_read))


    print(f"[+] Finished receiving {filename} from {address}")
    client_socket.close()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't need to connect, but it sets the correct address
        s.connect(("8.8.8.8", 80))  # Use Google's public DNS server to determine your network address
        ip = s.getsockname()[0]
    except Exception as e:
        ip = "127.0.0.1"  # Fallback to localhost in case of any error
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    # device's IP address
    SERVER_HOST = get_local_ip()
    SERVER_PORT = 5001
    # receive 4096 bytes each time
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"

    # create the server socket
    s = socket.socket()
    # bind the socket to our local address
    s.bind((SERVER_HOST, SERVER_PORT))
    # enabling the server to accept connections
    s.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

    # keep server running to accept multiple connections
    while True:
        client_socket, address = s.accept()
        # create a new thread for each client connection
        thread = threading.Thread(target=process_handler, args=(client_socket, address))
        thread.start()
