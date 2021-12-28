import struct
import select
import socket
import time
import os
from scapy.arch import get_if_addr
import concurrent.futures
import itertools
import random
from concurrent.futures import ThreadPoolExecutor


MAGIC_COOKIE = 0xabcddcba
MESSAGE_TYPE = 0X2
VIRTUAL_NETWORK = 'eth1'
NUM_OF_TEAMS = 2
SERVER_TCP_PORT = 2075
TIME_LIMIT = 10
BROADCAST_PORT = 13117
BROADCAST_INTERVAL = 1




def Broadcast(time_limit=TIME_LIMIT, interval=BROADCAST_INTERVAL):
    # creat udp socket and send message in Brodcast_port (13117)
    i=0
    x = socket.gethostbyname(socket.gethostname()) #get ip
    ip = x if os.name == 'nt' else get_if_addr(VIRTUAL_NETWORK)
    print("Server started, listening on ip address", ip)
    start_time = time.time()
    # Open new udp socket
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # Set broadcasting mode
    udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Set a timeout
    udp_server.settimeout(0.3)

    brodcast_message = struct.pack('IBH', MAGIC_COOKIE, MESSAGE_TYPE, SERVER_TCP_PORT)
    while flag1: #time.time() - start_time < time_limit:
        try:
            i+=1
            
            print("brodcast send",i,flag1)
            udp_server.sendto(brodcast_message, (ip, BROADCAST_PORT))
        except Exception as e:
            print("Broadcasting error!", e)
            return False
        time.sleep(interval)
    print("end brodcast")    
    udp_server.close()
    return True


def listen_for_clients( time_limit=TIME_LIMIT):
    global flag1
    flag1 = True
    #Open server socket in SERVER_TCP_PORT and wait for client to connect 
    start_time = time.time()
    #Open server socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    serverSocket.setblocking(0)
    while True and time.time() - start_time < time_limit:
        try:
            serverSocket.bind(('', SERVER_TCP_PORT ))
            
            break
        except Exception as massage: 
            print('Bind error. Message:', massage)
            time.sleep(1)

    serverSocket.listen(5)
    socketsList = [serverSocket]
    teamIpNameDict = {}  # team_ip : team_name
    i = 0
    flag1 = True
    while socketsList and flag1: #and time.time() - start_time < time_limit:
        readable, writable, exceptional = select.select(socketsList, [], socketsList, 0) 
        for sock in readable:
            if sock is serverSocket:  
                connection, client_address = sock.accept() # connection 1 socket 
                connection.setblocking(0)
                socketsList.append(connection)
                teamIpNameDict[connection] = (None, client_address[0])

            else:  # The client should sent team's name
                data = sock.recv(1024) # Recive data from client 
                i += 1
                if i == 2:
                    flag1 = False
                if teamIpNameDict[sock][0] == None:
                    if data:
                        teamIpNameDict[sock] = (str(data, "utf-8")[0:-1], teamIpNameDict[sock][1]) #name
                    else:
                        socketsList.remove(sock) #if there is no data, remove and close socket
                        sock.close()
                else:
                    if data:
                        print("Unexpected data from client")

        for sock in exceptional:
            socketsList.remove(sock)
            sock.close()
        time.sleep(0.1)
    serverSocket.setblocking(1)

    return teamIpNameDict, socketsList, serverSocket

def randomQuestion():
    while True:
        x = random.randint(0,9)
        y = random.randint(0,9)

        allops = ['+','-','*']
        op = allops[random.randint(0,2)]
        z = 0
        if op == "+":
          z = x + y
          q = str(x) + "+" + str(y) + "?"
        if op == "-":
          z = max(x,y)-min(x,y)
          q = str(max(x,y)) + "-" + str(min(x,y)) + "?"
        if op == "*":
          z = x*y
          q = str(x) + "*" + str(y) + "?"

        if z > -1 and z < 10:
            tup = (q,z)
            return tup
    print("problem randomQuestion")        
    return

