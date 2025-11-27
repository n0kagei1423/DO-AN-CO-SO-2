import requests     # Thư viện để gửi yêu cầu HTTP (tải file/up file)
import threading    # Thư viện để chạy đa luồng (xử lý song song)
import time         # Thư viện đo thời gian
import socket       # Thư viện kết nối mạng cấp thấp (để đo Ping TCP)
import os           # Thư viện tương tác hệ điều hành (để tạo dữ liệu rác)
import psutil       # Thư viện lấy thông tin hệ thống (để đo băng thông tổng)

# --- CẤU HÌNH ---
# Link tải file mẫu 50MB từ Cloudflare (Server CDN rất nhanh và ổn định)
URL_DOWNLOAD = "https://speed.cloudflare.com/__down?bytes=50000000"
# Link đích để upload dữ liệu lên
URL_UPLOAD = "https://speed.cloudflare.com/__up"
# Danh sách server Việt Nam để đo Ping (cổng 443 là cổng web HTTPS thông dụng)
SERVERS_VIETNAM = [("vnexpress.net", 443), ("dantri.com.vn", 443)]
# API miễn phí để lấy địa chỉ IP và tên nhà mạng
URL_IP_INFO = "http://ip-api.com/json/"

# Cấu hình kỹ thuật: Chạy 4 luồng song song trong 10 giây
SO_LUONG_LUONG = 4
THOI_GIAN_TEST = 10 

# --- BIẾN TOÀN CỤC (GLOBAL VARIABLES) ---
# Dùng để lưu giữ đối tượng đang chạy đo, giúp ta có thể gọi lệnh dừng nó từ bên ngoài
core_hien_tai = None  
# Cờ hiệu (Flag): Nếu biến này = True, mọi vòng lặp phải dừng lại ngay lập tức
co_lenh_huy = False   

# --- CÁC HÀM HỖ TRỢ ---
def lay_thong_tin_ip():
    try:
        # Thêm header để yêu cầu server không trả lại kết quả cũ
        headers = {'Cache-Control': 'no-cache'}
        response = requests.get(URL_IP_INFO, headers=headers, timeout=3)
        data = response.json()
        return {
            "ip": data.get('query', '---'), 
            "city": data.get('city', '---'), 
            "country": data.get('country', '---'), 
            "isp": data.get('isp', '---')
        }
    except:
        return None

def kich_hoat_lenh_huy():
    """Hàm này được Giao diện gọi khi người dùng bấm nút Hủy"""
    global co_lenh_huy, core_hien_tai
    co_lenh_huy = True # Bật cờ báo động
    if core_hien_tai:
        core_hien_tai.dung_lai_ngay() # Ra lệnh cho bộ xử lý dừng lại

def reset_trang_thai():
    """Xóa sạch các cờ báo động trước khi bắt đầu đo mới"""
    global co_lenh_huy, core_hien_tai
    co_lenh_huy = False
    core_hien_tai = None

