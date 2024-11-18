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
#ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"[+] Connecting to {host}:{5001}")
s.connect((host, 5001))
response = s.recv(2048)
name = input(response.decode())	
s.send(str.encode(name))
response = s.recv(2048)
# Input Password
password = input(response.decode())	
s.send(str.encode(password))
''' Response : Status of Connection :
    1 : Registeration successful 
    2 : Connection Successful
    3 : Login Failed
'''
# Receive response 
response = s.recv(2048)
response = response.decode()
if(response != 'Login Failed'):
    print(response)
    print("Welcome!") if (response == 'Registeration Successful') else print("Welcome back!")
    print("[+] Connected.")
    status = ""
    while status != "exit":
        operation = input("Type 'Send' to send a file to the server, \nType 'Download' to download a file from the server, \nor type 'Dir' to view directory operations.")
        s.send(operation)
        if operation == "Send":
            print(os.listdir())
            fileName = input("What file would you like to send? \n")
            if not os.path.isfile(fileName):
                print(f"File '{fileName}' not found.")
            else:
                send_file(fileName)
        elif operation == "Download":
<<<<<<< HEAD
            serverDir = s.recv()
            


        
        # elif operation == "Download":
        #         print()
        # elif operation == "Dir":
        #         dirOp = input("Type 'View' to see the server directory, \ntype 'Make' to make a new directory, \nor type 'Delete' to remove a file or directory.")
        #         s.send(dirOp)
        status = input("\nPress enter to continue or type 'exit' to exit.\n")
=======
            pass
        elif operation == "View":
            status = input("\nPress enter to continue or type 'exit' to exit.\n")
>>>>>>> 5a78264cec3f5e2584451686d09e30fe94b13ace
else:
    print(response, "\nConnection closed")
    s.close()