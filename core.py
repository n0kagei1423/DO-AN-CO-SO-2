import socket
import time
import requests

import matplotlib
matplotlib.use("TkAgg")


def tcp_ping(host="8.8.8.8", port=80, repeat=5, timeout=2):
    times = []

    for _ in range(repeat):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        start = time.time()
        try:
            s.connect((host, port))
            end = time.time()
            times.append((end - start) * 1000)
        except:
            times.append(None)
        s.close()

    valid = [t for t in times if t]
    return sum(valid)/len(valid) if valid else None


def download_speed(url="http://speed.hetzner.de/10MB.bin", size_bytes=3_000_000):
    r = requests.get(url, stream=True)
    start = time.time()

    total = 0
    for chunk in r.iter_content(1024 * 50):
        total += len(chunk)
        if total >= size_bytes:
            break

    end = time.time()
    elapsed = end - start
    mbps = (total * 8) / (elapsed * 1_000_000)
    return mbps


def upload_speed(url="https://httpbin.org/post", size_bytes=1_000_000):
    data = b"x" * size_bytes
    start = time.time()
    requests.post(url, data=data)
    end = time.time()

    elapsed = end - start
    mbps = (size_bytes * 8) / (elapsed * 1_000_000)
    return mbps
