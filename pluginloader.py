import socket
import sys
import os
import argparse
import json
import inspect
import asyncio

server_address = "./plugin.sock"


# Starts the plugin server and listens on a unix socket.
def start_server():
    # Load the plugin
    from main import Plugin

    plugin = Plugin()

    # Make sure the socket does not already exist
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    # Bind the socket to the port
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        print("Waiting for client connection")
        connection, client_address = sock.accept()
        try:
            data = receive(connection)

            # Parse the JSON message
            print(f"Received message: {data}")
            message = json.loads(data)
            method = message["method"]
            argsv = message["args"]

            # Call the method and send back the response
            response = call(plugin, method, argsv)
            send(connection, response)
        finally:
            # Clean up the connection
            print("Closing connection")
            connection.close()


# Calls a method on the given plugin using the given args. Returns the
# return value as a JSON encoded string.
def call(plugin, method_name, argsv):
    try:
        method = getattr(plugin, method_name)
        # Call the method
        if inspect.iscoroutinefunction(method):
            ret = synchronize_async(method(*argsv))
        else:
            ret = method(*argsv)
    except Exception as e:
        return json.dumps(str(e))

    return json.dumps(ret)


# Starts the client and sends the given message to the server.
def start_client(message):
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    try:
        sock.connect(server_address)
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    try:
        # Send data
        send(sock, message)

        response = receive(sock)
        print(response)

    finally:
        sock.close()


# Recieves data over the given unix socket.
def receive(connection):
    data = ""
    expected = -1
    while True:
        data += connection.recv(16).decode("utf-8")
        # Get the data length from the first 16 bytes.
        if expected == -1:
            expected = int(data)
            data = ""
            continue
        if not data or len(data) == expected:
            break
    return data


# Sends the given message over the given unix socket.
def send(sock, message):
    length = len(message)
    length_str = f"{length:016d}"
    msg = f"{length_str}{message}"
    sock.sendall(str.encode(msg))


# Run async calls syncronously.
def synchronize_async(to_await):
    async_response = []

    async def run_and_capture_result():
        r = await to_await
        async_response.append(r)

    loop = asyncio.get_event_loop()
    coroutine = run_and_capture_result()
    loop.run_until_complete(coroutine)
    return async_response[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(
        help="sub-command help", dest="command"
    )
    parser_start = sub_parsers.add_parser(
        "start", help="starts the plugin server"
    )
    parser_send = sub_parsers.add_parser(
        "send", help="send a json command to plugin"
    )
    parser_send.add_argument("data", help="JSON string of data to send")
    args = parser.parse_args()

    if args.command == "start":
        start_server()
    if args.command == "send":
        start_client(args.data)
