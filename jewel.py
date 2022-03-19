#!/usr/bin/env python3

import socket
import sys
import select
import os
from file_reader import FileReader

try:
    import queue
except ImportError:
    import Queue as queue


class Jewel:

    # Note, this starter example of using the socket is very simple and
    # insufficient for implementing the project. You will have to modify this
    # code.
    def __init__(self, port, file_path, file_reader):
        self.file_path = file_path
        self.file_reader = file_reader

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", port))

        server.listen(5)
        print('Listening on port %s ...' % port)

        # Sockets from which we expect to read
        inputs = [server]

        # Sockets to which we expect to write
        outputs = []
        message_queues = {}

        # Reference: http://pymotw.com/2/select/
        while inputs:
            # select queue
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            # Handle inputs
            for s in readable:

                if s is server:
                    client, address = s.accept()
                    # A "readable" server socket is ready to accept a connection
                    sys.stdout.write('[CONN] Connection from {:} on port {:}\n'.format(address[0], address[1]))
                    inputs.append(client)

                    # Give the connection a queue for data we want to send
                    message_queues[client] = queue.Queue()
                else:
                    try:
                        data = s.recv(4096).decode()
                        if data:
                            # A readable client socket has data
                            message_queues[s].put(data)
                            # Add output channel for response
                            if s not in outputs:
                                outputs.append(s)
                        else:
                            # Interpret empty result as closed connection
                            # Stop listening for input on the connection
                            if s in outputs:
                                outputs.remove(s)
                            inputs.remove(s)
                            s.close()

                            # Remove message queue
                            del message_queues[s]
                    except ConnectionResetError:
                        sys.stdout.write('[ERRO] Connection Reset Error\n')
                        continue

            for c in writable:
                try:
                    next_msg = message_queues[c].get_nowait()
                except queue.Empty:
                    # No messages waiting so stop checking for writability.
                    outputs.remove(c)
                else:
                    self.send(next_msg, c, address)

            for s in exceptional:
                # Stop listening for input on the connection
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()

                # Remove message queue
                del message_queues[s]

        server.close()

    def send(self, data, client, address):
        header_end = data.find('\r\n\r\n')
        if header_end > -1:
            header_string = data[:header_end]
            lines = header_string.split('\r\n')
            request_fields = lines[0].split()
            if len(request_fields) != 3:
                self.badRequest(client)
                return
            path = file_path + request_fields[1]
            sys.stdout.write(
                '[REQU] [{:}:{:}] {:} request for {:}\n'.format(address[0], address[1], request_fields[0], path))
            if request_fields[0] == 'GET':
                response = self.file_reader.get(path)
                if response:
                    status = '{:} 200 OK\r\n'.format(request_fields[2])

                    client.sendall(status.encode())

                    length = "Server: sy4yeh\r\nContent-Length: {:}\r\n\r\n".format(self.file_reader.head(path))
                    client.sendall(length.encode())
                    try:
                        client.sendall(response)
                    except BrokenPipeError or OSError:
                        return
                else:
                    sys.stdout.write(
                        '[ERRO] [{:}:{:}] {:} request returned error {:}\n'.format(address[0], address[1],
                                                                                   request_fields[0], 404))

                    status = '{:} 404 NOT FOUND\r\n'.format(request_fields[2])
                    client.sendall(status.encode())
                    message = "Error 404: File not found"
                    length = "Server: sy4yeh\r\nContent-Length: {:}\r\n\r\n".format(len(message))
                    client.sendall(length.encode())
                    client.sendall(message.encode())


            elif request_fields[0] == 'HEAD':
                response = self.file_reader.head(path)
                if response:
                    message = '{:} 200 OK\r\n'.format(request_fields[2])
                    length = "Server: sy4yeh\r\nContent-Length: {:}\r\n\r\n".format(response)
                    response = message.encode() + length.encode()

                else:
                    sys.stdout.write(
                        '[ERRO] [{:}:{:}] {:} request returned error {:}\n'.format(address[0], address[1],
                                                                                   request_fields[0], 404))
                    status = '{:} 404 NOT FOUND\r\n'.format(request_fields[2])
                    client.sendall(status.encode())
                    response = b"Server: sy4yeh\r\nContent-Length: 0\r\n\r\n"
                client.sendall(response)

            else:
                sys.stdout.write('[ERRO] [{:}:{:}] {:} request returned error {:}\n'.format(address[0], address[1],
                                                                                            request_fields[0], 501))
                status = '{:} 501 Unsupported method (\'{:}\')\r\n'.format(request_fields[2], request_fields[0])
                client.sendall(status.encode())
                message = "Error 501: Unsupported method \'{:}\'".format(request_fields[0])
                length = "Server: sy4yeh\r\nContent-Length: {:}\r\n\r\n".format(len(message))
                client.sendall(length.encode())
                client.sendall(message.encode())
        else:
            self.badRequest(client)

    def badRequest(self, client):
        sys.stdout.write('[ERRO] {:} 400 Bad Request Error\n')
        status = '{:} 400 Bad Request Error\r\n'
        client.sendall(status.encode())
        message = '{:} 400 Bad Request Error\r\n'
        length = "Server: sy4yeh\r\nContent-Length: {:}\r\n\r\n".format(len(message))
        client.sendall(length.encode())
        client.sendall(message.encode())


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 46171))
    file_path = "./mywebsite/www"
    FR = FileReader()

    J = Jewel(port, file_path, FR)
