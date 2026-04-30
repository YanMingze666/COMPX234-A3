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

            parts = line.split(" ", 2)
            cmd = parts[0].upper()
            key = parts[1]
            value = parts[2] if len(parts) >= 3 else ""

            # length check
            total_length = len(key) + 1 + len(value)
            if total_length > 970 or len(key) > 999 or len(value) > 999:
                print(f"{line}: ERR Invalid size")
                continue

            # get the R G P
            message_b = ""
            if cmd == "READ":
                message_b = f"R {key}"
            elif cmd == "GET":
                message_b = f"G {key}"
            elif cmd == "PUT":
                message_b = f"P {key} {value}"
            else:
                print(f"{line}:  Unknown command")
                continue

            # calculate length and generate the pre-str
            msg_len = len(message_b)
            size_str = f"{msg_len:03d}"
            full_message = f"{msg_len:03d}" + message_b

            # TASK 3: Send the message to the server, then receive the response.
            # - Send:    sock.sendall(message.encode())
            # - Receive: first read 3 bytes to get the response size (like the server does).
            # Then read the remaining (size - 3) bytes to get the response body.
            # send message
            sock.sendall(full_message.encode())

            # read 3 len message

            response_size_header = sock.recv(3)
            if not response_size_header:
                raise socket.error("Connection closed by server")
            response_size = int(response_size_header.decode())


            response_buffer = b""
            while len(response_buffer) < response_size:
                chunk = sock.recv(response_size - len(response_buffer))
                if not chunk:
                    break
                response_buffer += chunk

            response = response_buffer.decode().strip()
            print(f"{line}: {response}")

    except (socket.error, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # TASK 4: Close the socket when done (already called for you — explain why
        # finally: is the right place to do this even if an error occurs above).

        # This ensures the socket is always properly closed, preventing resource leaks
        sock.close()

if __name__ == "__main__":
    main()