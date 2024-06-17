import socket
import typing
from datetime import datetime, timezone
from enum import Enum


class SyslogFacility(Enum):
    KERN = 0
    USER = 1
    MAIL = 2
    DAEMON = 3
    AUTH = 4
    SYSLOG = 5
    LPR = 6
    NEWS = 7
    UUCP = 8
    CRON = 9
    AUTHPRIV = 10
    FTP = 11
    NTP = 12
    SECURITY = 13
    CONSOLE = 14
    SOLARIS_CRON = 15
    LOCAL0 = 16
    LOCAL1 = 17
    LOCAL2 = 18
    LOCAL3 = 19
    LOCAL4 = 20
    LOCAL5 = 21
    LOCAL6 = 22
    LOCAL7 = 23


class SyslogSeverity(Enum):
    EMERGENCY = 0
    ALERT = 1
    CRITICAL = 2
    ERROR = 3
    WARNING = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7


def get_c6t_version() -> str:
    return "0.0.0"


def get_local_ip_address() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return typing.cast(str, ip_address)


def get_current_time() -> str:
    now = datetime.now(timezone.utc).astimezone()
    formatted_time = now.strftime("%b %d %Y %H:%M:%S.%f")[:-3] + now.strftime("%z")
    return formatted_time


def get_syslog_priority(syslog_facility: int, syslog_severity: int) -> int:
    return syslog_facility * 8 + syslog_severity


def create_cef_message(syslog_facility: int, syslog_severity: int, message: str) -> str:
    current_time = get_current_time()
    ip_address = get_local_ip_address()
    syslog_priority = get_syslog_priority(
        syslog_facility=syslog_facility, syslog_severity=syslog_severity
    )
    c6t_version = get_c6t_version()
    return f"<{syslog_priority}>{current_time} {ip_address} CEF:0|Contrast Security|Contrast - c6t|{c6t_version}|TEST|{message}"


def send_udp_test_message(
    udp_ip: str, udp_port: int, syslog_facility: int, syslog_severity: int, message: str
) -> None:
    """
    Send a UDP message to the specified IP and port.
    """
    address = (udp_ip, udp_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cef_message = create_cef_message(
        syslog_facility=syslog_facility,
        syslog_severity=syslog_severity,
        message=message,
    )
    sock.sendto(cef_message.encode(), address)
    print(f"Sent message to {address}: {cef_message}")
