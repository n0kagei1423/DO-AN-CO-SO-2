import requests
import time
import random
import string


# Cấu hình URL test (Sử dụng file 10MB của Tele2)
URL_DOWNLOAD = "https://speed.cloudflare.com/__down?bytes=50000000"
URL_PING = "http://google.com"
URL_UPLOAD = "https://httpbin.org/post" 

def do_ping():
    """
    Gửi request đến Google để đo độ trễ.
    Trả về: số mili-giây (ms) hoặc None nếu lỗi.
    """
    try:
        start = time.time()
        requests.get(URL_PING, timeout=5)
        end = time.time()
        return round((end - start) * 1000, 2)
    except Exception as e:
        print(f"Lỗi Ping: {e}")
        return None

def do_download():
    """
    Tải file mẫu về để đo tốc độ.
    Trả về: tốc độ (Mbps) hoặc None nếu lỗi.
    """
    try:
        start_time = time.time()
        # stream=True để không tải toàn bộ vào RAM ngay lập tức
        response = requests.get(URL_DOWNLOAD, stream=True, timeout=20)
        
        downloaded_bytes = 0
        
        # Đọc dữ liệu theo từng khối (chunk) 1KB
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                downloaded_bytes += len(chunk)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Công thức: (Bytes * 8) / (Giây * 1,000,000) = Mbps
        speed_mbps = (downloaded_bytes * 8) / (duration * 1_000_000)
        
        return round(speed_mbps, 2)
    except Exception as e:
        print(f"Lỗi Download: {e}")
        return None

def generate_random_data(size_mb):
    """
    Tạo dữ liệu ngẫu nhiên để upload
    """
    size_bytes = size_mb * 1024 * 1024
    return ''.join(random.choices(string.ascii_letters, k=size_bytes)).encode()

def do_upload():
    """
    Đo tốc độ upload bằng cách gửi file 5MB lên server
    """
    try:
        data = generate_random_data(5)  # 5MB
        start_time = time.time()

        response = requests.post(URL_UPLOAD, data=data)

        end_time = time.time()
        duration = end_time - start_time

        if response.status_code == 200:
            speed_mbps = (5 * 8) / duration  # 5MB = 40 Mb
            return round(speed_mbps, 2)
        else:
            print("Upload lỗi:", response.status_code)
            return None

    except Exception as e:
        print(f"Lỗi Upload: {e}")
        return None
