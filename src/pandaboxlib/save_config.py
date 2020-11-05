#!/usr/bin/env python2

# Script to save the state of the given Panda.

import socket


# Reads response lines from config socket.
class GetLines:
    def __init__(self, sock):
        self.sock = sock
        self.buf = ''
        self.lines = []

    def __iter__(self):
        return self

    def __read_lines(self, buf):
        while True:
            rx = self.sock.recv(65536).decode()
            if not rx:
                raise StopIteration
            buf += rx

            lines = buf.split('\n')
            if len(lines) > 1:
                break

        return lines[0], lines[1:-1], lines[-1]

    def next(self):
        if self.lines:
            line = self.lines[0]
            del self.lines[0]
        else:
            line, self.lines, self.buf = self.__read_lines(self.buf)
        return line


def read_response(input, command, sock):
    sock.sendall((command + '\n').encode())
    for line in input:
        if line[0] == '!':
            yield line[1:]
        elif line[0] == '.':
            break
        else:
            assert False, 'Malformed response: "%s"' % line


def save_state(input, output, command, sock):
    for line in read_response(input, command, sock):
        print >> output, line


def save_table(input, output, table, sock):
    assert table[-1] == '<'
    print >> output, table + 'B'
    for line in read_response(input, table[:-1] + '.B?', sock):
        print >> output, line
    print >> output


def save_metatable(input, output, table, sock):
    print >> output, table
    for line in read_response(input, table[:-1] + '?', sock):
        print >> output, line
    print >> output


def save_metadata(input, output, line, sock):
    if line[-1] == '<':
        save_metatable(input, output, line, sock)
    else:
        print >> output, line