def game(teamIpNameDict, sockets, server, time_limit=TIME_LIMIT):
    print("start game")
    player1 = []
    player2 = []
    teamName1 = ""
    teamName2 = ""
    for index, player in enumerate(teamIpNameDict.values()):  # Split teams into groups
        if player != None:
            if index % 2 == 0:
                player1.append(player)
                teamName1 = player[0]
            else:
                player2.append(player)
                teamName2 = player[0]

    teams_dictionary = {}
    for player in player1 + player2:
        teams_dictionary[player[1]] = (player[0], 1 if player in player1 else 2)  # (team_name, group#)

    message = "Welcome to Quick Maths. \nPlayer 1:"

    for player in player1:
        message += player[0]+'\n'
    message += "Player 2:"
    for player in player2:
        message += player[0]+'\n=='
    message += "Please answer the following question as fast as you can:\nHow much is "

    tup = randomQuestion()
    qusestuin = tup[0]
    realAns = tup[1]
    message += qusestuin
    clinetAddresses = []  # Save clients' addresses to send end messages through
    for running_socket in sockets:
        try:
            if running_socket != server:
                running_socket.sendall(bytes(message, "utf-8"))
                running_socket.setblocking(1)
                clinetAddresses.append(running_socket.getpeername())
                running_socket.close()
        except Exception as e:
            print("Error while sending starting messages!", e)

    start_time = time.time()
    finalMessage=''
    listSockets = [server] 
    socket_ips = {}
    flag =False
    while listSockets and time.time() - start_time < time_limit and not flag :
        # try:
        readable, writable, exceptional = select.select(listSockets, [], listSockets, 0)
        for sock in readable:
            
            if sock is server:  
                connection, client_address = sock.accept()
                connection.setblocking(0)
                listSockets.append(connection)
                socket_ips[connection] = client_address[0]

            else:  # Client send answer
                data = sock.recv(1) # reading anser from client
                flag = True
                userAns = data.decode('utf-8')



                curP = teams_dictionary[socket_ips[connection]][0] 

                if curP == teamName1:
                    secP = teamName1
                else:
                    secP = teamName2
                try :
                    if int(userAns) == realAns: # check if right ans                        
                        finalMessage= whoWon(curP,userAns)
                        listSockets.remove(sock)
                        sock.close()
                        flag = True
                        break 
                    else:
                        finalMessage = whoWon(secP,userAns) 
                        listSockets.remove(sock)
                        sock.close()
                        flag = True
                        break
                except:
                    finalMessage = whoWon(secP,userAns) 
                    listSockets.remove(sock)
                    sock.close()
                    flag = True
                    break

        for sock in exceptional:
            listSockets.remove(sock)
            sock.close()
   
        # except Exception as e:
        #     print("Error while receiving keys!", e)
    #send the final message to all clinet

    for address in clinetAddresses:
        try:
            if finalMessage=='':
                finalMessage = "its a Draw!"
            running_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            running_socket.connect(address)
            running_socket.sendall(bytes(finalMessage, "utf-8"))  # TODO
            #open_socket.setblocking(1)
            running_socket.close()
        except Exception as e:
            print("Error while sending end messages!", e)
    # server.setblocking(1)
    server.close()
    flag1=True

    print("game end")

def whoWon(name,ans):
    msg = "\nGame over!\nThe correct answer was " + ans + "!\n"
    msg+= "Congratulations to the winner: " + name +"\n"
    #print(msg)
    return msg


if __name__ == "__main__":

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while 1:
            broadcast1 = executor.submit(Broadcast)
            teams_future = executor.submit(listen_for_clients)
            team_names, sockets, server = teams_future.result()
            if len(sockets)-1 >= NUM_OF_TEAMS:
                match = executor.submit(game(team_names, sockets, server))
                flag1=True
            else:
                i = 0 
                message = "Cant play alone"
                for open_socket in sockets:
                    open_socket.close()
                    print("close socket")
    executor.shutdown()

# if __name__ == "__main__":

#     executor = ThreadPoolExecutor(2)
#     while 1:
#         broadcast1 = executor.submit(Broadcast)
#         print("end brodcast")
#         teams_future = executor.submit(listen_for_clients)
#         team_names, sockets, server = teams_future.result()
#         if len(sockets)-1 >= NUM_OF_TEAMS:
#             match = executor.submit(game(team_names, sockets, server))
#         else:
#             i = 0 
#             message = "Cant play alone"
#             for open_socket in sockets:
#                 open_socket.close()
#                 print("close socket")
# executor.shutdown()