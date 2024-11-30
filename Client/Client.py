"""
Client for file operations: upload, download, delete, and directory management.
"""
import socket
import tqdm
import os
import Analysis
import time

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 4 #4KB
# Define restricted files
RESTRICTED_FILES = [".RESOURCES.csv", "Server.py", "Client.py"]

# Handles the creation or deletion of directories
def directory_op():
    
    # Prompts the user whether they want to create or delete a directory
    choice = input("Create or delete file (type \"create\" or \"delete\"): ").strip().lower()
    
    # Sends the choice to the server
    s.send(choice.encode())

    # Filter invalid input
    if choice != "create" or "delete":
        print("Invalid input...")
        return
        
    # Prompts the name of the directory that the user wants to create or delete
    dir_name = input("Directory name: ")

    # Sends the directory name to the server
    s.send(dir_name.encode())
    
    # Recieves and prints the response from the server
    response = s.recv(2048).decode()
    print(response)

# Handles uploading files to the server
def upload_file(filename, host):
    # Declare file path for uploading to subdirectories
    filepath = filename
    filename = os.path.basename(filename)
    # Kills the function if the filename does not exist
    if not os.path.isfile(filename):
        print(f"File '{filename}' not found.")
        return
    elif filename in RESTRICTED_FILES:
        print("Operation not permitted")
        return
    
    # Gets the size of the selected file
    filesize = os.path.getsize(filename)

    # Time when the upload starts
    t1 = time.perf_counter()

    # Send the file path  and file size to the server
    s.send(f"{filepath}{SEPARATOR}{filesize}".encode())

    # Gets the response from the server
    response = s.recv(2048).decode()

    # If the uploaded file is already in the server directory:
    if response.isdigit():
        
        print(f"File already exists in host: {host}. Would you like to overwrite the existing file? \n ")
        print(f"Client side: {filename}\t{os.path.getsize(filename)}\t\tServer side: {filename}\t{response}")
        
        # Prompts the user to overwrite the file
        choice = input("(Y/N)\n").lower().strip()
        s.send(choice.encode())
        # 'y' to overwrite the file, 'n' to kill the transfer
        if choice == "y":
            print("Overwriting file...")
        elif choice == "n":
            print("Cancelling operation...")
            return
        else:
            print("Did not quite catch that...")
    
    # Start sending file to the client
    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        while True:
            
            # Read bytes as they are sent
            bytes_read = f.read(BUFFER_SIZE)
            
            # If transmission is complete
            if not bytes_read:
                # File send has completed
                break
            
            # Verify transmission via sendall function
            s.sendall(bytes_read)
            
            # Update the progress bar
            progress.update(len(bytes_read))

    # Time when the upload ends
    t2 = time.perf_counter()
    
    # Calculates the elapsed time
    t = t2-t1

    # Adds upload to the analysis log
    Analysis.getData(filesize, t, 'uploaded')
    print(f"[+] File sent to {host}")

