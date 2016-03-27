import sys
import argparse
import socket
import whois

PORT = 34443
MAX_HOPS = 30
DEFAULT_WHOIS_PROVIDER = "whois.iana.org"
DEFAULT_WHOIS_PORT = 43
TYPE = 8
CODE = 0
CHECKSUM = 247, 248


def main(addr):
    ttl = 1
    icmp = socket.getprotobyname('icmp')
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    recv_sock.bind(("", PORT))
    # send_socket.bind(("", PORT))
    list_of_addr = []
    send_msg = bytearray([TYPE, CODE, CHECKSUM[0], CHECKSUM[1], 0, 1, 0, 6] + 64 * [0])
    try:
        while 1:
            recv_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            ttl += 1
            recv_sock.sendto(send_msg, (addr, PORT))
            current_addr = None
            try:
                recv_sock.settimeout(1)
                data, current_addr = recv_sock.recvfrom(1024)
            except socket.error:
                print(str(ttl - 1) + " Превышен интервал ожидания для запроса")
                pass
            if current_addr:
                current_addr = current_addr[0]
                if not (current_addr in list_of_addr):
                    print(str(ttl - 1) + " " + current_addr)
                    args_list = [current_addr, "whois.iana.org:43"]
                    whois.main(args_list)
                    list_of_addr.append(current_addr)

            if current_addr == addr:
                print("Трассировка завершена")
                break

            if ttl - 1 == MAX_HOPS:
                print("TTL == MAX_HOPS")
                sys.exit(1)

    except socket.error as e:
        print(e)
    finally:
        recv_sock.close()


def get_local_machine_ip():
    return socket.gethostbyname(socket.gethostname())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tracert by python")
    parser.add_argument("addrDest", nargs="?", default=socket.gethostbyname(socket.gethostname()),
                        help="address of destination")
    args = parser.parse_args()
    main(socket.gethostbyname(args.addrDest))