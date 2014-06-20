import json, socket, select

def send_list(connection, list_):
    bytes_string = bytes(json.dumps(list(list_)), "ascii")
    if len(bytes_string) > 4096:
        raise ValueError("List to send too long")
    while len(bytes_string) < 4096:
       bytes_string += b" "
    connection.send(bytes_string)

def recieve_list(connection):
    return json.loads(connection.recv(4096).decode("ascii").strip())

PORT = 13337  # The same port as used by the server
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = input("Enter the IP address you want to connect to! ")

try:
    connection.connect((host, PORT))
except Exception as e:
    print(e)
    print("Could not connect to host.")
    connection.close()
    print("Session closed!")

connection.setblocking(0)

while True:
    try:
        readable, writable, exceptional = select.select([connection], [], [], 0.05)
        if readable:
            try:
                data = recieve_list(connection)
            except ValueError:
                continue
            message = data[0]
            if message:
                print(message)
    except KeyboardInterrupt:
        try:
            command = input(": ")
            while True:
                readable, writable, exceptional = select.select([], [connection], [], 0.05)
                if writable:
                    send_list(connection, [command])
                    break
        except KeyboardInterrupt:
            pass
