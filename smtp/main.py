import argparse
import datetime
import getpass
import os
import random
import socket
import base64
import ssl
import sys
 
DEFAULT_SENDER = "seti2seti"
DEFAULT_SUBJECT = "Images"
DEFAULT_PORT = 465
ADDITIONAL_PORT = 25
IMAGE_EXPANSION = ['gif', 'pjpeg', 'png', 'jpeg', 'bmp']
SEPARATOR = bytes("".join([str(random.randint(0, 9)) for i in range(15)]), encoding="utf-8")


def conn(sock, serv_addr, port):
    sock.settimeout(4)
    sock.connect((serv_addr, port))
    answer = sock.recv(1024)
    print(answer)
    return sock


def connect(ssl_sock, sock, serv_addr, ssl_port, port):
    try:
        return conn(ssl_sock, serv_addr, ssl_port)
    except socket.error:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return conn(sock, serv_addr, port)
        except socket.error:
            sys.stderr.write("Failed connect to server")
            sys.exit(1)
    except UnicodeError:
        sys.stderr.write("Problem with codec")
        sys.exit(1)
 
 
def change_data(sock, b_msg):
    send_data(sock, b_msg)
    return get_data(sock)
 
 
def get_data(sock):
    answer = b""
    while True:
        for timeout in range(3, 6):
            try:
                sock.settimeout(timeout)
                temp_answer = sock.recv(1024)
                if str(temp_answer)[2] == str(5):
                    print(str(temp_answer)[5:-1])
                    sys.exit(1)
                answer += temp_answer
                if answer and not temp_answer:
                    return answer
            except socket.error:
                if answer:
                    return answer
                pass
    if not answer:
        sys.stderr.write("Failed get some data")
        sys.exit(1)
    return answer
 
 
def send_data(sock, b_msg):
    sock.send(b_msg)
 
 
def auth(sock, login, password):
    auther = change_data(sock, b"auth login\r\n")
    print(auther)
    login = change_data(sock, base64.b64encode(login) + b'\r\n')
    print(login)
    pass_ = change_data(sock, base64.b64encode(password) + b'\r\n')
    print(pass_)

 
def header(sock, login, passwd, b_mail_from, b_mail_to):
    ehlo_answer = change_data(sock, b"EHLO I\r\n")
    print(ehlo_answer)
    if login and passwd:
        auth(sock, bytes(login, encoding="utf-8"), bytes(passwd, encoding="utf-8"))
    mailfrom_answer = change_data(sock, b"MAIL FROM: <" + b_mail_from + b">\r\n")
    print(mailfrom_answer)
    rcptto_answer = change_data(sock, b"RCPT TO: <" + b_mail_to + b">\r\n")
    print(rcptto_answer)
    data_answer = change_data(sock, b"DATA\r\n")
    print(data_answer)
 
 
def create_base64image(name_file):
    with open(name_file, 'rb') as f:
        b_content_file = base64.b64encode(f.read())
        return_str = list(str(b_content_file)[2:-1])
        count = len(return_str) / 70
        for i in range(1, int(count) + 1):
            return_str.insert(i*70, '\n')
        return bytes("".join(return_str), encoding="utf-8")
 
 
def send_image(sock, expansion, file):
    expansion = bytes(expansion, encoding="utf-8")
    name_file = bytes(file, encoding="utf-8")
    send_data(sock, b"--" + SEPARATOR + b"\r\n")
    send_data(sock, b"Content-Type: image/" + expansion + b"\r\n")
    send_data(sock, b"Content-Transfer-Encoding: base64\r\n")
    send_data(sock, b"Content-Disposition:attachment;filename=" + name_file + b"\n")
    send_data(sock, b"Content-Id: attachedImage\r\n\r\n")
    send_data(sock, create_base64image(name_file) + b'\r\n')
    send_data(sock, b'\r\n')
 
 
def send_images(sock, directory=None):
    if not directory:
        directory = os.getcwd()
    try:
        files = os.listdir(directory)
    except:
        sys.stderr.write("Incorrect directory")
        sys.exit(1)
    for file in files:
        expansion = (file.split('.'))[-1]
        if expansion.lower() in IMAGE_EXPANSION:
            send_image(sock, expansion, file)
 
 
def body(sock, b_sender, b_receiver, b_subject, b_date, directory=None):
    send_data(sock, b"From: " + b_sender + b"\r\n")
    send_data(sock, b"To: " + b_receiver + b"\r\n")
    send_data(sock, b"Subject: " + b_subject + b"\r\n")
    send_data(sock, b"Date: " + b_date + b"\r\n")
    send_data(sock, b"Content-Type: multipart/mixed; boundary=" + SEPARATOR + b"\r\n")
    send_data(sock, b"\r\n")
 
    send_images(sock, directory)
    send_data(sock, b"--" + SEPARATOR + b"--\r\n")
    answer = change_data(sock, b".\r\n")
 
 
def write_letter(serv_addr, login, passwd, b_mail_from, b_mail_to, b_sender, b_receiver, b_subject, directory=None):
    date = datetime.datetime.now()
    date = str(date.year) + "-" + str(date.month) + '-' + str(date.day)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = ssl.wrap_socket(sock)
    curr_sock = connect(ssl_sock, sock, serv_addr, DEFAULT_PORT, ADDITIONAL_PORT)
    header(curr_sock, login, passwd, b_mail_from, b_mail_to)
    body(curr_sock, b_sender, b_receiver, b_subject, bytes(date, encoding="utf-8"), directory=None)
 
 
def main(from_mail, to_mail, addr_serv, login, passwd, name_directory=None):
    sender = '=?utf-8?B?' + str(base64.b64encode(bytes(DEFAULT_SENDER, encoding='windows-1251')))[2:-1] + \
             '?= <' + login + '>'
    subject = '=?utf-8?B?' + str(base64.b64encode(bytes(DEFAULT_SUBJECT, encoding='windows-1251')))[2:-1] + '?='
    receiver = '=?utf-8?B?' + str(base64.b64encode(bytes(to_mail, encoding='windows-1251')))[2:-1] + \
               '?= <' + to_mail + '>'
    write_letter(addr_serv,
                 login, passwd,
                 bytes(from_mail, encoding="utf-8"),
                 bytes(to_mail, encoding="utf-8"),
                 bytes(sender, encoding="utf-8"),
                 bytes(receiver, encoding="utf-8"),
                 bytes(subject, encoding="utf-8"),
                 name_directory)
 
 
def get_args():
    parser = argparse.ArgumentParser(description="SMTP-MIME")
    parser.add_argument("send_email", nargs="?", default="smtp2smtp@mail.ru", help="sender's email")
    parser.add_argument("recv_email", nargs="?", default="beklenischeva-elena@yandex.ru", help="receiver's email")
    parser.add_argument("addr_serv", nargs="?", default="smtp.mail.ru", help="server's address")
    parser.add_argument("--auth", action="store_true", default="False", help="key for authorization")
    parser.add_argument("directory", nargs="?", default=None, help="Name directory with images")
    args = parser.parse_args()
    return args
 
 
if __name__ == "__main__":
    args = get_args()
    login = passwd = None
    if args.auth == True:
        login = input("Input login\n")
        passwd = getpass.getpass()
    else:
        login = args.send_email
    main(args.send_email, args.recv_email, args.addr_serv, login, passwd, args.directory)