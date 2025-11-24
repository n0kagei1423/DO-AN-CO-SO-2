import tkinter as tk
from tkinter import messagebox
import threading
import core as logic_mang

class UngDungSpeedTest:
    def __init__(self, root_window):
        self.root = root_window
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Python Speed Test Pro")
        self.root.geometry("450x550") # Tăng kích thước cửa sổ
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f2f5") # Màu nền xám nhẹ hiện đại

        # --- PHẦN 1: THÔNG TIN MẠNG (Header) ---
        self.frame_info = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ddd")
        self.frame_info.pack(fill="x", padx=15, pady=15)
        
        # Label hiển thị thông tin (Ban đầu để trống)
        self.lbl_isp = tk.Label(self.frame_info, text="ISP: Đang tải...", font=("Arial", 11, "bold"), bg="white", fg="#333")
        self.lbl_isp.pack(pady=5)
        
        self.lbl_ip = tk.Label(self.frame_info, text="IP: ---", font=("Arial", 10), bg="white", fg="#666")
        self.lbl_ip.pack()
        
        self.lbl_loc = tk.Label(self.frame_info, text="Location: ---", font=("Arial", 10), bg="white", fg="#666")
        self.lbl_loc.pack(pady=(0, 10))

        # --- PHẦN 2: KẾT QUẢ ĐO ---
        self.frame_result = tk.Frame(self.root, bg="#f0f2f5")
        self.frame_result.pack(pady=10)

        # Ping
        self.lbl_ping = tk.Label(self.frame_result, text="PING: --- ms", font=("Arial", 12), bg="#f0f2f5", fg="#555")
        self.lbl_ping.pack(pady=5)

        # Download Section
        tk.Label(self.frame_result, text="DOWNLOAD", font=("Arial", 10, "bold"), fg="#aaa", bg="#f0f2f5").pack(pady=(15,0))
        self.lbl_down = tk.Label(self.frame_result, text="---", font=("Helvetica", 36, "bold"), fg="#2196F3", bg="#f0f2f5")
        self.lbl_down.pack()
        tk.Label(self.frame_result, text="Mbps", font=("Arial", 10), bg="#f0f2f5").pack()

        # Upload Section
        tk.Label(self.frame_result, text="UPLOAD", font=("Arial", 10, "bold"), fg="#aaa", bg="#f0f2f5").pack(pady=(15,0))
        self.lbl_up = tk.Label(self.frame_result, text="---", font=("Helvetica", 36, "bold"), fg="#9C27B0", bg="#f0f2f5")
        self.lbl_up.pack()
        tk.Label(self.frame_result, text="Mbps", font=("Arial", 10), bg="#f0f2f5").pack()

        # --- PHẦN 3: NÚT BẤM ---
        self.btn_start = tk.Button(self.root, text="BẮT ĐẦU ĐO", font=("Arial", 12, "bold"), 
                                   bg="#4CAF50", fg="white", width=20, height=2, bd=0,
                                   activebackground="#45a049", cursor="hand2",
                                   command=self.chay_luong_phu)
        self.btn_start.pack(pady=20)

        self.lbl_status = tk.Label(self.root, text="Sẵn sàng", fg="gray", bg="#f0f2f5", font=("Arial", 9, "italic"))
        self.lbl_status.pack(side="bottom", pady=10)

        # Tự động lấy thông tin IP khi mở app
        threading.Thread(target=self.lay_thong_tin_nen).start()

    # --- CÁC HÀM CẬP NHẬT GIAO DIỆN ---
    def lay_thong_tin_nen(self):
        """Chạy ngầm để lấy IP ngay khi mở app"""
        info = logic_mang.lay_thong_tin_ip()
        if info:
            self.lbl_isp.config(text=info['isp'])
            self.lbl_ip.config(text=f"IP: {info['ip']}")
            self.lbl_loc.config(text=f"{info['city']}, {info['country']}")
        else:
            self.lbl_isp.config(text="Không thể lấy thông tin IP")

    def cap_nhat_down(self, toc_do):
        self.lbl_down.config(text=f"{toc_do}")

    def cap_nhat_up(self, toc_do):
        self.lbl_up.config(text=f"{toc_do}")

    def xu_ly_logic(self):
        # Reset giao diện
        self.btn_start.config(state="disabled", bg="#cccccc")
        self.lbl_down.config(text="---", fg="#2196F3")
        self.lbl_up.config(text="---", fg="#9C27B0")
        
        # 1. Ping
        self.lbl_status.config(text="Đang đo độ trễ (Ping)...", fg="#333")
        ping = logic_mang.lay_ping()
        self.lbl_ping.config(text=f"PING: {ping} ms" if ping else "PING: Lỗi")

        # 2. Download
        self.lbl_status.config(text="Đang đo Download...", fg="#2196F3")
        final_down = logic_mang.do_download(callback_func=self.cap_nhat_down)
        if final_down:
            self.lbl_down.config(text=f"{final_down}", fg="#008000") # Xanh lá khi xong
        
        # 3. Upload (Phần mới)
        self.lbl_status.config(text="Đang đo Upload...", fg="#9C27B0")
        final_up = logic_mang.do_upload(callback_func=self.cap_nhat_up)
        if final_up:
            self.lbl_up.config(text=f"{final_up}", fg="#008000") # Xanh lá khi xong

        # Hoàn tất
        self.lbl_status.config(text="Đã hoàn tất kiểm tra!", fg="#008000")
        self.btn_start.config(state="normal", bg="#4CAF50")

    def chay_luong_phu(self):
        threading.Thread(target=self.xu_ly_logic).start()