# --- CLASS CHÍNH: BỘ XỬ LÝ TỐC ĐỘ ---
class BoXuLyTocDo:
    def __init__(self, mode="download"):
        self.tong_bytes = 0       # Biến đếm tổng số byte đã tải/up được
        self.dang_chay = False    # Trạng thái: Đang chạy hay đã dừng
        self.lock = threading.Lock() # Cái khóa: Đảm bảo khi cộng điểm không bị tranh chấp giữa các luồng
        self.mode = mode          # Chế độ: 'download' hoặc 'upload'
        
        # Nếu là upload, tạo trước 1 cục dữ liệu rác 1MB trong RAM
        # os.urandom tạo ra byte ngẫu nhiên để modem không thể nén dữ liệu (đo chính xác hơn)
        if mode == "upload":
            self.data_upload = os.urandom(1024 * 1024) 

    def dung_lai_ngay(self):
        """Hàm gạt cần số về 0 để dừng vòng lặp"""
        self.dang_chay = False

    # ... (Phần bên trên giữ nguyên) ...

    def worker(self):
        # 1. CẤU HÌNH HEADERS ĐỂ GIẢ LẬP TRÌNH DUYỆT (Tránh bị Cloudflare chặn/lơ)
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }

        # 2. CẤU HÌNH ADAPTER ĐỂ TỰ THỬ LẠI (RETRY)
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Cập nhật headers cho session
        session.headers.update(HEADERS)
        
        start_time = time.time()
        
        # 3. CẤU HÌNH TIMEOUT THÔNG MINH
        # (Connect Timeout: 5s, Read Timeout: 20s)
        # 4G thường connect nhanh nhưng download dữ liệu thì hay bị khựng, nên cần Read Timeout dài.
        TIMEOUT_CONFIG = (5.0, 20.0) 

        while self.dang_chay and (time.time() - start_time < THOI_GIAN_TEST):
            try:
                if self.mode == "download":
                    # stream=True: Tải dòng chảy
                    with session.get(URL_DOWNLOAD, stream=True, timeout=TIMEOUT_CONFIG) as response:
                        # Kiểm tra xem server có từ chối không (403/404/500)
                        if response.status_code != 200:
                            time.sleep(0.5)
                            continue

                        for chunk in response.iter_content(chunk_size=102400):
                            if not self.dang_chay: return 
                            if chunk:
                                with self.lock: self.tong_bytes += len(chunk)
                else:
                    # Upload
                    session.post(URL_UPLOAD, data=self.data_upload, timeout=TIMEOUT_CONFIG)
                    with self.lock: self.tong_bytes += len(self.data_upload)

            except requests.exceptions.ReadTimeout:
                # NẾU BỊ READ TIMEOUT -> KHÔNG CRASH, CHỈ CẦN THỬ LẠI
                # print("Bị Timeout, đang thử lại...") # Bỏ comment nếu muốn debug
                time.sleep(0.2) 
            except requests.exceptions.ConnectionError:
                # Lỗi mất mạng hẳn
                time.sleep(0.5)
            except Exception as e:
                # Các lỗi khác
                time.sleep(0.5)
        
        session.close()

    # ... (Phần bên dưới giữ nguyên) ...

    def bat_dau(self, callback_update=None):
        """Hàm quản lý chính, tính toán tốc độ hiển thị"""
        self.tong_bytes = 0
        self.dang_chay = True
        danh_sach_luong = []

        # Tạo và khởi động 4 công nhân (threads)
        for i in range(SO_LUONG_LUONG):
            t = threading.Thread(target=self.worker)
            t.start()
            danh_sach_luong.append(t)

        # Chuẩn bị biến để tính tốc độ Real-time
        start_time = time.time()
        last_time = start_time
        last_bytes = 0
        current_display_speed = 0

        # Vòng lặp giám sát (Chạy song song với 4 công nhân kia)
        while time.time() - start_time < THOI_GIAN_TEST:
            if not self.dang_chay: break # Thoát nếu bị hủy

            time.sleep(0.25) # Cứ 0.25 giây dậy tính toán 1 lần
            now = time.time()
            
            # Tính lượng thay đổi trong 0.25s vừa qua (Delta)
            delta_time = now - last_time
            delta_bytes = self.tong_bytes - last_bytes
            
            if delta_time > 0:
                # Công thức: (Số Byte * 8 bit) / (Thời gian * 1 triệu) = Mbps
                instant_speed = (delta_bytes * 8) / (delta_time * 1_000_000)
                
                # Thuật toán làm mượt (Smoothing):
                # Tốc độ hiển thị = 70% số cũ + 30% số mới
                # Giúp kim đồng hồ không bị giật cục
                if current_display_speed == 0: current_display_speed = instant_speed
                else: current_display_speed = (current_display_speed * 0.7) + (instant_speed * 0.3)
                
                # Gọi ngược về giao diện để cập nhật số
                if callback_update: callback_update(round(current_display_speed, 2))
            
            # Cập nhật mốc cũ
            last_time = now
            last_bytes = self.tong_bytes

        # Dọn dẹp: Chờ tất cả công nhân về đích
        self.dang_chay = False
        for t in danh_sach_luong:
            t.join()

        if co_lenh_huy: return None

        # Tính tốc độ trung bình toàn quá trình (Số chốt hạ)
        final_speed = (self.tong_bytes * 8) / ((time.time() - start_time) * 1_000_000)
        return round(final_speed, 2)

