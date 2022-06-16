#necessary libraries
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

# function to receive commands, run it and return it as a string
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
        
    # runs a command on the local operating system and then returns the output from that command
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)

    return output.decode()

class NetCat:
    #initialize the NetCat object
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer

        #we create the socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #set up listener method or send method
        def run(self):
            if self.args.listen:
                self.listen()
            else:
                self.send()

# listener method
def listen(self):
    # binds to the target and port
    self.socket.bind((self.args.target, self.args.port))
    self.socket.listen(5)
    # starts listening in a loop
    while True:
        client_socket, _ = self.socket.accept()
        # passing the connected socket to the handle method
        client_thread = threading.Thread(target=self.handle, args=(client_socket,))
        client_thread.start()

# send method
def send(self):
    self.socket.connect((self.args.target, self.args.port))
    # When connected, if we have a buffer, we send that to the target first
    if self.buffer:
        self.socket.send(self.buffer)  
        try:
            while True:
                recv_len = 1
                response = ''
                # loop to get data from target
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break 
                # if theres no data, break out of loop
                # else, we print the response data and pause to get interactive input, send that input, and continue the loop
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print('User terminated.')
            self.socket.close()
            sys.exit()

# handle method
def handle(self, client_socket):
    # executes the task corresponding to the commandline argument it receives:
    if self.args.execute:
        output = execute(self.args.execute)
        client_socket.send(output.encode())

    # We set up a loop to listen for content on the listening socket and receive data until there’s no more data coming in
    elif self.args.upload:
        file_buffer = b''
        while True:
            data = client_socket.recv(4096)
            if data:
                file_buffer += data
            else:
                break

        with open(self.args.upload, 'wb') as f:
            f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())

    # we set up a loop, send a prompt to the sender, and wait for acommand string to come back
    elif self.args.command:
        cmd_buffer = b''
        while True:
            try:
                client_socket.send(b'BHP: #> ')
                while '\n' not in cmd_buffer.decode():
                    cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                if response:
                    client_socket.send(response.encode())
                    cmd_buffer = b''
            except Exception as e:
                print(f'server killed {e}')
                self.socket.close()
                sys.exit()

# main block
if __name__ == '__main__':
    # Creates a com-mand line interface
    parser = argparse.ArgumentParser(
        # -- help menu to show how the program behaves
        description='Netcat Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
            netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
            netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
            netcat.py -t 192.168.1.108 -p 5555 # connect to server
        '''))
    parser.add_argument('-c', '--command', action='store_true', help='command shell') # interactive shell
    parser.add_argument('-e', '--execute', help='execute specified command') # executes command
    parser.add_argument('-l', '--listen', action='store_true', help='listen') # listener should be set up
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port') # port to communicate with
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP') # target ip
    parser.add_argument('-u', '--upload', help='upload file') # name of file to upload
    args = parser.parse_args()

    # if a listener is set up, we invoke the NetCat object with an empty buffer string
    if args.listen: 
        buffer = ''
    # else we we send the buffer content from stdin
    else:
        buffer = sys.stdin.read()

    # we start up out netcat listener
    nc = NetCat(args, buffer.encode())
    nc.run()      

