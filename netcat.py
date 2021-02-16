#-*- coding:utf-8 -*-
import sys
import socket
import getopt
import threading
import subprocess


listen = False
command = False
upload = ""
execute = ""
target = ""
upload_destination = ""
port = 0


def client_handler(client_socket):
    global upload
    global execute
    global command

    if len(upload_destination):
        #读取所有字符并写入
        file_buffer = ""   
        #持续读取
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data
        #接收数据并写入
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close

            #确认文件是否写入
            client_socket.send("Successfully saved file to %s\r\n"% upload_destination)

        except:
            client_socket.send("Failed to save file to %s\r\n"% upload_destination)

    #检查命令执行
    if len(execute):

        output= run_command(execute)
        client_socket.send(output)

    #如果需要命令行shell，进入另一个循环
    if command:
        while True:
            client_socket.send("<NC:#> ")
            #接收文件直到发现换行
            cmd_buffer = ""

            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
                response = run_command(cmd_buffer) #返回命令输出
                client_socket.send(response)     #返回数据

def server_loop():
    global target
    #如未定义，监听所有端口
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((target,port))

    server.listen(5)

    while True:
        client_socket,addr = server.accept()
        #处理新客户端
        client_thread = threading.Thread(target=client_handler,args=(client_socket,))
        client_thread.start()

def run_command(command):

    command = command.rstrip()

    try:
        output = subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)

    except:
        output = "File to execute command.\r\n"

    return output




def client_sender(buffer):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    

    try:
        #链接目标主机
        client.connect((target,port))

        if len(buffer):
            client.send(buffer)

        while True:

            #等待数据回传
            recv_len = 1
            response = ""

            while recv_len:
                data      = client.recv(4096)
                recv_len  = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response)

            buffer = raw_input("") #等待更多信息
            buffer += "\n"

            #发送
            client.send(buffer)
    except:

        print("[*] Exception! Exiting")

        client.close()


def usage():
    print("NET TOOLS")
    print
    print("Usage:netcat.py -t target_host -p port")
    print("-l --listen                       listen on [host]:[port] for incoming connections")

    print("-e --execute = file_to_run        execute the given file upon receiving a connection")

    print("-c --command                      initizlize a command shell")

    print("-u --upload = destination         upon receiving connection upload a file and write to [destination]")

    print
    print
    print("Examples:")
    print("netcat.py -t 192.168.0.1 -p 555 -l -c")
    print("netcat.py -l -p 555 -c")
    print("netcat.py -t 192.168.0.1 -p 555 -l -u=c:\\target.exe")
    print("netcat.py -t 192.168.0.1 -p 555 -l -e=\"cat /flag\"")
    print("echo 'ABCDEFGHI'|./netcat.py -t 192.168.11.12 -p 135")
    sys.exit(0)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    #读取命令行选项
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
    
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execute"):
            execute = a
        elif o in ("-c","--commandshell"):
            command = True
        elif o in ("-u","--uplaod"):
            upload_destination = a 
        elif o in ("-t","--target"):
            target = a 
        elif o in ("-p","port"):
            port = int(a)
        else:
            assert False,"netcat Option"
    
    #判断监听还是发送数据
    if not listen and len(target) and port > 0:
        #通过命令行读取内存数据
        buffer = sys.stdin.read()
        client_sender(buffer) #发送数据

    if listen:
        server_loop()

if __name__ == '__main__':
    main()
    