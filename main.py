from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import UDPServer, BaseRequestHandler
import mimetypes
import socket
import urllib.parse
import pathlib
import json
from datetime import datetime
import threading


# Адреса та порт, на який прослуховується Socket сервер
UDP_SERVER_ADDRESS = ('localhost', 5000)

# Створення UDP клієнта
socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        # Отримані дані передаються на Socket сервер
        socket_client.sendto(data, ('localhost', 5000))
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)

        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')

        self.end_headers()

        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


class SocketHandler(BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        # Зберігаємо дані у файлі data.json
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        with open('storage/data.json', 'a') as file:
            json.dump({current_time: data_dict}, file)
            file.write('\n')


def run_http_server():
    server_address = ('', 3000)
    http_server = HTTPServer(server_address, HttpHandler)
    http_server.serve_forever()


def run_socket_server():
    server_address = ('', 5000)
    socket_server = UDPServer(server_address, SocketHandler)
    socket_server.serve_forever()


if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    socket_thread = threading.Thread(target=run_socket_server)

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()
