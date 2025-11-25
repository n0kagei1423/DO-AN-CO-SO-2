import tkinter as tk
import threading
import core as logic_mang

class UngDungSpeedTest:
    def __init__(self, root_window):
        self.root = root_window
        
        # Biến theo dõi trạng thái Monitor (Đang bật hay tắt)
        self.is_monitoring = False
        self.monitor_core = None # Lưu đối tượng xử lý để còn ra lệnh dừng
        
        self.setup_ui()
        
        # LƯU Ý: Đã xóa dòng tự động chạy monitor ở đây

    def setup_ui(self):
        self.root.title("Python Network Monitor")
        self.root.geometry("450x650") # Tăng chiều cao thêm chút nữa chứa nút mới
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f2f5")

        # --- HEADER & BODY (Giữ nguyên như cũ) ---
        self.frame_info = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ddd")
        self.frame_info.pack(fill="x", padx=15, pady=15)
        self.lbl_isp = tk.Label(self.frame_info, text="ISP: Đang tải...", font=("Arial", 11, "bold"), bg="white", fg="#333")
        self.lbl_isp.pack(pady=5)
        self.lbl_ip = tk.Label(self.frame_info, text="IP: ---", font=("Arial", 10), bg="white", fg="#666")
        self.lbl_ip.pack()
        self.lbl_loc = tk.Label(self.frame_info, text="Location: ---", font=("Arial", 10), bg="white", fg="#666")
        self.lbl_loc.pack(pady=(0, 10))

        self.frame_result = tk.Frame(self.root, bg="#f0f2f5")
        self.frame_result.pack(pady=10)
        
        self.lbl_ping = tk.Label(self.frame_result, text="PING: --- ms", font=("Arial", 12), bg="#f0f2f5", fg="#555")
        self.lbl_ping.pack(pady=5)

        tk.Label(self.frame_result, text="DOWNLOAD SPEED", font=("Arial", 10, "bold"), fg="#aaa", bg="#f0f2f5").pack(pady=(10,0))
        self.lbl_down = tk.Label(self.frame_result, text="---", font=("Helvetica", 32, "bold"), fg="#2196F3", bg="#f0f2f5")
        self.lbl_down.pack()
        
        tk.Label(self.frame_result, text="UPLOAD SPEED", font=("Arial", 10, "bold"), fg="#aaa", bg="#f0f2f5").pack(pady=(10,0))
        self.lbl_up = tk.Label(self.frame_result, text="---", font=("Helvetica", 32, "bold"), fg="#9C27B0", bg="#f0f2f5")
        self.lbl_up.pack()

        self.btn_start = tk.Button(self.root, text="BẮT ĐẦU ĐO (SPEEDTEST)", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", width=25, height=2, bd=0, command=self.chay_luong_phu)
        self.btn_start.pack(pady=20)

        self.lbl_status = tk.Label(self.root, text="Sẵn sàng", fg="gray", bg="#f0f2f5", font=("Arial", 9, "italic"))
        self.lbl_status.pack(pady=5)

        # --- PHẦN FOOTER (CÓ SỬA ĐỔI) ---
        self.frame_monitor = tk.Frame(self.root, bg="#333", height=100)
        self.frame_monitor.pack(side="bottom", fill="x")
        
        # Tiêu đề nhỏ
        tk.Label(self.frame_monitor, text="SYSTEM BANDWIDTH MONITOR", font=("Arial", 8, "bold"), fg="#aaa", bg="#333").pack(pady=(10,0))
        
        # Khung số liệu
        f_mon = tk.Frame(self.frame_monitor, bg="#333")
        f_mon.pack(fill="x", pady=5)
        
        self.lbl_sys_down = tk.Label(f_mon, text="↓ --- MB/s", font=("Courier New", 11, "bold"), fg="#4CAF50", bg="#333", width=15)
        self.lbl_sys_down.pack(side="left", expand=True)
        
        self.lbl_sys_up = tk.Label(f_mon, text="↑ --- MB/s", font=("Courier New", 11, "bold"), fg="#FFC107", bg="#333", width=15)
        self.lbl_sys_up.pack(side="left", expand=True)

        # NÚT BẬT/TẮT MONITOR (MỚI)
        self.btn_toggle_mon = tk.Button(self.frame_monitor, text="Bật Giám Sát", font=("Arial", 9), 
                                        bg="#555", fg="white", bd=0, width=15,
                                        command=self.xy_ly_nut_monitor)
        self.btn_toggle_mon.pack(pady=(0, 10))

        # Thread lấy IP chạy ngầm
        threading.Thread(target=self.lay_thong_tin_nen).start()

    # --- LOGIC XỬ LÝ NÚT BẬT/TẮT ---
    def xy_ly_nut_monitor(self):
        if not self.is_monitoring:
            # Nếu đang Tắt -> Bật lên
            self.is_monitoring = True
            self.btn_toggle_mon.config(text="Dừng Giám Sát", bg="#d32f2f") # Đổi màu đỏ
            
            # Gọi hàm bên Logic để chạy luồng
            self.monitor_core = logic_mang.chay_giam_sat_he_thong(self.cap_nhat_bandwidth_he_thong)
        else:
            # Nếu đang Bật -> Tắt đi
            self.is_monitoring = False
            self.btn_toggle_mon.config(text="Bật Giám Sát", bg="#555") # Về màu xám
            
            # Ra lệnh dừng vòng lặp bên logic
            if self.monitor_core:
                self.monitor_core.dung_giam_sat()
            
            # Reset số về 0 cho đẹp
            self.lbl_sys_down.config(text="↓ --- MB/s")
            self.lbl_sys_up.config(text="↑ --- MB/s")

    def cap_nhat_bandwidth_he_thong(self, down_mb, up_mb):
        # Chỉ cập nhật nếu đang bật (đề phòng luồng cũ còn sót lại vài mili giây)
        if self.is_monitoring:
            self.lbl_sys_down.config(text=f"↓ {down_mb:.2f} MB/s")
            self.lbl_sys_up.config(text=f"↑ {up_mb:.2f} MB/s")

    # ... (Các hàm cũ GIỮ NGUYÊN) ...
    def lay_thong_tin_nen(self):
        info = logic_mang.lay_thong_tin_ip()
        if info:
            self.lbl_isp.config(text=info['isp'])
            self.lbl_ip.config(text=f"IP: {info['ip']}")
            self.lbl_loc.config(text=f"{info['city']}, {info['country']}")

    def cap_nhat_down(self, toc_do):
        self.lbl_down.config(text=f"{toc_do}")

    def cap_nhat_up(self, toc_do):
        self.lbl_up.config(text=f"{toc_do}")

    def xu_ly_logic(self):
        self.btn_start.config(state="disabled", bg="#cccccc")
        self.lbl_down.config(text="---", fg="#2196F3")
        self.lbl_up.config(text="---", fg="#9C27B0")
        
        self.lbl_status.config(text="Đang đo độ trễ (Ping)...", fg="#333")
        ping = logic_mang.lay_ping()
        self.lbl_ping.config(text=f"PING: {ping} ms" if ping else "PING: Lỗi")

        self.lbl_status.config(text="Đang đo Download...", fg="#2196F3")
        final_down = logic_mang.do_download(callback_func=self.cap_nhat_down)
        if final_down: self.lbl_down.config(text=f"{final_down}", fg="#008000")
        
        self.lbl_status.config(text="Đang đo Upload...", fg="#9C27B0")
        final_up = logic_mang.do_upload(callback_func=self.cap_nhat_up)
        if final_up: self.lbl_up.config(text=f"{final_up}", fg="#008000")

        self.lbl_status.config(text="Hoàn tất!", fg="#008000")
        self.btn_start.config(state="normal", bg="#4CAF50")

    def chay_luong_phu(self):
        threading.Thread(target=self.xu_ly_logic).start()