import socket
import tqdm
import os
import threading
import hashlib
import csv

HashTable = {}
def load_data_from_csv(file):
    if os.path.exists(file):
        with open(file, mode='r', newline='') as file:
            reader = csv.reader(file)
            # Skip the header if it exists
            for row in reader:
                if len(row) == 2:  # Ensure valid rows
                    key, value = row
                    HashTable[key] = value
        print("{:<8} {:<20}".format('USER','PASSWORD'))
        for k, v in HashTable.items():
            label, num = k,v
            print("{:<8} {:<20}".format(label, num))
        print("-------------------------------------------")
    else:
        try:
            open(file, mode='w', newline='')
        except Exception as e:
            print(e, "Error creating csv file")
    return HashTable
#to add credentials into csv file
def add(file, key, value):
     with open(file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([key, value])

def server_receive(client_socket, name):
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
    
    if os.path.isfile(filename):
        client_socket.send(f"{os.path.getsize(filename)}".encode())
        print(f"The file '{filename}' already exists in the current directory.")
        response = client_socket.recv(2048)
        response = response.decode()
        if response == "N":
            return
        elif response == "Y":
            print("Overwriting")
    else:
        client_socket.send("False".encode())
        print(f"The file '{filename}' does not exist in the current directory.")
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
    
def server_download(client_socket, filename, name):
    if not os.path.isfile(filename):
        client_socket.send("File not found".encode())
        return
    client_socket.send("File found".encode())

    filesize = os.path.getsize(filename)

    # send the file-name and file-size
    client_socket.send(f"{os.path.basename(filename)}{SEPARATOR}{filesize}".encode())

    # start sending the file


    
    progress = tqdm.tqdm(total=filesize, desc=f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            # we use sendall to assure transmission in busy networks
            client_socket.sendall(bytes_read)
            progress.update(len(bytes_read))  # Update progress

def server_delete(client_socket, filename, name):
    try:
        os.remove(filename)
        client_socket.send(f"0File '{filename}' has been deleted.".encode())
        print("Deletion requested from {name} successful.")
    except FileNotFoundError:
        client_socket.send(f"1File '{filename}' not found.".encode())
        print("Deletion requested from {name} unsuccessful.")
    except PermissionError:
        client_socket.send(f"2Permission denied: '{filename}'".encode())
        print("Permition denied for deletion request from {name}.")
    except Exception as e:
        client_socket.send(f"3Error occurred while deleting the file: {e}'".encode())
        print(f"Error: {e}, ocurred while servicing delete request from {name}.")

def print_dir(directory, prefix=""):
    dir = "\n"
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
        dir += f"{new_prefix}{d}\n"
        # Recursively print the subdirectory
        print_dir(os.path.join(directory, d), prefix + ("   " if is_last else " ┃ "))

    # Print files
    for idx, f in enumerate(files):
        is_last = idx == len(files) - 1
        file_prefix = prefix + (" ┗ " if is_last else " ┣ ")
        dir += f"{file_prefix}{f}\n"
    
    return dir

def login(s):
    client_socket.send(str.encode('ENTER USERNAME : ')) # Request Username
    name = client_socket.recv(2048)
    client_socket.send(str.encode('ENTER PASSWORD : ')) # Request Password
    password = client_socket.recv(2048)
    password = password.decode()
    name = name.decode()
    password=hashlib.sha256(str.encode(password)).hexdigest() # Password hash using SHA256
# REGISTERATION PHASE   
# If new user,  regiter in Hashtable Dictionary  
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
        
    else:
# If already existing user, check if the entered password is correct
        if(HashTable[name] == password):
            client_socket.send(str.encode('Connection Successful')) # Response Code for Connected Client 
            print('Connected : ',name)
        else:
            client_socket.send(str.encode('Login Failed')) # Response code for login failed
            print('Connection denied : ',name)
            client_socket.close()
            return 0
    print(f"[+] {cip}: {name} is connected.")
    return name


def process_handler(client_socket, address):
    name = login(client_socket)
    while name:
        operation = client_socket.recv(2048)
        operation = operation.decode()
        
        if operation == "send":
            server_receive(client_socket,name)
            print(f"[+] Finished receiving {filename} from {cip}: {name}")

        elif operation == "download" or operation == "delete" or operation == "dir":
            #getting directory of server
            root_directory = os.getcwd()  # Dynamically get the current working directory
            root_name = os.path.basename(root_directory) or root_directory
            dir = root_name
            dir += print_dir(root_directory)
            print(dir)
            #sending it to client to choose a file
            client_socket.send(str.encode(f'{dir}'))
            if operation == "download" or operation == "delete":
                #getting user choice
                filename = client_socket.recv(2048)
                filename = filename.decode()
                if operation == "download":
                    server_download(client_socket, filename, name)
                    print(f"[+] Finished sending {filename} to {cip}: {name}")
                else:
                    server_delete(client_socket, filename, name)

        elif operation == "subfolder":
            choice = client_socket.recv(2048)
            choice = choice.decode()
            while True:
                if choice == "create":
                    dir = client_socket.recv(2048)
                    dir = dir.decode()
                    os.mkdir(dir)
                    client_socket.send(str.encode(f'Successfully created directory {dir}'))
                    break
                elif choice == "delete":
                    dir = client_socket.recv(2048)
                    dir = dir.decode()
                    os.rmdir(dir)
                    client_socket.send(str.encode(f'Successfully removed directory {dir}'))
                    break

        elif operation == "exit":
            print(f"[+] {address[1]}: {name} disconnected.")
            client_socket.close()
            break
        

def find_csv(directory):
    # Loop through all the directories and files in the specified directory
    for file in os.listdir(directory):
            if file.endswith('.csv'):
                # Return the full path of the first .xml file found
                return os.path.join(directory, file)
    return None  # If no .xml file is found

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
    file = ".RESOURCES.csv"
    #load previous usernames and passwords
    load_data_from_csv(file)
    # device's IP address
    SERVER_HOST = get_local_ip()
    SERVER_PORT = 5001
    # receive 4096 bytes each time
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"

    # create the server socket
    #ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind the socket to our local address
    s.bind((SERVER_HOST, SERVER_PORT))
    # enabling the server to accept connections
    s.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

    # keep server running to accept multiple connections
    while True:
        client_socket, address = s.accept()
        global cip
        cip = address[1]
        # create a new thread for each client connection
        thread = threading.Thread(target=process_handler, args=(client_socket, address))
        thread.start()
