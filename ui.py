import customtkinter as ctk
import threading
import core as logic_mang

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UngDungSpeedTest(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpeedTest Pro Ultimate")
        self.geometry("500x700")
        self.resizable(False, False)
        
        # Biến trạng thái
        self.is_monitoring = False
        self.monitor_core = None
        self.dang_do_toc_do = False # Biến kiểm soát xem có đang chạy test hay không
        
        self.setup_ui()
        threading.Thread(target=self.lay_thong_tin_nen).start()

    def setup_ui(self):
        # ... (PHẦN HEADER & BODY & CARD GIỮ NGUYÊN) ...
        # (Để tiết kiệm không gian trả lời, tôi chỉ viết lại phần Nút bấm, 
        # bạn giữ nguyên các phần tạo Label ISP, Ping, Down, Up, Footer nhé)

        # 1. HEADER
        self.frame_info = ctk.CTkFrame(self, corner_radius=15)
        self.frame_info.pack(fill="x", padx=20, pady=20)
        self.lbl_isp = ctk.CTkLabel(self.frame_info, text="Đang tải ISP...", font=("Roboto", 16, "bold"), text_color="#4facfe")
        self.lbl_isp.pack(pady=(15, 0))
        self.lbl_ip_loc = ctk.CTkLabel(self.frame_info, text="IP: --- | Location: ---", font=("Roboto", 12))
        self.lbl_ip_loc.pack(pady=(0, 15))

        # 2. BODY
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_main.pack(fill="both", expand=True, padx=20)
        
        # Ping
        self.card_ping = ctk.CTkFrame(self.frame_main, fg_color="#333333", corner_radius=10)
        self.card_ping.pack(fill="x", pady=5)
        ctk.CTkLabel(self.card_ping, text="PING", font=("Arial", 10, "bold"), text_color="gray").pack(side="left", padx=20, pady=10)
        self.lbl_ping_val = ctk.CTkLabel(self.card_ping, text="--- ms", font=("Roboto", 14, "bold"), text_color="#FF9800")
        self.lbl_ping_val.pack(side="right", padx=20)

        # Download
        self.card_down = ctk.CTkFrame(self.frame_main, corner_radius=15, border_width=2, border_color="#2196F3")
        self.card_down.pack(fill="x", pady=10, ipady=10)
        ctk.CTkLabel(self.card_down, text="DOWNLOAD", font=("Arial", 12, "bold"), text_color="#2196F3").pack(pady=(10,0))
        self.lbl_down = ctk.CTkLabel(self.card_down, text="---", font=("Roboto", 48, "bold"), text_color="white")
        self.lbl_down.pack()
        ctk.CTkLabel(self.card_down, text="Mbps", text_color="gray").pack(pady=(0,10))

        # Upload
        self.card_up = ctk.CTkFrame(self.frame_main, corner_radius=15, border_width=2, border_color="#9C27B0")
        self.card_up.pack(fill="x", pady=5, ipady=5)
        ctk.CTkLabel(self.card_up, text="UPLOAD", font=("Arial", 12, "bold"), text_color="#9C27B0").pack(pady=(5,0))
        self.lbl_up = ctk.CTkLabel(self.card_up, text="---", font=("Roboto", 36, "bold"), text_color="white")
        self.lbl_up.pack()
        ctk.CTkLabel(self.card_up, text="Mbps", text_color="gray").pack(pady=(0,5))

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self, height=10, corner_radius=5)
        self.progress_bar.pack(fill="x", padx=40, pady=(20, 10))
        self.progress_bar.set(0)
        
        self.lbl_status = ctk.CTkLabel(self, text="Sẵn sàng", font=("Arial", 12, "italic"), text_color="gray")
        self.lbl_status.pack(pady=5)

        # --- NÚT BẤM (QUAN TRỌNG) ---
        # Chúng ta dùng 1 nút duy nhất nhưng đổi màu và chức năng
        self.btn_action = ctk.CTkButton(self, text="BẮT ĐẦU ĐO", font=("Roboto", 16, "bold"), 
                                       height=50, corner_radius=25, 
                                       fg_color="#00C853", hover_color="#009624",
                                       command=self.xu_ly_nut_bat_dau)
        self.btn_action.pack(padx=20, pady=10, fill="x")

        # Footer Monitor (Giữ nguyên)
        self.frame_footer = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.frame_footer.pack(side="bottom", fill="x", ipady=10)
        ctk.CTkLabel(self.frame_footer, text="GIÁM SÁT HỆ THỐNG", font=("Arial", 10, "bold"), text_color="gray").pack(pady=5)
        self.frame_footer_grid = ctk.CTkFrame(self.frame_footer, fg_color="transparent")
        self.frame_footer_grid.pack(fill="x", padx=20)
        self.lbl_sys_down = ctk.CTkLabel(self.frame_footer_grid, text="↓ 0.00 MB/s", font=("Consolas", 14), text_color="#4CAF50")
        self.lbl_sys_down.pack(side="left", padx=20)
        self.switch_monitor = ctk.CTkSwitch(self.frame_footer_grid, text="BẬT", command=self.xy_ly_switch_monitor, progress_color="#E91E63")
        self.switch_monitor.pack(side="right")
        self.lbl_sys_up = ctk.CTkLabel(self.frame_footer_grid, text="↑ 0.00 MB/s", font=("Consolas", 14), text_color="#FFC107")
        self.lbl_sys_up.pack(side="right", padx=20)

    # --- LOGIC NÚT BẤM 2 CHIỀU ---
    def xu_ly_nut_bat_dau(self):
        if not self.dang_do_toc_do:
            # 1. NẾU CHƯA CHẠY -> BẮT ĐẦU CHẠY
            self.dang_do_toc_do = True
            
            # Đổi giao diện sang trạng thái "Đang chạy"
            self.btn_action.configure(text="HỦY BỎ", fg_color="#D32F2F", hover_color="#B71C1C")
            
            # Reset số liệu
            self.lbl_down.configure(text="---")
            self.lbl_up.configure(text="---")
            self.lbl_ping_val.configure(text="--- ms")
            self.progress_bar.set(0)
            
            # Reset logic
            logic_mang.reset_trang_thai()
            
            # Chạy luồng đo
            threading.Thread(target=self.luong_do_toc_do).start()
            
        else:
            # 2. NẾU ĐANG CHẠY -> BẤM THÌ HỦY
            self.lbl_status.configure(text="Đang hủy...", text_color="red")
            self.btn_action.configure(state="disabled") # Khóa nút để tránh spam
            
            # Gửi lệnh hủy sang logic
            logic_mang.kich_hoat_lenh_huy()

    def luong_do_toc_do(self):
        # --- QUÁ TRÌNH ĐO ---
        
        # 1. Ping
        if not self.kiem_tra_huy(): return
        self.lbl_status.configure(text="Đang đo độ trễ (Ping)...", text_color="white")
        ping = logic_mang.lay_ping()
        
        if ping is not None:
            self.lbl_ping_val.configure(text=f"{ping} ms")
        self.progress_bar.set(0.2)

        # 2. Download
        if not self.kiem_tra_huy(): return
        self.lbl_status.configure(text="Đang đo Download...", text_color="#2196F3")
        final_down = logic_mang.do_download(callback_func=self.cap_nhat_down)
        
        if final_down is not None:
             self.lbl_down.configure(text=f"{final_down}")
        self.progress_bar.set(0.5)

        # 3. Upload
        if not self.kiem_tra_huy(): return
        self.lbl_status.configure(text="Đang đo Upload...", text_color="#9C27B0")
        final_up = logic_mang.do_upload(callback_func=self.cap_nhat_up)
        
        if final_up is not None:
            self.lbl_up.configure(text=f"{final_up}")
        self.progress_bar.set(1.0)

        # --- KẾT THÚC ---
        self.dang_do_toc_do = False
        
        # Kiểm tra xem kết thúc do xong hay do hủy
        if logic_mang.co_lenh_huy:
            self.lbl_status.configure(text="ĐÃ HỦY ĐO", text_color="red")
            self.progress_bar.set(0)
        else:
            self.lbl_status.configure(text="HOÀN TẤT!", text_color="#00C853")

        # Khôi phục nút bấm
        self.btn_action.configure(state="normal", text="BẮT ĐẦU ĐO", fg_color="#00C853", hover_color="#009624")

    def kiem_tra_huy(self):
        """Hàm phụ trợ để check xem user có bấm hủy không"""
        if logic_mang.co_lenh_huy:
            self.dang_do_toc_do = False
            self.lbl_status.configure(text="ĐÃ HỦY ĐO", text_color="red")
            self.btn_action.configure(state="normal", text="BẮT ĐẦU ĐO", fg_color="#00C853", hover_color="#009624")
            self.progress_bar.set(0)
            return False # Báo hiệu ngừng chạy
        return True # Báo hiệu chạy tiếp

    # --- CÁC HÀM CŨ GIỮ NGUYÊN ---
    def lay_thong_tin_nen(self):
        info = logic_mang.lay_thong_tin_ip()
        if info:
            self.lbl_isp.configure(text=info['isp'])
            self.lbl_ip_loc.configure(text=f"IP: {info['ip']}  |  {info['city']}, {info['country']}")

    def cap_nhat_down(self, toc_do):
        self.lbl_down.configure(text=f"{toc_do}")
        self.progress_bar.set(0.3 + (toc_do % 10)/50) # Hiệu ứng nhúc nhích nhẹ

    def cap_nhat_up(self, toc_do):
        self.lbl_up.configure(text=f"{toc_do}")
        self.progress_bar.set(0.6 + (toc_do % 10)/50)

    def xy_ly_switch_monitor(self):
        if self.switch_monitor.get() == 1:
            self.is_monitoring = True
            self.monitor_core = logic_mang.chay_giam_sat_he_thong(self.cap_nhat_bandwidth_he_thong)
        else:
            self.is_monitoring = False
            if self.monitor_core: self.monitor_core.dung_giam_sat()
            self.lbl_sys_down.configure(text="↓ 0.00 MB/s")
            self.lbl_sys_up.configure(text="↑ 0.00 MB/s")

    def cap_nhat_bandwidth_he_thong(self, down_mb, up_mb):
        if self.is_monitoring:
            self.lbl_sys_down.configure(text=f"↓ {down_mb:.2f} MB/s")
            self.lbl_sys_up.configure(text=f"↑ {up_mb:.2f} MB/s")