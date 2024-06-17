import socket
import threading
from typing import Optional

from rich import print as rprint


def start_udp_server(
    udp_ip: str,
    udp_port: int,
    forward_ip: Optional[str],
    forward_port: Optional[int],
    stop_event: Optional[threading.Event] = None,
) -> None:
    address = (udp_ip, udp_port)
    forward_address = (forward_ip, forward_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_forward = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(address)

    rprint(f"UDP server started on {address}")
    if forward_ip and forward_port:
        rprint(f"Forwarding to {forward_address}")
    while not stop_event or not stop_event.is_set():
        data, addr = sock.recvfrom(1024)
        rprint(f"Received message from {addr}: {data.decode()}")
        if forward_ip and forward_port:
            sock_forward.sendto(data, forward_address)
            rprint(f"Forwarded message to {forward_address}")

    sock.close()
    if forward_ip and forward_port:
        sock_forward.close()