# --- CÁC HÀM WRAPPER (Vỏ bọc) ---
# Các hàm này giúp Giao diện gọi Logic dễ dàng hơn
def ping_tcp(host, port):
    """
    Sử dụng socket.create_connection để hỗ trợ cả IPv4 và IPv6.
    Tự động xử lý DNS cho mạng di động.
    """
    try:
        start = time.time()
        # socket.create_connection tự động chọn IPv4/IPv6 và tự xử lý socket
        # Tăng timeout lên 3 giây cho mạng 4G yếu
        s = socket.create_connection((host, port), timeout=3.0) 
        end = time.time()
        s.close()
        return (end - start) * 1000
    except Exception as e:
        # Uncomment dòng dưới để xem lỗi gì trong Terminal nếu cần debug
        print(f"Lỗi Ping {host}: {e}")
        return 9999

def lay_ping():
    """Chiến thuật Best-of-3: Đo 3 lần lấy số nhỏ nhất"""
    global co_lenh_huy
    ket_qua_tot_nhat = 9999
    host, port = SERVERS_VIETNAM[0]
    for _ in range(3):
        if co_lenh_huy: return None
        p = ping_tcp(host, port)
        if p < ket_qua_tot_nhat: ket_qua_tot_nhat = p
        time.sleep(0.1)
    return round(ket_qua_tot_nhat, 0) if ket_qua_tot_nhat < 9999 else None

# Hai hàm này khởi tạo đối tượng BoXuLyTocDo và chạy nó
def do_download(callback_func=None):
    global core_hien_tai
    core_hien_tai = BoXuLyTocDo(mode="download")
    return core_hien_tai.bat_dau(callback_update=callback_func)

def do_upload(callback_func=None):
    global core_hien_tai
    core_hien_tai = BoXuLyTocDo(mode="upload")
    return core_hien_tai.bat_dau(callback_update=callback_func)

# --- PHẦN GIÁM SÁT HỆ THỐNG ---
# Sử dụng psutil để đọc thông số card mạng của máy tính
class GiamSatHeThong:
    def __init__(self):
        self.dang_chay = False
    def bat_dau_giam_sat(self, callback_update):
        self.dang_chay = True
        # Lấy mốc dữ liệu ban đầu
        last_received = psutil.net_io_counters().bytes_recv
        last_sent = psutil.net_io_counters().bytes_sent
        while self.dang_chay:
            time.sleep(1) # Cập nhật mỗi giây
            counters = psutil.net_io_counters()
            # Tính lượng chênh lệch (Mới - Cũ)
            new_received = counters.bytes_recv - last_received
            new_sent = counters.bytes_sent - last_sent
            
            # Gửi dữ liệu về (Đổi ra MB)
            if callback_update:
                callback_update(new_received / 1024 / 1024, new_sent / 1024 / 1024)
            
            last_received = counters.bytes_recv
            last_sent = counters.bytes_sent
    def dung_giam_sat(self):
        self.dang_chay = False

def chay_giam_sat_he_thong(callback):
    monitor = GiamSatHeThong()
    t = threading.Thread(target=monitor.bat_dau_giam_sat, args=(callback,))
    t.daemon = True # Thread daemon sẽ tự chết khi tắt app chính
    t.start()
    return monitor