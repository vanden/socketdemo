import datetime
import os
import queue
import socket
import sys

import config
import logger

# FixMe add docstrings


class Server:

    def __init__(self, host, port, msg_queue):

        try:
            # If port was sourced in an envar, it may come as a string
            # reprentation of an int
            port = int(port)
        except ValueError:
            # Not going to worry about possibility that we are passed a float
            print(' '.join(["port must be an int or convertible into one,",
                            "got %s" %(port,)]))
            sys.exit(1)

        self.host = host
        self.port = port
        self.msg_queue = msg_queue
        # self.socket will be set to a socket.socket by self._initialize_socket
        self.socket = None 
        
        try:
            # While there is a lot going on in the call-graph, here,
            # we are catching only KeyboardInterrupt, so the breadth
            # of the try suite is safe.
            self._run()
        except KeyboardInterrupt:
            self._shutdown_server()
            sys.exit(0)


    def _run(self):
        while True:
            # Outer loop keeps a socket available by recreating one
            # after a given client closes their connection to the
            # previously created socket.
            
            self._initialize_socket()
            conn, addr = self.socket.accept()

            while True:
                data = conn.recv(4096)
                time_stamp = datetime.datetime.now(datetime.timezone.utc)
                
                if not data:
                    # Note that this can occur either if the client
                    # explicitly sends an empty msg or if it is
                    # terminated with Ctrl-C. In principle, the client
                    # could be set up to send a sentinel msg on Ctrl-C
                    # so that we could discriminate the cases and
                    # produce distinct notifications; doesn't seem
                    # worth it.
                    print("Client sent empty data; closing the socket")
                    self._shutdown_server()
                    break
                
                decoded = data.decode()
                self.msg_queue.put((time_stamp, addr, decoded))
                print(decoded)
                
                # Echo data back to client
                conn.sendall(data)


    def _initialize_socket(self):
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = sock
        # In what follows, reference sock rather than self.socket for
        # namespace lookup efficiency.
        
        # Allow quick resuse of the address, ignoring the TIME_WAIT state.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind((self.host, self.port))
        except socket.gaierror:
            print("Could not resolve host %s" %(self.host,))
            sys.exit(1)
        except OSError as e:
            if e.errno == 49:
                # Covers cases like when self.host is www.ibm.com and thus
                # not under our control.
                print("Can't assign the requested address %s" %(self.host,))
                sys.exit(1)
            else:
                raise
        
        sock.listen()
        print("Server listening at %s on port %s" %(self.host, self.port))

        
    def _shutdown_server(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            if e.errno == 9:
                # OSError: [Errno 9] Bad file descriptor This seemed
                # to occur on a previous organization of the code in
                # some circumstances where sending an empty msg from
                # the client terminated the socket and then Ctrl-C was
                # used to interupt the server. (I'm not clear on the
                # details.) I don't understand why, but wrapping
                # self._run with the try/except to catch
                # KeyBoardInterupt appears to have resolved it.
                # Leaving it in as harmless and, should the code again
                # allow for a Bad file descriptor on calls to
                # self.socket.shutdown, this would still be the
                # desired behaviour as the BFD indicates there is no
                # socket to shutdown. However, slightly
                # nervous-making.
                pass
            elif e.errno == 57:
                # OSError: [Errno 57] Socket is not connected

                # This occurs if the client already shutdown the socket and is expected, so:
                pass
            else:
                # Unexpected OSError, so:
                raise

        # Leading newline to clear the terminal's '^C' on Ctrl-C
        print("\nServer shutting down")
        self.socket.close()



def _main():

    server_config = config.server_config

    # Try to set config params from envars; if missing, read values
    # from server_config. This lets envars over-ride the config file.
    port = os.getenv('PORT', server_config.getint('port'))
    host = os.getenv('HOST', server_config.get('host'))
    log_file_path = os.getenv('LOGFILEPATH', server_config.get('logfilepath'))

    if host == config.HOST:
        # HOST is the human friendly 'localhost'; replace with ip address
        # Was done in config.py, but that won't catch setting $HOST=localhost
        host = '127.0.0.1'

    msg_queue = queue.Queue(maxsize=0)
    log_worker = logger.LogWorker(msg_queue, log_file_path)

    # Initially thought I would have more threads. Ooops.
    pool = [log_worker]
    for thread in pool:
        thread.start()
    print("LogWorker thread started")

    s = Server(host, port, msg_queue)

    
if __name__ == '__main__':
    _main()
