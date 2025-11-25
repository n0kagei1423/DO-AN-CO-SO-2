import requests
import threading
import time
import socket
import os

# --- CẤU HÌNH ---
URL_DOWNLOAD = "https://speed.cloudflare.com/__down?bytes=50000000"
URL_UPLOAD = "https://speed.cloudflare.com/__up"
SERVERS_VIETNAM = [("vnexpress.net", 443), ("dantri.com.vn", 443)]
URL_IP_INFO = "http://ip-api.com/json/"

SO_LUONG_LUONG = 4
THOI_GIAN_TEST = 10 

# BIẾN TOÀN CỤC ĐỂ QUẢN LÝ VIỆC HỦY
core_hien_tai = None  # Lưu đối tượng đang chạy đo
co_lenh_huy = False   # Cờ báo hiệu lệnh hủy

# --- CÁC HÀM HỖ TRỢ ---
def lay_thong_tin_ip():
    try:
        response = requests.get(URL_IP_INFO, timeout=3)
        data = response.json()
        return {"ip": data.get('query'), "city": data.get('city'), "country": data.get('country'), "isp": data.get('isp')}
    except:
        return None

def kich_hoat_lenh_huy():
    """Hàm này được gọi từ Giao diện khi bấm nút Hủy"""
    global co_lenh_huy, core_hien_tai
    co_lenh_huy = True
    if core_hien_tai:
        core_hien_tai.dung_lai_ngay()

def reset_trang_thai():
    """Reset trạng thái trước khi đo mới"""
    global co_lenh_huy, core_hien_tai
    co_lenh_huy = False
    core_hien_tai = None

# --- CLASS XỬ LÝ CHÍNH ---
class BoXuLyTocDo:
    def __init__(self, mode="download"):
        self.tong_bytes = 0
        self.dang_chay = False
        self.lock = threading.Lock()
        self.mode = mode
        if mode == "upload":
            self.data_upload = os.urandom(1024 * 1024) 

    def dung_lai_ngay(self):
        """Hàm phanh gấp"""
        self.dang_chay = False

    def worker(self):
        session = requests.Session()
        start_time = time.time()
        while self.dang_chay and (time.time() - start_time < THOI_GIAN_TEST):
            try:
                if self.mode == "download":
                    with session.get(URL_DOWNLOAD, stream=True, timeout=5) as response:
                        for chunk in response.iter_content(chunk_size=102400):
                            if not self.dang_chay: return # Ngắt ngay
                            if chunk:
                                with self.lock: self.tong_bytes += len(chunk)
                else:
                    session.post(URL_UPLOAD, data=self.data_upload, timeout=5)
                    with self.lock: self.tong_bytes += len(self.data_upload)
            except:
                time.sleep(0.1)
        session.close()

    def bat_dau(self, callback_update=None):
        self.tong_bytes = 0
        self.dang_chay = True
        danh_sach_luong = []

        # Chạy worker
        for i in range(SO_LUONG_LUONG):
            t = threading.Thread(target=self.worker)
            t.start()
            danh_sach_luong.append(t)

        start_time = time.time()
        last_time = start_time
        last_bytes = 0
        current_display_speed = 0

        # Vòng lặp chính
        while time.time() - start_time < THOI_GIAN_TEST:
            # Nếu nhận lệnh hủy từ bên ngoài
            if not self.dang_chay:
                break

            time.sleep(0.25)
            now = time.time()
            delta_time = now - last_time
            delta_bytes = self.tong_bytes - last_bytes
            
            if delta_time > 0:
                instant_speed = (delta_bytes * 8) / (delta_time * 1_000_000)
                if current_display_speed == 0: current_display_speed = instant_speed
                else: current_display_speed = (current_display_speed * 0.7) + (instant_speed * 0.3)
                if callback_update: callback_update(round(current_display_speed, 2))
            
            last_time = now
            last_bytes = self.tong_bytes

        # Dọn dẹp
        self.dang_chay = False
        for t in danh_sach_luong:
            t.join()

        # Nếu bị hủy giữa chừng -> Trả về None
        if co_lenh_huy:
            return None

        final_speed = (self.tong_bytes * 8) / ((time.time() - start_time) * 1_000_000)
        return round(final_speed, 2)

# --- WRAPPER FUNCTIONS ---
def ping_tcp(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        start = time.time()
        s.connect((host, port))
        end = time.time()
        s.close()
        return (end - start) * 1000
    except:
        return 9999

def lay_ping():
    global co_lenh_huy
    ket_qua_tot_nhat = 9999
    host, port = SERVERS_VIETNAM[0]
    for _ in range(3):
        if co_lenh_huy: return None # Kiểm tra lệnh hủy giữa các lần ping
        p = ping_tcp(host, port)
        if p < ket_qua_tot_nhat: ket_qua_tot_nhat = p
        time.sleep(0.1)
    return round(ket_qua_tot_nhat, 0) if ket_qua_tot_nhat < 9999 else None

def do_download(callback_func=None):
    global core_hien_tai
    core_hien_tai = BoXuLyTocDo(mode="download")
    return core_hien_tai.bat_dau(callback_update=callback_func)

def do_upload(callback_func=None):
    global core_hien_tai
    core_hien_tai = BoXuLyTocDo(mode="upload")
    return core_hien_tai.bat_dau(callback_update=callback_func)

# --- MONITOR SYSTEM (GIỮ NGUYÊN) ---
class GiamSatHeThong:
    def __init__(self):
        self.dang_chay = False
    def bat_dau_giam_sat(self, callback_update):
        self.dang_chay = True
        last_received = psutil.net_io_counters().bytes_recv
        last_sent = psutil.net_io_counters().bytes_sent
        while self.dang_chay:
            time.sleep(1)
            counters = psutil.net_io_counters()
            new_received = counters.bytes_recv - last_received
            new_sent = counters.bytes_sent - last_sent
            if callback_update:
                callback_update(new_received / 1024 / 1024, new_sent / 1024 / 1024)
            last_received = counters.bytes_recv
            last_sent = counters.bytes_sent
    def dung_giam_sat(self):
        self.dang_chay = False

import psutil # Import ở đây hoặc đầu file
def chay_giam_sat_he_thong(callback):
    monitor = GiamSatHeThong()
    t = threading.Thread(target=monitor.bat_dau_giam_sat, args=(callback,))
    t.daemon = True
    t.start()
    return monitor