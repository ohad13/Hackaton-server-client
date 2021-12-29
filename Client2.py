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

TEAM_NAME = b'red team\n'
MAGIC_COOKIE = 0xabcddcba

def search_server(i):
    if i == 0:# only at first run print the "Client started.."
        print("Client started, listening for offer requests...")
    # create new socket udp
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # Set broadcasting mode
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(('', 13117))

    # try to recive new offer for a new game
    while True:
        try:
            data, addr = client.recvfrom(10) # recive the addrress of the server
            cookie, msg_type, port_number = struct.unpack('IbH', data)# 'open' the message
            if cookie == MAGIC_COOKIE and msg_type == 0x2:
                print("Received offer from", addr[0], ", attempting to connect...")
                client.close() # close udp socket
                return addr[0], port_number
        except Exception as e:
            print("Error occurred while listening for game offers..")
        time.sleep(0.1)

def connect_to_server(server_address):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # new tcp socket
        client_socket.connect(server_address) # connect to the server port
        client_socket.send(TEAM_NAME)         # send our name to the server
        port = client_socket.getsockname()[1]
        message = str(client_socket.recv(1024), "utf-8") # recive the message
        print(message) # welcome message
        return port
    except Exception as e:
        print("Error occurred while trying to send my name to the server. Trying to find a different server...")
        return 0

def client_game(server_address, my_port):
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # new tcp socket
    # try to bind to this port
    try:
        listen_socket.bind(('', my_port))
    except Exception as e:
        print("Error occurred while trying to bind.")
    listen_socket.listen(5)
    listen_socket.settimeout(1)
    socketList = [listen_socket]
    outputs = []
    flag = False
    while 1:
        try:
            readable, writable, exceptional = select.select(socketList, outputs, [], 0)
            for sock in readable:
                if sock is listen_socket:
                    connection, client_address = sock.accept()
                    connection.setblocking(0)
                    socketList.append(connection)
                    flag = True
                    socketList.remove(sock)
                    sock.close()

                else:  # The client should receive 'end message'
                    data = sock.recv(1024)
                    print(str(data, "utf-8"))
                    sock.close()
                    print("Server disconnected, listening for offer requests...")
                    socketList.remove(sock)
                    return
                    
            if currentOP() and not flag:
                keys_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                keys_socket.connect(server_address)
                keys_socket.setblocking(0)
                c = sys.stdin.read(1) if os.name != 'nt' else msvcrt.getch().decode('utf-8') # read from keyboard std
                keys_socket.send(bytes(c, "utf-8"))
                keys_socket.close()

        except Exception as e:
            print("Error occurred while trying to send messages.", e)
            break
        time.sleep(0.01)
    # close all open sockets
    for open_socket in socketList:
        open_socket.setblocking(1)
        open_socket.close()

def currentOP():
    if os.name != 'nt':
        return select.select([sys.stdin], [], [], 0)[0] != []
    else:
        return msvcrt.kbhit()

if __name__ == "__main__":
    if os.name != 'nt': #linux
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            port = 0
            i = 0
            while (port == 0):
                server_address = search_server(i)
                i += 1
                my_port = connect_to_server(server_address)
                if my_port == 0:
                    print("Server disconnected, listening for offer requests...")
                    continue
                client_game(server_address, my_port)
                time.sleep(0.1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    else: # windows
        port = 0
        i = 0
        while (port == 0):
            server_address = search_server(i)
            i += 1
            my_port = connect_to_server(server_address)
            if my_port == 0:
                print("Server disconnected, listening for offer requests...")
                continue
            client_game(server_address, my_port)
            time.sleep(0.1)