# Handles downloading files from the server
def download_file():

    # Recieving and prints the directory of the server
    response = s.recv(2048).decode()
    print(response)

    while True:

        # Prompts the user for the file to download
        filename = input("Enter the filename to download: ")

        # Normalize the filename
        base_filename = os.path.basename(filename)

        # Prevents the user from downloading the password file and the server sourcecode
        if base_filename in RESTRICTED_FILES:
            print("Operation not permitted")
            continue
        elif base_filename.endswith(".mp4"):
            print("Video file detected")
        elif base_filename.endswith(".mp3"):
            print("Audio file detected")
        elif base_filename.endswith(".txt"):
            print("Text file detected")
        break
    
    # Send the filename to the server
    s.send(f"{filename}".encode())

    # Time when the download begins
    t1 = time.perf_counter()

    # Recieves the response from the server
    response = s.recv(2048).decode()
    
    # If the file does not exist
    if(response == "File not found"):
        
        print(response)
        return
    

    received = b""
    while SEPARATOR.encode() not in received:
        # Keep receiving until the SEPARATOR is found
        received += s.recv(BUFFER_SIZE)

    try:
        # Split only once at the first occurrence of SEPARATOR
        received = received.decode('utf-8', errors='ignore')
        filename, filesize = received.split(SEPARATOR, 1)
        filesize = int(filesize)
    except (UnicodeDecodeError, ValueError) as e:
        print(f"Error while decoding metadata: {e}")
        s.close()
        return

    # Start receiving the file from the socket
    progress = tqdm.tqdm(total=filesize, desc = f"Receiving {base_filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(base_filename, "wb") as f:

        # Track how much was already received
        bytes_received = 0  

        # Loops until the entire file is recieved
        while bytes_received < filesize:
            
            # Recieves 4 KB of data
            bytes_read = s.recv(BUFFER_SIZE)
            
            if not bytes_read:
                
                # Nothing is received, file transmission is done
                break

            f.write(bytes_read)
            bytes_received += len(bytes_read)
            progress.update(len(bytes_read))

    # Time when the download ends
    t2 = time.perf_counter()

    # Calculates the elapsed time
    t = t2 - t1

    # Adds download to the analysis log
    Analysis.getData(filesize, t, 'downloaded')

def delete_file():

    # Recieving and prints the directory of the server
    response = s.recv(2048).decode()
    print(response)

    while True:

        # Prompts the user for the file they want to delete
        filename = input("Enter the filename to delete: ")

        # Normalize the filename
        base_filename = os.path.basename(filename)
        
        # Prevents the user from deleting the password file and server source code
        if base_filename in RESTRICTED_FILES:
            print("Operation not permitted")
            continue
        elif base_filename.endswith(".mp4"):
            print("Video file detected")
        elif base_filename.endswith(".mp3"):
            print("Audio file detected")
        elif base_filename.endswith(".txt"):
            print("Text file detected")
        break

    # Send the filename to the server
    s.send(filename.encode())

    # Recieves and prints the server response
    response = s.recv(2048).decode()
    print(response)

# Prints the server directory
def server_directory():
    
    # Recieves and prints the server directory
    response = s.recv(2048).decode()
    print(response)
    return response

# Prints the client directory
def print_dir(directory, prefix=""):

    # Lists and sorts all entries in the directory
    entries = [e for e in os.listdir(directory) if not e.startswith('.')]    
    entries.sort()

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

# Handles user authentication
def login(s):

    # Authentication section
    
    response = s.recv(2048) #ENTER USERNAME : 
    
    # Gets user name
    name = input(response.decode())	
    
    # Sends username to server
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
    return response

if __name__ == "__main__":
    host = input("What IP would you like to connect to? ")
    #ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)

    # Time when the socket is created
    socketTime1 = time.perf_counter()

    # Creates and connects to the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[+] Connecting to {host}:{5001}")
    s.connect((host, 5001))

    # Time when the socket is connected
    socketTime2 = time.perf_counter()

    # Calculates the elapsed time
    socketTime = socketTime2 - socketTime1

    # Gets the login response from the server
    response = login(s)

    # If the user had a valid login or registration
    if(response != 'Login Failed'):
        
        # Prints the login response
        print(response)
        print("Welcome!") if (response == 'Registeration Successful') else print("Welcome back!")
        print("[+] Connected.")
        
        # Adds the server response time to the analysis file
        Analysis.initializeData(socketTime)
        
        operation = ""
        while operation != "exit":
            
            # Prompts the user for the operation
            operation = input("Choose an operation (Upload, Download, Delete, Dir, Subfolder, Help, Exit): ").strip().lower()
            # Sends the operation to the server
            s.send(str.encode(operation))
            
            # Uploads a file
            if operation == "upload":
                root_directory = os.getcwd()  # Dynamically get the current working directory
                root_name = os.path.basename(root_directory) or root_directory
                print(root_name)
                print_dir(root_directory)
                fileName = input("Enter the file name to upload: ")
                if fileName.endswith(".mp4"):
                    print("Video file detected")
                elif fileName.endswith(".mp3"):
                    print("Audio file detected")
                elif fileName.endswith(".txt"):
                    print("Text file detected")
                upload_file(fileName, host)
            
            # Downloads a file
            elif operation == "download":
                download_file()
                print(f"[+] File received from {host}")
            
            # Deletes a file
            elif operation == "delete":
                delete_file()
            
            # Prints the server directory
            elif operation == "dir":
                server_directory()
            
            # Handles subfolder operations
            elif operation == "subfolder":
                directory_op()
            
            # Prints the commands
            elif operation == "help":
                print("Welcome to help!")
                print("Send: upload a file to the file sharing server.")
                print("Download: download a file from the server.")
                print("Delete: delete a file from the server.")
                print("Dir: view a list of files and subdirectories in the server's file storage path.")
                print("Subfolder: create folders or subfolders in the server's file storage path")
            
            # Exits the connection
            elif operation == "exit":
                s.close()

    # If the user did not have a valid login
    else:
        print(response, "\nConnection closed")
        s.close()