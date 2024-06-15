import socket
from typing import Optional


def start_udp_server(
    udp_ip: str, udp_port: int, forward_ip: Optional[str], forward_port: Optional[int]
) -> None:
    address = (udp_ip, udp_port)
    forward_address = (forward_ip, forward_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_forward = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(address)

    print(f"UDP server started on {address}")
    if forward_ip and forward_port:
        print(f"Forwarding to {forward_address}")
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received message from {addr}: {data.decode()}")
        if forward_ip and forward_port:
            sock_forward.sendto(data, forward_address)
            print(f"Forwarded message to {forward_address}")
