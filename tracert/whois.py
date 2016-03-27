#!/usr/bin/python3
 
import argparse
from ipaddress import IPv4Address
from select import select
import socket
import re
 
DEFAULT_WHOIS_PORT = 43
DEFAULT_WHOIS_PROVIDER = "whois.iana.org"
SOCKET_CONNECT_TIMEOUT = 1
SOCKET_POLLING_PERIOD = 0.25
 
BUFFER_SIZE = 4 * 1024
 
 
def get_socket_address(address_string):
    chunks = address_string.split(':')
    return chunks[0], int(chunks[1]) if len(chunks) > 1 else DEFAULT_WHOIS_PORT
 
 
def recv_all(sock):
    result = b''
    while select([sock], [], [], SOCKET_POLLING_PERIOD)[0]:
        data = sock.recv(BUFFER_SIZE)
        if len(data) == 0:
            break
        result += data
    return result
 
 
def reg_exp(string, claim):
    pattern = re.compile(claim + '(.)+', re.IGNORECASE)
    return pattern.search(string)


def receive_information(target, socket_address):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(SOCKET_CONNECT_TIMEOUT)
        sock.connect(socket_address)
        sock.setblocking(0)
        result = recv_all(sock).decode('utf-8')
        sock.sendall((target + "\r\n").encode('utf-8'))
        temp_res = recv_all(sock).decode('utf-8')
        result += temp_res
        temp_res = recv_all(sock).decode('utf-8')
        result += temp_res
    return result


def print_inform(res, error_text):
    if res:
        print(res.group(0))
    else:
        print(error_text)


def main(args_list):
    try:
        socket_address = get_socket_address(args_list[1])
        target = str(IPv4Address(args_list[0]))
        temp_res = receive_information(target, (socket_address))
        res = reg_exp(temp_res, "whois\.")
        if res:
            provider = res.group(0).strip()
            source = "{}:{}".format(provider, DEFAULT_WHOIS_PORT)
            socket_address = get_socket_address(source)
            temp_res = receive_information(target, socket_address)
            res = reg_exp(temp_res, "NetName:")
            print_inform(res, "NetName is not found")
            res = reg_exp(temp_res, "country:")
            print_inform(res, "country is not defined")
            res = reg_exp(temp_res, "(origin:)|(AS\d+)")
            print_inform(res, "AS is not defined ")
        else:
            print("country is not defined. This IP has status RESERVE")
    except Exception as e:
        print(e)
        print("Failed to request info about '%s' from '%s'" % (args_list[0], args_list[1]))
