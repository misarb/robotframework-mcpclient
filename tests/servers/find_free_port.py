"""Prints one free TCP port to stdout. Used by the HTTP acceptance suite to
avoid colliding with other processes on a shared CI runner."""

import socket
import sys


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        print(sock.getsockname()[1])


if __name__ == "__main__":
    sys.exit(main())
