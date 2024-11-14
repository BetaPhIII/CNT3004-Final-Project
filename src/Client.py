"""
Client that sends the file (uploads)
"""
import socket
import tqdm
import os

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 4 #4KB

def send_file(filename):
    # get the file size
    filesize = os.path.getsize(filename)
    # create the client socket


    # send the file-name and file-size
    s.send(f"{filename}{SEPARATOR}{filesize}".encode())

    # start sending the file
    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            # we use sendall to assure transmission in busy networks
            s.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))

    # close the socket
    s.close()

host = input("What IP would you like to connect to?")
s = socket.socket()
print(f"[+] Connecting to {host}:{5001}")
s.connect((host, 5001))
print("[+] Connected.")
status = ""
while status != "exit":
    fileName = input("What file would you like to send?")
    send_file(fileName)
    status = input("Press enter to continue or type 'exit' to exit")