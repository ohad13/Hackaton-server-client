import struct
import socket
import time
import sys
import select
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if os.name != 'nt':
    import tty
    import termios
else:
    import msvcrt

TEAM_NAME = b'ohAdi\n'
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
            data, addr = client.recvfrom(8) # recive the addrress of the server
            cookie, msg_type, port_number = struct.unpack('IbH', data) # 'open' the message
            if cookie == MAGIC_COOKIE and msg_type == 0x2:
                print("Received offer from", addr[0], ", attempting to connect...")
                client.close() # close udp socket
                return addr[0], port_number
        except Exception as e:
            print(bcolors.FAIL+"Error occurred while listening for game offers.."+bcolors.ENDC,e)
        time.sleep(0.1)

def connect_to_server(server_address):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # new tcp socket
        client_socket.connect(server_address) # connect to the server port
        client_socket.send(TEAM_NAME)         # send our name to the server
        
        print("wait now for the game to begin...")

        #message = str(client_socket.recv(1024), "utf-8") # recive the message
        message = client_socket.recv(1024).decode()# recive the message
        print("message...")

        print(message) # welcome message

        port = client_socket.getsockname()[1]
        return [port,client_socket]

    except Exception as e:
        print(bcolors.FAIL+"Error occurred while trying to send my name to the server. Trying to find a different server..."+bcolors.ENDC,e)
        return [0]

def client_game(server_address, my_port,client_socket):
    listen_socket = client_socket #socket.socket(socket.AF_INET, socket.SOCK_STREAM) # new tcp socket
    #listen_socket.connect(server_address)

    # try to bind to this port
    # try:
    #     listen_socket.bind(('', my_port))
    # except Exception as e:
    #     print(listen_socket,my_port)
    #     print(bcolors.FAIL+"Error occurred while trying to bind."+bcolors.ENDC,e)
    # listen_socket.listen(5)
    # listen_socket.settimeout(1)

    c = sys.stdin.read(1) if os.name != 'nt' else msvcrt.getch().decode('utf-8') # read from keyboard std  
    listen_socket.send(bytes(c, "utf-8"))
    data = listen_socket.recv(2048)
    print(data.decode("utf-8"))
    # print(str(data, "utf-8"))


    # socketList = [listen_socket]
    # outputs = []
    # flag = False
    # print("in game")
    # while 1:
    #     try:
    #         readable, writable, exceptional = select.select(socketList, outputs, [], 0)
    #         for sock in readable:
    #             print("in for")
    #             if sock is listen_socket:
    #                 print("in if 1 after for")
    #                 connection, client_address = sock.accept()
    #                 connection.setblocking(0)
    #                 socketList.append(connection)
    #                 flag = True
    #                 socketList.remove(sock)
    #                 sock.close()

    #             else:  # The client should receive 'end message'
    #                 print("recive end message")
    #                 data = sock.recv(1024)
    #                 print(data.decode("utf-8"))
    #                 # print(str(data, "utf-8"))
    #                 sock.close()
    #                 print("Server disconnected, listening for offer requests...")
    #                 socketList.remove(sock)
    #                 return
    #         if currentOP() and not flag:
    #             keys_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #             keys_socket.connect(server_address)
    #             keys_socket.setblocking(0)
    #             c = sys.stdin.read(1) if os.name != 'nt' else msvcrt.getch().decode('utf-8') # read from keyboard std
                
    #             keys_socket.send(bytes(c, "utf-8"))
    #             print("success send the answer")
    #             keys_socket.close()
    #     except Exception as e:
    #         print(bcolors.FAIL+"Error occurred while trying to send messages."+bcolors.ENDC,e)
    #         break
    #     time.sleep(0.01)
    # close all open sockets
    # for open_socket in socketList:
    #     open_socket.setblocking(1)
    #     open_socket.close()

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
                x = connect_to_server(server_address)
                if len(x)>1:
                    my_port=x[0]
                    sock=x[1]
                else:
                    my_port=x[0]  
                if my_port == 0:
                    print(bcolors.FAIL+"Server disconnected, listening for offer requests..."+bcolors.ENDC)
                    continue
                client_game(server_address, my_port,sock)
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
                print(bcolors.FAIL+"Server disconnected, listening for offer requests..."+bcolors.ENDC)
                continue
            client_game(server_address, my_port)
            time.sleep(0.1)