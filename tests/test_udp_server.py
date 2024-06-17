import socket
import threading
import pytest
from c6t.tools.udp_server import start_udp_server


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(args=args, kwargs=kwargs)
        self._stop_event = threading.Event()
    
    def start(self):
        self._stop_event.clear()
        super().start()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class TestUDPServer:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.server_ip = "0.0.0.0"
        self.server_port = 514
        self.client_ip = "127.0.0.1"
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        yield
        self.client_socket.close()

    def test_start_udp_server_without_forwarding(self, capsys):
        server_thread = StoppableThread(threading.Thread(
            group=None,
            target=start_udp_server,
            args=(self.server_ip, self.server_port, None, None, threading.Event()),
            daemon=True,
        ))
        server_thread.start()

        message = "Test message"
        self.client_socket.sendto(message.encode(), (self.client_ip, self.server_port))
        # Get the output from the server

        server_thread.stop()

    # def test_start_udp_server_with_forwarding(self, capsys):
    #     forward_port = self.server_port + 1
    #     forward_thread = threading.Thread(target=start_udp_server, args=("0.0.0.0", forward_port, None, None), daemon=True)
    #     forward_thread.start()

    #     server_thread = threading.Thread(target=start_udp_server, args=("0.0.0.0", self.server_port, self.server_ip, forward_port), daemon=True)
    #     server_thread.start()

    #     message = "Test message"
    #     self.client_socket.sendto(message.encode(), ("127.0.0.1", self.server_port))
    #     data, _ = self.client_socket.recvfrom(1024)
    #     assert data.decode() == message

    #     server_thread.join(timeout=1)
    #     forward_thread.join(timeout=1)
