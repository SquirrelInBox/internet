from time import time, gmtime, strftime
from decimal import Decimal
from ipaddress import IPv4Address
import socket
import argparse
import threading
from struct import unpack, pack
import sys


NTP_HEADER_FORMAT = ">BBBBII4sQQQQ"
DEFAULT_PORT = 123


def from_ntp_short_bytes(value):
    return Decimal(value) / (2 ** 16)


def from_ntp_time_bytes(value):
    return Decimal(value) / (2 ** 32)


def utc_to_ntp_bytes(time):
    return int((Decimal(time) + 2208988800) * (2 ** 32))


def utc_to_string(value):
    return strftime("%a, %d %b %Y %H:%M:%S UTC", gmtime(value))


class Packet(object):
    def __init__(self, leap=0, version=4, mode=3, stratum=16, poll=0, precision=0, root_delay=0,
                 root_dispersion=0, ref_id=b'\x00' * 4, ref_time=0, origin=0, receive=0,
                 transmit=0):
        self.leap = leap
        self.version = version
        self.mode = mode
        self.options = (self.leap << 6) | (self.version << 3) | self.mode
        self.stratum = 10
        self.poll_binary = poll
        self.poll = 2 ** (-poll)
        self.precision_binary = precision
        self.precision = 2 ** (-precision)
        self.root_delay_binary = root_delay
        self.root_delay = from_ntp_short_bytes(root_delay)
        self.root_dispersion_binary = root_dispersion
        self.root_dispersion = from_ntp_short_bytes(root_dispersion)
        self.ref_id_binary = ref_id
        self.ref_id = str(IPv4Address(ref_id))
        self.ref_time_binary = ref_time
        self.ref_time = from_ntp_time_bytes(ref_time)
        self.origin_binary = origin
        self.origin = from_ntp_time_bytes(origin)
        self.receive_binary = receive
        self.receive = from_ntp_time_bytes(receive)
        self.transmit_binary = transmit
        self.transmit = from_ntp_time_bytes(transmit)

    @classmethod
    def from_binary(cls, data):
        options, stratum, poll, precision, root_delay, root_dispersion, \
        ref_id, ref_time, origin, receive, transmit \
            = unpack(">BBBBII4sQQQQ", data[:48])
        leap, version, mode = options >> 6, ((options >> 3) & 0x7), options & 0x7
        return Packet(leap, version, mode, stratum, poll, precision, root_delay, root_dispersion, ref_id,
                      ref_time,
                      origin, receive, transmit)

    def to_binary(self):
        return pack(NTP_HEADER_FORMAT,
                    self.options,
                    self.stratum,
                    self.poll_binary,
                    self.precision_binary,
                    self.root_delay_binary,
                    self.root_dispersion_binary,
                    self.ref_id_binary,
                    self.ref_time_binary,
                    self.origin_binary,
                    self.receive_binary,
                    self.transmit_binary)


def change_time(serv, data, addr, offset, current_time):
    try:
        packet = Packet.from_binary(data)
        send_packet = Packet(leap=0, version=4, mode=3, stratum=10, poll=3, precision=237, root_delay=32,
                             root_dispersion=1333,
                             ref_time=utc_to_ntp_bytes(Decimal(time()) - 10000 + offset),
                             ref_id=b'\xFA\x3D\xD8\xB4',
                             origin=packet.transmit_binary,
                             receive=utc_to_ntp_bytes(Decimal(current_time) + offset),
                             transmit=utc_to_ntp_bytes(Decimal(time() + offset)))
        serv.sendto(send_packet.to_binary(), addr)
    except ArithmeticError:
        print("Get incorrect data to create packet")
        sys.exit(1)


def start(offset):
    serv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        serv.bind(("", DEFAULT_PORT))
    except Exception:
        print("Can't take port")
        sys.exit(1)
    while True:
        data, addr = serv.recvfrom(1024)
        curr_time = time()
        thr = threading.Thread(target=change_time, args=[serv, data, addr, offset, curr_time])
        thr.start()
        thr.join()
    serv.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SNTP")
    parser.add_argument("offset", nargs="?", default=0, help="offset of time  in seconds")
    args = parser.parse_args()
    start(int(args.offset))