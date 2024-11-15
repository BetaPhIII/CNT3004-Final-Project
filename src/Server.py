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

def add(file, key, value):
     with open(file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([key, value])

def process_handler(client_socket, address):
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
        add("RESOURCES.csv", name, password)
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
            return
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


def find_csv(directory):
    # Loop through all the directories and files in the specified directory
    for file in os.listdir(directory):
            if file.endswith('.csv'):
                # Return the 