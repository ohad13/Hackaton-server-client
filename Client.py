import struct
import socket
import time
import sys
import select
import os

if os.name != 'nt':
    import tty
    import termios
else:
    import msvcrt

TEAM_NAME = b'team1\n'


def _is_data():
    if os.name != 'nt':
        return select.select([sys.stdin], [], [], 0)[0] != []
    else:
        return msvcrt.kbhit()


def look_for_server(i):
    if i == 0:
        print("Client started, listening for offer requests...")
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # Set broadcasting mode
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(('', 13117))

    while True:
        try:
            data, addr = client.recvfrom(10)
            # print(data, addr)
            cookie, msg_type, port_number = struct.unpack('IBH', data)
            if cookie == 0xfeedbeef and msg_type == 0x2:  # and port_number == 2018
                # print("received ", hex(cookie), hex(msg_type), port_number, "from", addr[0])
                print("Received offer from", addr[0], ", attempting to connect...")
                client.close()
                return addr[0], port_number
        except Exception as e:
            print("Error while listening for offers!", e)
        time.sleep(0.1)


def connect_to_server(server_address):
    # print(server_address)
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server_address)
        client_socket.send(TEAM_NAME)
        port = client_socket.getsockname()[1]
        message = str(client_socket.recv(1024), "utf-8")
        print(message)
        return port
    except Exception as e:
        print("Could not send team name! Trying to find a different server...", e)
        return 0


def play_with_server(server_address, my_port):
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listen_socket.bind(('', my_port))
    except Exception as e:
        print("Error trying to bind end message socket", e)
    listen_socket.listen(5)
    listen_socket.settimeout(1)
    inputs = [listen_socket]
    outputs = []
    stop = False
    while 1:
        try:
            readable, writable, exceptional = select.select(inputs, outputs, [], 0)  # todo: remove loop
            for s in readable:
                if s is listen_socket:  # Server is trying to connect and send end message
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    inputs.append(connection)
                    stop = True
                    inputs.remove(s)
                    s.close()

                else:  # The client should receive end message
                    data = s.recv(1024)
                    print(str(data, "utf-8"))
                    s.close()
                    print("Server disconnected, listening for offer requests...")
                    inputs.remove(s)
                    return

            if _is_data() and not stop:
                keys_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                keys_socket.connect(server_address)
                keys_socket.setblocking(0)
                c = sys.stdin.read(1) if os.name != 'nt' else msvcrt.getch().decode('utf-8')
                keys_socket.send(bytes(c, "utf-8"))
                keys_socket.close()

        except Exception as e:
            print("Error while trying to send characters!", e)

    for open_socket in inputs:
        open_socket.setblocking(1)
        open_socket.close()

if __name__ == "__main__":
    if os.name != 'nt':
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            port = 0
            while (port == 0):
                server_address = look_for_server()
                my_port = connect_to_server(server_address)
                play_with_server(server_address, my_port)
                time.sleep(0.1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    else:
        port = 0
        i = 0
        while (port == 0):
            server_address = look_for_server(i)
            i += 1
            my_port = connect_to_server(server_address)
            play_with_server(server_address, my_port)
            time.sleep(0.1)