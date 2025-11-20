import tkinter as tk
from tkinter import messagebox
import threading
import core  # <--- Kết nối với file logic ở trên

class UngDungSpeedTest:
    def __init__(self, root_window):
        self.root = root_window
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        self.root.title("Python Speed Test (Module)")
        self.root.geometry("400x350")
        self.root.resizable(False, False)

        # Tiêu đề
        tk.Label(self.root, text="KIỂM TRA MẠNG", font=("Arial", 18, "bold")).pack(pady=20)

        # Khu vực kết quả
        self.frame_result = tk.Frame(self.root)
        self.frame_result.pack(pady=10)

        # Ping
        self.lbl_ping = tk.Label(self.frame_result, text="Ping: --- ms", font=("Arial", 12))
        self.lbl_ping.pack(pady=5)

        # Download
        self.lbl_down = tk.Label(self.frame_result, text="Download: --- Mbps", font=("Arial", 12))
        self.lbl_down.pack(pady=5)

        # Nút bấm
        self.btn_start = tk.Button(self.root, text="BẮT ĐẦU", font=("Arial", 12, "bold"), 
                                   bg="#4CAF50", fg="white", width=15, height=2,
                                   command=self.chay_luong_phu)
        self.btn_start.pack(pady=30)

        # Trạng thái
        self.lbl_status = tk.Label(self.root, text="Sẵn sàng", fg="gray", font=("Arial", 10, "italic"))
        self.lbl_status.pack(side="bottom", pady=10)

    def xu_ly_logic(self):
        """Hàm này chạy ngầm để không làm đơ giao diện"""
        # 1. Khóa nút bấm
        self.btn_start.config(state="disabled", bg="gray")
        
        # 2. Đo Ping
        self.lbl_status.config(text="Đang đo Ping...", fg="blue")
        ping_result = core.do_ping() # Gọi hàm từ file logic
        
        if ping_result:
            self.lbl_ping.config(text=f"Ping: {ping_result} ms", fg="black")
        else:
            self.lbl_ping.config(text="Ping: Lỗi", fg="red")

        # 3. Đo Download
        self.lbl_status.config(text="Đang tải dữ liệu...", fg="blue")
        down_result = core.do_download() # Gọi hàm từ file logic
        
        if down_result:
            self.lbl_down.config(text=f"Download: {down_result} Mbps", fg="green")
            self.lbl_status.config(text="Đo hoàn tất!", fg="green")
        else:
            self.lbl_down.config(text="Download: Lỗi", fg="red")
            self.lbl_status.config(text="Kiểm tra thất bại", fg="red")

        # 4. Mở lại nút
        self.btn_start.config(state="normal", bg="#4CAF50")

    def chay_luong_phu(self):
        """Tạo luồng riêng để chạy hàm xử lý"""
        threading.Thread(target=self.xu_ly_logic).start()