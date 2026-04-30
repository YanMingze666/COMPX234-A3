import socket
import sys
import os

def main():
    if len(sys.argv) != 4:
        print("Usage: python tuple_space_client.py <server-hostname> <server-port> <input-file>")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])
    input_file_path = sys.argv[3]

    if not os.path.exists(input_file_path):
        print(f"Error: Input file '{input_file_path}' does not exist.")
        sys.exit(1)

    with open(input_file_path, 'r') as file:
        lines = file.readlines()

    # TASK 1: Create a TCP/IP socket and connect it to the server.
    # Hint: socket.socket(socket.AF_INET, socket.SOCK_STREAM) creates the socket.
    # Then call sock.connect((hostname, port)) to connect.

    # Create a TCP/IP socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Establish a connection to the server using the provided hostname and port
    sock.connect((hostname, port))


    try:
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ", 2)
            cmd = parts[0]
            message = ""

            # TASK 2: Build the protocol message string to send to the server.
            # Format:  "NNN X key"        for READ / GET
            #          "NNN P key value"   for PUT
            # where NNN is the total message length as a zero-padded 3-digit number,
            # X is "R" for READ and "G" for GET.
            # Hint: for READ/GET, size = 6 + len(key). For PUT, size = 7 + len(key) + len(value).
            # Reject lines with invalid format or key+" "+value > 970 chars.
                        # Validate command and format
            if len(parts) < 2:
                print(f"Error: Invalid command format: {line}")
                continue

            # Extract key and value (if present)
            key = parts[1]
            value = parts[2] if len(parts) > 2 else ""

            # Validate key length and total entry size
            if len(key) > 999 or (cmd == "P" and (len(value) > 999 or len(key + " " + value) > 970)):
                print(f"Error: Key or value too long: {line}")
                continue

            # Construct the message based on the command type
            if cmd in ["R", "G"]:
                # Format for READ/GET: "NNN X key"
                # Size calculation: 3 (size) + 1 (space) + 1 (op) + 1 (space) + len(key)
                msg_size = 6 + len(key)
                message = f"{msg_size:03d} {cmd} {key}"
            elif cmd == "P":
                # Format for PUT: "NNN P key value"
                # Size calculation: 3 (size) + 1 (space) + 1 (op) + 1 (space) + len(key) + 1 (space) + len(value)
                msg_size = 7 + len(key) + len(value)
                message = f"{msg_size:03d} {cmd} {key} {value}"
            else:
                print(f"Error: Unknown command: {cmd}")
                continue


            # TASK 3: Send the message to the server, then receive the response.
            # - Send:    sock.sendall(message.encode())
            # - Receive: first read 3 bytes to get the response size (like the server does).
            #            Then read the remaining (size - 3) bytes to get the response body.

            # Send the constructed message to the server
            sock.sendall(message.encode())

            # Receive the response from the server
            response_size_header = sock.recv(3)
            
            # Check if the connection is still alive
            if not response_size_header:
                raise socket.error("Connection closed by server")
            
            # Parse the total response size from the header
            response_size = int(response_size_header.decode())
            
            # Read the remaining response body
            response_buffer = sock.recv(response_size - 3)


            response = response_buffer.decode().strip()
            print(f"{line}: {response}")

    except (socket.error, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # TASK 4: Close the socket when done (already called for you — explain why
        # finally: is the right place to do this even if an error occurs above).
        sock.close()

if __name__ == "__main__":
    main()