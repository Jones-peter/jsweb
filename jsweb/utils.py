import socket


def get_local_ip():
    """
    Attempts to determine the local IP address of the machine.

    This function creates a temporary socket and connects to a public-facing
    IP address to determine the primary local IP address of the host machine.
    This is useful for displaying a network-accessible URL for the server.

    If the IP address cannot be determined (e.g., no network connection),
    it defaults to '127.0.0.1'.

    Returns:
        str: The local IP address as a string.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send data, just connects to find the best interface
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
