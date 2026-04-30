import socket
import sys
import threading
import time

# using a lock -- see https://realpython.com/python-thread-lock/
# sockets -- see https://realpython.com/python-sockets/#python-socket-api-overview

# Shared data structures
tuple_space = {}
total_clients = 0
total_operations = 0
read_count = 0
get_count = 0
put_count = 0
error_count = 0
lock = threading.Lock()

def receive_n(sock, num_bytes):
    """Read exactly num_bytes from the socket."""
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:  # Connection closed or error
            break
        data += chunk
    return data


def increment_stat(stat_name):
    global total_clients, total_operations, read_count, get_count, put_count, error_count
    if stat_name == "total_clients":
        total_clients += 1
    elif stat_name == "total_operations":
        total_operations += 1
    elif stat_name == "read_count":
        read_count += 1
    elif stat_name == "get_count":
        get_count += 1
    elif stat_name == "put_count":
        put_count += 1
    elif stat_name == "error_count":
        error_count += 1

def print_stats():
    while True:
        time.sleep(10)
        with lock:
            tuple_count = len(tuple_space)
            avg_key_size = avg_value_size = avg_tuple_size = 0
            if tuple_count > 0:
                total_key_size = sum(len(k) for k in tuple_space.keys())
                total_value_size = sum(len(v) for v in tuple_space.values())
                avg_key_size = total_key_size / tuple_count
                avg_value_size = total_value_size / tuple_count
                avg_tuple_size = avg_key_size + avg_value_size
            print("\n--- Tuple Space Stats ---")
            print(f"Tuples: {tuple_count}")
            print(f"Avg Tuple Size: {avg_tuple_size:.2f}")
            print(f"Avg Key Size: {avg_key_size:.2f}")
            print(f"Avg Value Size: {avg_value_size:.2f}")
            print(f"Clients: {total_clients}")
            print(f"Operations: {total_operations}")
            print(f"READs: {read_count}")
            print(f"GETs: {get_count}")
            print(f"PUTs: {put_count}")
            print(f"Errors: {error_count}\n")

def handle_client(client_socket):
    global tuple_space

    increment_stat("total_clients")
    try:
        while True:
            # TASK 1: Read the first 3 bytes to get the message size, then read
            # the remaining (size - 3) bytes and decode to a string.
            # Hint: use receive_n(). If nothing arrives, client disconnected — break.
            
            # 1. Read the 3-byte message size header
            size_header = receive_n(client_socket, 3)
            
            # Check if the connection is still alive
            # An empty return value indicates the client disconnected
            if not size_header:
                break

            # 2. Parse the total message size from the header
            msg_size = int(size_header.decode('utf-8'))

            # 3. Read the rest of the message payload
            message_buffer = receive_n(client_socket, msg_size - 3).decode('utf-8')

            # Handle the request
            response = handle_request(message_buffer)

            # TASK 2: Build the response string with its size prepended (3 digits + space),
            # then send it. Hint: total size = len(response) + 4. Use sendall().
            
            # 1. Calculate the total size of the response packet
            total_size = len(response) + 4

            # 2. Format the response header with leading zeros (e.g., "015")
            response_with_size = f"{total_size:03d} {response}".encode('utf-8')

            # 3. Send the complete packet to the client
            client_socket.sendall(response_with_size)

    except (socket.error, ValueError):
        pass
    finally:
        client_socket.close()

def handle_request(message):
    global tuple_space
    increment_stat("total_operations")
    if len(message) < 3:
        increment_stat("error_count")
        return "ERR Invalid message"

    # split(" ", 2) keeps values with spaces intact in parts[2]
    parts = message.split(" ", 2)
    if len(parts) < 2:
        increment_stat("error_count")
        return "ERR Invalid message"

    op = parts[0]
    key = parts[1]
    if len(key) > 999:
        increment_stat("error_count")
        return "ERR Key too long"

    with lock:
        if op == "R":
            # TASK 3: READ — look up key in tuple_space.
            # Return "OK (<key>, <value>) read" or "ERR <key> does not exist".
            
            increment_stat("read_count")

            # Check if the key exists in the shared dictionary
            if key in tuple_space:
                # Retrieve the value associated with the key
                value = tuple_space[key]
                # Return success message with the key-value pair
                return f"OK ({key}, {value}) read"
            else:
                # Return error message if the key is not found
                return f"ERR {key} does not exist"



        elif op == "G":
            # TASK 4: GET — remove key from tuple_space and return its value.
            # Return "OK (<key>, <value>) removed" or "ERR <key> does not exist".
            # Hint: dict.pop(key, None) removes and returns the value, or None if missing.
            increment_stat("get_count")

            # Attempt to remove the key and retrieve its value
            # dict.pop returns None if the key does not exist
            value = tuple_space.pop(key, None)
            
            if value is not None:
                # Return success message confirming removal
                return f"OK ({key}, {value}) removed"
            else:
                # Return error message if the key was not found
                return f"ERR {key} does not exist"


        elif op == "P":
            if len(parts) < 3:
                increment_stat("error_count")
                return "ERR Invalid PUT"
            value = parts[2]
            # TASK 5: PUT — add (key, value) only if key does not already exist.
            # Validate: len(value) <= 999 and len(key + " " + value) <= 970.
            # Return "OK (<key>, <value>) added" or "ERR <key> already exists".
            increment_stat("put_count")

            # Check if the key already exists to prevent overwriting
            if key in tuple_space:
                return f"ERR {key} already exists"

            # Validate the length of the value and the total entry size
            # This ensures the tuple space entry fits within protocol limits
            if len(value) > 999 or len(key + " " + value) > 970:
                increment_stat("error_count")
                return "ERR Value too long"

            # Add the new key-value pair to the shared dictionary
            tuple_space[key] = value
            # Return success message confirming the addition
            return f"OK ({key}, {value}) added"


        else:
            increment_stat("error_count")
            return "ERR Unknown operation"


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 TupleSpaceServer.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", port))
    server_socket.listen(5)
    print(f"Server started on port {port}")

    # Start the stats printing thread (daemon=True means it stops when main exits)
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()

    try:
        while True:
            # Wait for a client to connect, then spawn a new thread for it
            (client_socket, address) = server_socket.accept()
            print(f"Connection from {address} accepted.")
            print(f"Create a new thread that will deal with the client which just connected.")
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()