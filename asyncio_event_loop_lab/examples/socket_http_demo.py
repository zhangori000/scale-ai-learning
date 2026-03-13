from __future__ import annotations

import socket

from asyncio_event_loop_lab.mini_asyncio import get_running_loop, run


async def fetch_example_dot_com() -> None:
    loop = get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)

    try:
        await loop.sock_connect(sock, ("example.com", 80))
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
        await loop.sock_sendall(sock, request)

        chunks: list[bytes] = []
        while True:
            chunk = await loop.sock_recv(sock, 4096)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        sock.close()

    response = b"".join(chunks).decode("latin1", errors="replace")
    headers, _, _body = response.partition("\r\n\r\n")
    print(headers)


if __name__ == "__main__":
    run(fetch_example_dot_com())
