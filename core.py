import requests
import threading
import time
import socket # <--- Thư viện mới để đo Ping chuẩn hơn
import os

# Link Cloudflare (Server quốc tế tốc độ cao)
URL_DOWNLOAD = "https://speed.cloudflare.com/__down?bytes=50000000"
URL_UPLOAD = "https://speed.cloudflare.com/__up"
# Dùng Google DNS để đo Ping TCP (Rất ổn định)
PING_HOST = "8.8.8.8"
PING_PORT = 53

# API thông tin
URL_IP_INFO = "http://ip-api.com/json/"

SO_LUONG_LUONG = 4
THOI_GIAN_TEST = 10 

def lay_thong_tin_ip():
    try:
        response = requests.get(URL_IP_INFO, timeout=3)
        data = response.json()
        return {
            "ip": data.get('query', '---'),
            "city": data.get('city', '---'),
            "country": data.get('country', '---'),
            "isp": data.get('isp', '---')
        }
    except:
        return None

# --- CẤU HÌNH PING MỚI ---
# Danh sách các server tại Việt Nam để đo ping thấp nhất
# Port 443 là port HTTPS, luôn mở và phản hồi nhanh
SERVERS_VIETNAM = [
    ("vnexpress.net", 443),
    ("dantri.com.vn", 443),
    ("zingnews.vn", 443)
]

def ping_tcp(host, port):
    """Hàm đo 1 lần kết nối"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0) # Timeout ngắn thôi
        
        start = time.time()
        s.connect((host, port))
        end = time.time()
        
        s.close()
        return (end - start) * 1000
    except:
        return 9999 # Trả về số lớn nếu lỗi

def do_ping():
    """
    Chiến thuật mới: 
    1. Ping tới server Việt Nam.
    2. Ping 3 lần, lấy kết quả NHỎ NHẤT (Min Ping).
    """
    ket_qua_tot_nhat = 9999
    
    # Thử server đầu tiên trong danh sách (VnExpress)
    host, port = SERVERS_VIETNAM[0]
    
    # Ping 3 lần liên tiếp (Warm-up)
    ds_ping = []
    for _ in range(3):
        p = ping_tcp(host, port)
        ds_ping.append(p)
        time.sleep(0.05) # Nghỉ cực ngắn giữa các lần bắn
        
    # Lấy giá trị thấp nhất (Đây là cách Speedtest làm)
    # Vì ping cao có thể do nghẽn tức thời, ping thấp nhất mới là giới hạn vật lý
    if ds_ping:
        min_ping = min(ds_ping)
        if min_ping < 9999:
            return round(min_ping, 0) # Không lấy số lẻ
            
    return None

# --- CLASS XỬ LÝ TỐC ĐỘ (Up & Down) ---
class BoXuLyTocDo:
    def __init__(self, mode="download"):
        self.tong_bytes = 0
        self.dang_chay = False
        self.lock = threading.Lock()
        self.mode = mode
        
        # Tối ưu Upload: Tạo sẵn cục dữ liệu to (1MB) để đỡ tốn CPU tạo đi tạo lại
        if mode == "upload":
            # Tạo 1MB dữ liệu ngẫu nhiên
            self.data_upload = os.urandom(1024 * 1024) 

    def worker(self):
        # TẠO SESSION: Giữ kết nối sống (Keep-Alive), tăng tốc độ Upload cực nhiều
        session = requests.Session()
        
        start_time = time.time()
        while self.dang_chay and (time.time() - start_time < THOI_GIAN_TEST):
            try:
                if self.mode == "download":
                    # DOWNLOAD
                    with session.get(URL_DOWNLOAD, stream=True, timeout=5) as response:
                        for chunk in response.iter_content(chunk_size=102400): # Tăng chunk lên 100KB
                            if not self.dang_chay or (time.time() - start_time > THOI_GIAN_TEST): return
                            if chunk:
                                with self.lock: self.tong_bytes += len(chunk)
                                
                else:
                    # UPLOAD
                    # post dữ liệu liên tục qua session đã mở
                    session.post(URL_UPLOAD, data=self.data_upload, timeout=5)
                    with self.lock:
                        self.tong_bytes += len(self.data_upload)
                        
            except Exception:
                time.sleep(0.1)
        
        # Đóng session khi xong
        session.close()

    def bat_dau(self, callback_update=None):
        self.tong_bytes = 0
        self.dang_chay = True
        danh_sach_luong = []

        for i in range(SO_LUONG_LUONG):
            t = threading.Thread(target=self.worker)
            t.start()
            danh_sach_luong.append(t)

        start_time = time.time()
        last_time = start_time
        last_bytes = 0
        current_display_speed = 0

        while time.time() - start_time < THOI_GIAN_TEST:
            time.sleep(0.25)
            
            now = time.time()
            delta_time = now - last_time
            delta_bytes = self.tong_bytes - last_bytes
            
            if delta_time > 0:
                instant_speed = (delta_bytes * 8) / (delta_time * 1_000_000)
                
                # Logic làm mượt hiển thị
                if current_display_speed == 0:
                    current_display_speed = instant_speed
                else:
                    current_display_speed = (current_display_speed * 0.7) + (instant_speed * 0.3)

                if callback_update:
                    callback_update(round(current_display_speed, 2))
            
            last_time = now
            last_bytes = self.tong_bytes

        self.dang_chay = False
        for t in danh_sach_luong:
            t.join()

        final_speed = (self.tong_bytes * 8) / ((time.time() - start_time) * 1_000_000)
        return round(final_speed, 2)

# --- WRAPPER FUNCTIONS ---
# Hàm ping giờ gọi hàm do_ping mới ở trên
def lay_ping():
    return do_ping()

def do_download(callback_func=None):
    core = BoXuLyTocDo(mode="download")
    return core.bat_dau(callback_update=callback_func)

def do_upload(callback_func=None):
    core = BoXuLyTocDo(mode="upload")
    return core.bat_dau(callback_update=callback_func)