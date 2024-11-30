import socket
import tqdm
import os
import threading
import hashlib
import csv

HashTable = {}

# Loads login information from the csv
def load_data_from_csv(file):
    
    # If the filepath exists
    if os.path.exists(file):
        
        # Opens the file
        with open(file, mode='r', newline='') as file:
            
            reader = csv.reader(file)
            
            # Skip the header if it exists
            for row in reader:
                if len(row) == 2:  # Ensure valid rows
                    key, value = row
                    HashTable[key] = value
        
        # Prints the login information
        print("{:<8} {:<20}".format('USER','PASSWORD'))
        for k, v in HashTable.items():
            label, num = k,v
            print("{:<8} {:<20}".format(label, num))
        print("-------------------------------------------")
    
    # Handles errors in opening the file
    else:
        try:
            open(file, mode='w', newline='')
        except Exception as e:
            print(e, "Error creating csv file")
    return HashTable

# Adds new logins to the file
def add(file, key, value):
    
    # Opens the file
    with open(file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([key, value])

# Handles files being uploaded to the server
def server_receive(client_socket):
    
    # Receive and parse file metadata
    received = b""
    while SEPARATOR.encode() not in received:
        
        # Keep receiving until the SEPARATOR is found
        received += client_socket.recv(BUFFER_SIZE)

    try:
        
        # Split only once at the first occurrence of SEPARATOR
        received = received.decode('utf-8', errors='ignore')
        filename, filesize = received.split(SEPARATOR, 1)
        filesize = int(filesize)
    
    except (UnicodeDecodeError, ValueError) as e:
        
        print(f"Error while decoding metadata: {e}")
        client_socket.close()
        return
    
    # If the file already exists in the server directory
    if os.path.isfile(filename):
        
        client_socket.send(f"{os.path.getsize(filename)}".encode())
        print(f"The file '{filename}' already exists in the current directory.")
        response = client_socket.recv(2048)
        response = response.decode()
        
        # 'Y' to overwrite the file, 'N' to kill the transfer
        if response == "n":
            return
        elif response == "y":
            print("Overwriting")
        else:
            return
    else:
        client_socket.send("False".encode())
        print(f"The file '{filename}' does not exist in the current directory.")
    
    # Remove absolute path if there is
    filename = os.path.basename(filename)

    # Start receiving the file from the socket
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        
        # Track how much was already received
        bytes_received = 0  
        
        # Loops until the file is fully recieved
        while bytes_received < filesize:
            
            bytes_read = client_socket.recv(BUFFER_SIZE)
            if not bytes_read:
                # Nothing is received, file transmission is done
                break
            
            f.write(bytes_read)
            bytes_received += len(bytes_read)
            progress.update(len(bytes_read))

# Handles sending files to the client    
def server_send(client_socket, filename):
    
    # If the requested file is not in the server directory
    if not os.path.isfile(filename):
        client_socket.send("File not found".encode())
        return
    
    # Sends a response to the client
    client_socket.send("File found".encode())

    # Gets the file size
    filesize = os.path.getsize(filename)

    # Sends the file-name and file-size to the client
    client_socket.send(f"{os.path.basename(filename)}{SEPARATOR}{filesize}".encode())

    # Start sending the file to the client
    progress = tqdm.tqdm(total=filesize, desc=f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        
        while True:
            
            # Read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            
            if not bytes_read:
                # File transmitting is done
                break
            
            # We use sendall to assure transmission in busy networks
            client_socket.sendall(bytes_read)

            # Update progress bar
            progress.update(len(bytes_read))  

# Handles deleting files from the server
def server_delete(client_socket, filename, name):
    
    # Attempts to delete the file
    try:
        os.remove(filename)
        client_socket.send(f"File '{filename}' has been deleted sucessfully.".encode())
        print(f"Deletion requested from {name} successful.")
    
    # The file did not exist
    except FileNotFoundError:
        client_socket.send(f"File '{filename}' not found on server.".encode())
        print(f"Deletion requested from {name} unsuccessful.")
    
    # User does not have permission to delete the file
    except PermissionError:
        client_socket.send(f"Permission denied: '{filename}'".encode())
        print(f"Permition denied for deletion request from {name}.")
    
    # General error handling
    except Exception as e:
        client_socket.send(f"Error occurred while deleting the file: '{filename}'.\n {e}'".encode())
        print(f"Error: {e}, ocurred while servicing delete request from {name}.")

# Prints the server directory
def print_dir(directory, prefix=""):
    
    dir = ""
    
    # Lists and sorts all entries in the directory
    entries = [e for e in os.listdir(directory) if not e.startswith('.')]    
    entries.sort()

    # Separates files and directories
    files = [f for f in entries if os.path.isfile(os.path.join(directory, f))]
    dirs = [d for d in entries if os.path.isdir(os.path.join(directory, d))]

    # Prints directories first
    for idx, d in enumerate(dirs):
        
        # Check if it's the last directory
        is_last = idx == len(dirs) - 1 and not files
        new_prefix = prefix + (" ┗ " if is_last else " ┣ ")
        dir += f"{new_prefix}{d}\n"
        
        # Recursively print the subdirectory
        dir += print_dir(os.path.join(directory, d), prefix + ("   " if is_last else " ┃ "))

    # Print files
    for idx, f in enumerate(files):
        is_last = idx == len(files) - 1
        file_prefix = prefix + (" ┗ " if is_last else " ┣ ")
        dir += f"{file_prefix}{f}\n"
    # returns the directory
    return dir

# Handles user authorization
def login(s):

    # Request Username
    client_socket.send(str.encode('ENTER USERNAME : ')) 
    name = client_socket.recv(2048)
    
    # Request Password
    client_socket.send(str.encode('ENTER PASSWORD : ')) 
    password = client_socket.recv(2048)
    password = password.decode()
    name = name.decode()

    # Password hash using SHA256
    password=hashlib.sha256(str.encode(password)).hexdigest() 

    # REGISTERATION PHASE   
    # If new user, regiter in Hashtable Dictionary  
    if name not in HashTable:
        HashTable[name] = password
        add(".RESOURCES.csv", name, password)
        client_socket.send(str.encode('Registeration Successful')) 
        print('Registered : ',name)
        print("{:<8} {:<20}".format('USER','PASSWORD'))
        for k, v in HashTable.items():
            label, num = k,v
            print("{:<8} {:<20}".format(label, num))
        print("-------------------------------------------")

    # If already existing user, check if the entered password is correct        
    else:

        if(HashTable[name] == password):
            # Response Code for Connected Client 
            client_socket.send(str.encode('Connection Successful')) 
            print('Connected : ',name)
        else:
            # Response code for login failed
            client_socket.send(str.encode('Login Failed')) 
            print('Connection denied : ',name)
            client_socket.close()
            return 0
    
    print(f"[+] {cip}: {name} is connected.")
    return name

# Handles which server operation should be occuring
def process_handler(client_socket, address):
    name = login(client_socket)
    while name:
        
        # Recieves the operation from the client
        operation = client_socket.recv(2048)
        operation = operation.decode()
        
        # Handles the client sending files to the server
        if operation == "upload":
            server_receive(client_socket)
            print(f"[+] Finished receiving file from {cip}: {name}")

        # Handles sending files to the client, deleting files, and printing the server directory
        elif operation == "download" or operation == "delete" or operation == "dir":
            
            # Gets server directory
            root_directory = os.getcwd()
            root_name = os.path.basename(root_directory) or root_directory
            dir = root_name + "\n"
            dir += print_dir(root_directory)
            #sending it to client to choose a file
            client_socket.send(str.encode(f'{dir}'))
            if operation == "download" or operation == "delete":
                
                # Getting user choice
                filename = client_socket.recv(2048)
                filename = filename.decode()
                
                # Handles sending files to the client
                if operation == "download":
                    server_send(client_socket, filename)
                    print(f"[+] Finished sending {filename} to {cip}: {name}")
                
                # Handles deleting files from the server
                else:
                    server_delete(client_socket, filename, name)

        # Handles creating and deleting subfolders
        elif operation == "subfolder":
            choice = client_socket.recv(2048)
            choice = choice.decode()
            while True:
                
                # Handles creating subfolders
                if choice == "create":
                    dir = client_socket.recv(2048)
                    dir = dir.decode()
                    os.mkdir(dir)
                    client_socket.send(str.encode(f'Successfully created directory {dir}'))
                    break

                # Handles deleting subfolders
                elif choice == "delete":
                    dir = client_socket.recv(2048)
                    dir = dir.decode()
                    os.rmdir(dir)
                    client_socket.send(str.encode(f'Successfully removed directory {dir}'))
                    break
        
        # Exits the connection and closes the socket
        elif operation == "exit":
            print(f"[+] {address[1]}: {name} disconnected.")
            client_socket.close()
            break
        
# Gets the ip address of the host computer
def get_local_ip():
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        
        # This doesn't need to connect, but it sets the correct address
        # Use Google's public DNS server to determine your network address
        s.connect(("8.8.8.8", 80))  
        ip = s.getsockname()[0]
    
    except Exception as e:
        
        # Fallback to localhost in case of any error
        ip = "127.0.0.1"  
    
    finally:
        
        # Closes the test socket
        s.close()
    
    return ip

if __name__ == "__main__":
    
    file = ".RESOURCES.csv"
    
    # Load previous usernames and passwords
    load_data_from_csv(file)
    
    # Device's IP address
    SERVER_HOST = get_local_ip()
    SERVER_PORT = 5001
    
    # receive 4 KB each time
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"

    # Create the server socket
    # ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to our local address
    s.bind((SERVER_HOST, SERVER_PORT))
    
    # Enabling the server to accept connections
    s.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

    # Keep server running to accept multiple connections
    while True:
        
        client_socket, address = s.accept()
        global cip
        cip = address[1]
        
        # Create a new thread for each client connection
        thread = threading.Thread(target=process_handler, args=(client_socket, address))
        thread.start()
