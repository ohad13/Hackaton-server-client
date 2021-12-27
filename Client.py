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
MagicCookie = 0xabcddbca

def _is_data():
    if os.name != 'nt':
        return select.select([sys.stdin], [], [], 0)[0] != []
    else:
        return msvcrt.kbhit()


def look_for_server(i):
    if i==0:
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
            if cookie == MagicCookie and msg_type == 0x2:  # and port_number == 2018
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




if __name__ == "__main__":
        port = 0
        i=0
        while(port == 0):
            server_address = look_for_server(i)
            i+=1
            my_port = connect_to_server(server_address)
            time.sleep(0.1)