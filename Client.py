"""
Client that sends the file (uploads)
"""
import socket
import tqdm
import os
import Analysis
import time

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 4 #4KB

def create_directory():
    choice = input("Create or delete file (type \"create\" or \"delete\"):")
    s.send(f"{choice}".encode())
    dir_name = input("Directory name: ")
    s.send(f"{dir_name}".encode())
    response = s.recv(2048)
    response = response.decode()
    print(response)

def send_file(filename):
    if not os.path.isfile(filename):
        print(f"File '{filename}' not found.")
        return
    # get the file size
    filesize = os.path.getsize(filename)

    t1 = time.perf_counter()

    # send the file-name and file-size
    s.send(f"{filename}{SEPARATOR}{filesize}".encode())

    response = s.recv(2048)
    response = response.decode()

    if response.isdigit():
        print(f"File already exists in host: {host}. Would you like to overwrite the existing file? \n ")
        print(f"Client side: {filename}\t{os.path.getsize(filename)}\t\tServer side: {filename}\t{response}")
        choice = input("(Y/N)")
        if choice == "Y":
            print("Overwriting file...")
            s.send(choice.encode())
        elif choice == "N":
            s.send(choice.encode())
            return
        else:
            print("Did not quite catch that...")
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
    t2 = time.perf_counter()
    t = t2-t1

    Analysis.getSpeed(filesize, t)

    print(f"[+] File sent to {host}")

def download_file():
    #recieving the directory of the server
    response = s.recv(2048)
    response = response.decode()
    print(response)#printing it 

    while True:
        #prompting the user for the filename wanted
        filename = input("What file would you like to download? \n")
        if filename == ".RESOURCES.csv":
            print("Operation not permitted")
        else:
            break
    
    #telling the server the filename
    s.send(f"{filename}".encode())

    response = s.recv(2048)
    response = response.decode()
    if(response == "File not found"):
        print(response)
        return
    
    received = b""
    while SEPARATOR.encode() not in received:
        # keep receiving until the SEPARATOR is found
        received += s.recv(BUFFER_SIZE)

    try:
        # split only once at the first occurrence of SEPARATOR
        received = received.decode('utf-8', errors='ignore')
        filename, filesize = received.split(SEPARATOR, 1)
        filesize = int(filesize)
    except (UnicodeDecodeError, ValueError) as e:
        print(f"Error while decoding metadata: {e}")
        s.close()
        return

    # remove absolute path if there is
    filename = os.path.basename(filename)

    # start receiving the file from the socket
    progress = tqdm.tqdm(total=filesize, desc = f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        bytes_received = 0  # track how much was already received
        while bytes_received < filesize:
            bytes_read = s.recv(BUFFER_SIZE)
            if not bytes_read:
                # nothing is received, file transmission is done
                break
            f.write(bytes_read)
            bytes_received += len(bytes_read)
            progress.update(len(bytes_read))

    print(f"[+] File received from {host}")

def delete_file():
    #recieving the directory of the server
    response = s.recv(2048)
    response = response.decode()
    print(response)#printing it 

    #prompting the user for the filename wanted
    while True:
        filename = input("What file would you like to delete? \n")
        if filename == "Server.py" or filename == "../Client.py" or filename == ".RESOURCES.csv":
            print("Operation not permitted")
        else:
            break

    # if response.find(filename):

    #telling the server the filename
    s.send(f"{filename}".encode())

    response = s.recv(2048)
    response = response.decode()
    if(response[0] == "0"):
        print(response[1:])
    elif(response[0] == "1"):
        print(response[1:])
    elif(response[0] == "2"):
        print(response[1:])
    else:
        print(response[1:])
    #Types of responses
''' Response : Status of Connection :
    0 : File deleted
    1 : File not found
    2 : File is being processed
# '''

def server_directory():
    #recieving the directory of the server
    response = s.recv(2048)
    response = response.decode()
    print(response)#printing it 
    return response

def print_dir(directory, prefix=""):
    # List all entries in the directory
    entries = [e for e in os.listdir(directory) if not e.startswith('.')]    
    entries.sort()  # Sort entries for consistent output

    # Separate files and directories
    files = [f for f in entries if os.path.isfile(os.path.join(directory, f))]
    dirs = [d for d in entries if os.path.isdir(os.path.join(directory, d))]

    # Print directories first
    for idx, d in enumerate(dirs):
        # Check if it's the last directory
        is_last = idx == len(dirs) - 1 and not files
        new_prefix = prefix + (" ┗ " if is_last else " ┣ ")
        print(f"{new_prefix}{d}")
        # Recursively print the subdirectory
        print_dir(os.path.join(directory, d), prefix + ("   " if is_last else " ┃ "))

    # Print files
    for idx, f in enumerate(files):
        is_last = idx == len(files) - 1
        file_prefix = prefix + (" ┗ " if is_last else " ┣ ")
        print(f"{file_prefix}{f}")

    

host = input("What IP would you like to connect to?")
#ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"[+] Connecting to {host}:{5001}")
s.connect((host, 5001))

#Authentication section
response = s.recv(2048) #ENTER USERNAME : 
#Get user name
name = input(response.decode())	
#Send username to server
s.send(str.encode(name)) 
response = s.recv(2048)#ENTER PASSWORD :
# Input Password
password = input(response.decode())
#send password to server
s.send(str.encode(password))
#Types of responses
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
    operation = ""
    while operation != "exit":
        operation = input("Type 'Send' to send a file to the server, \nType 'Download' to download a file from the server, \nType 'Delete' to delete a file from the server, \nType 'Dir' to view directory operations, \nType 'Subfolder' to create or delete a directory in the server, \nType 'exit' to exit the program\n")
        s.send(str.encode(operation))
        if operation == "Send":
            root_directory = os.getcwd()  # Dynamically get the current working directory
            root_name = os.path.basename(root_directory) or root_directory
            print(root_name)
            print_dir(root_directory)
            fileName = input("What file would you like to send? \n")
            send_file(fileName)
        elif operation == "Download":
            download_file()
        elif operation == "Delete":
            delete_file()
        elif operation == "Dir":
            server_directory()
        elif operation == "Subfolder":
            create_directory()
        elif operation == "exit":
            s.send("exit".encode())
            
        # elif operation == "View":
        #     status = input("\nPress enter to continue or type 'exit' to exit.\n")

else:
    print(response, "\nConnection closed")
    s.close()