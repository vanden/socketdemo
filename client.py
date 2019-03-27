import socket
import sys

import config


class Client:

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.socket = None # Will be socket.socket set by self._get_socket

        self._run()


    def _run(self):
        self.socket = self._get_socket()
        while True:
            try:
                self._get_and_send_msg()
            except KeyboardInterrupt:
                # The expected Ctrl-C to terminate the client
                self._shutdown()


    def _get_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO Tune the timeout parameter; 1.0s seems a sane starting
        # value. The timeout is relevant if a host, such as, say,
        # www.google.fr (which won't respond on the selected port) is
        # used.
        sock.settimeout(1.0)

        address = (self.host, self.port)

        try:
            sock.connect(address)
        except socket.timeout:
            print("Connection to %s on %s timed out" %address)
            # Repetition of sys.exit(1) rankles. No easy way to avoid,
            # it seems. ThinkMe
            sys.exit(1)
        except ConnectionRefusedError:
            print("Connection to %s on %s refused" %address)
            sys.exit(1)
        except socket.gaierror:
            print("Could not resolve host %s" %(self.host,))
            sys.exit(1)

        print("Connected to %s on %s" %address)
        return sock


    def _get_and_send_msg(self):
        # Ideally, the input call would be in an infinite loop with a
        # short timeout (and break out when input given). As it is, if
        # the server shuts down, the client doesn't know about it
        # until after an input is given. Which isn't the right thing.
        # FixMe
        msg = input()

        if not msg:
            self._shutdown()
        else:
            self.socket.sendall(bytes(msg, 'utf-8'))
            data = self.socket.recv(4096)

            print("Received '%s' from server" %(data.decode()))


    def _shutdown(self):
        print("Closing socket and shutting down client")
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            if e.errno == 57:
                # This occurs if the server shut down the connection
                # and the client thereafter sends an empty string,
                # terminating causing _shutdown_client to be called.
                # (TODO: I don't understand why this does not happen
                # if the server shuts down the connection and then the
                # client is terminated with a Ctrl-C. That is worth
                # looking into.)
                pass
            else:
                # Then, we don't have the expected OSError and reraise
                raise
        self.socket.close()
        sys.exit(0)


if __name__ == '__main__':

    server_config = config.server_config
    host = server_config.get('host')
    port = server_config.getint('port')
    c = Client(host, port)
