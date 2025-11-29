import threading
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal

import core as logic_mang
import database # Import file database mới tạo

from styles import STYLESHEET
from widgets.login_widget import LoginWidget
from widgets.app_widget import AppWidget
from widgets.fade_stacked_widget import FadeStackedWidget


# --- CỬA SỔ CHÍNH (CONTAINER) ---
class MainWindow(QMainWindow):
    # Signals
    sig_update_ping = pyqtSignal(str)
    sig_update_down = pyqtSignal(float)
    sig_update_up = pyqtSignal(float)
    sig_update_sys_monitor = pyqtSignal(float, float)
    sig_finish = pyqtSignal()
    sig_info = pyqtSignal(dict)
    sig_update_progress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpeedTest Pro Ultimate")
        self.setStyleSheet(STYLESHEET)
        self.setFixedWidth(520)
        self.setWindowFlags(Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)

        # Biến tạm lưu kết quả để ghi DB
        self.last_result = {}
        # Danh sách lưu kết quả tạm thời khi chưa đăng nhập
        self.temp_history = []

        self.stack = FadeStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginWidget()
        self.login_screen.sig_login_success.connect(self.handle_login_success)
        self.login_screen.sig_back_requested.connect(self.show_app_screen)
        self.stack.addWidget(self.login_screen)

        self.app_screen = AppWidget()
        # Đưa tham chiếu của danh sách tạm vào AppWidget
        self.app_screen.temp_history_ref = self.temp_history
        self.stack.addWidget(self.app_screen)
        
        self.app_screen.tabs.currentChanged.connect(self.tu_dong_resize_tab)
        
        # Kết nối Signal cho App Screen
        self.setup_connections()

        self.show_app_screen() # Hiển thị màn hình app ngay từ đầu

        # 3. TỰ ĐỘNG CO GIÃN CHIỀU CAO VÀ KHÓA LẠI
        # adjustSize(): Lệnh này ép cửa sổ co lại vừa khít với nội dung bên trong
        self.adjustSize()
        
        # Sau khi co lại xong, ta lấy chiều cao đó khóa cứng luôn
        # Để người dùng không kéo dài xuống dưới được nữa
        self.setFixedSize(self.width(), self.height())

    def show_app_screen(self):
        self.stack.fade_to_widget(self.app_screen)
        threading.Thread(target=self.thread_lay_thong_tin, daemon=True).start()
        self.app_screen.load_history_data()

        self.setMaximumHeight(16777215)
        self.setMinimumHeight(0)
        self.adjustSize()
        self.tu_dong_resize_tab(0)

    def show_login_screen(self):
        self.stack.fade_to_widget(self.login_screen)
        self.setFixedSize(500, 350)
        frame_geo = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geo.moveCenter(screen_center)
        self.move(frame_geo.topLeft())

    def handle_login_success(self, email):
        # Khi đăng nhập xong mới tạo/kết nối DB riêng của user đó
        database.khoi_tao_db(email)
        
        self.app_screen.set_user_email(email)
        
        # Lưu các kết quả đo tạm thời vào DB
        if self.temp_history:
            for result in self.temp_history:
                try:
                    # Sửa lỗi: Truyền tham số đúng theo định dạng của hàm luu_ket_qua
                    database.luu_ket_qua(
                        email=email,
                        ping=result.get('ping', '---'),
                        download=result.get('download', 0.0),
                        upload=result.get('upload', 0.0),
                        isp=result.get('isp', '---'),
                        ip=result.get('ip', '---')
                    )
                except Exception as e:
                    print(f"Lỗi lưu kết quả tạm vào DB: {e}")
            # Xóa lịch sử tạm sau khi đã lưu thành công
            self.temp_history.clear()

        self.show_app_screen()
        self.app_screen.load_history_data() # Tải lại lịch sử sau khi đã thêm

    def tu_dong_resize_tab(self, index):
        """
        index = 0: Tab Đo Tốc Độ
        index = 1: Tab Lịch Sử
        """
        if index == 0:
            # Tab Đo Tốc Độ: Cần Cao và Hẹp (giao diện điện thoại)
            rong = 550
            cao = 750
        else:
            # Tab Lịch Sử: Cần Rộng hơn để hiển thị bảng nhiều cột
            rong = 1000
            cao = 600
            
        # 1. Đặt kích thước cố định mới
        self.setFixedSize(rong, cao)
        
        # 2. (Tùy chọn) Căn giữa lại màn hình 
        # Vì khi resize, cửa sổ hay bị lệch sang một bên, code này giúp nó nhảy về giữa
        frame_geo = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geo.moveCenter(screen_center)
        self.move(frame_geo.topLeft())

    def setup_connections(self):
        # Kết nối các nút bấm trong App Screen với Logic ở Main Window
        self.app_screen.btn_action.clicked.connect(self.on_btn_action_click)
        self.app_screen.btn_monitor.clicked.connect(self.toggle_monitor)
        self.app_screen.btn_show_login.clicked.connect(self.show_login_screen)
        
        # Kết nối Signal cập nhật giao diện
        self.sig_update_ping.connect(self.app_screen.val_ping.setText)
        self.sig_update_down.connect(lambda v: self.app_screen.val_down.setText(f"{v}"))
        self.sig_update_up.connect(lambda v: self.app_screen.val_up.setText(f"{v}"))
        self.sig_update_progress.connect(self.app_screen.progress.setValue)
        self.sig_finish.connect(self.on_process_finished)
        self.sig_info.connect(self.update_info_ui)
        self.sig_update_sys_monitor.connect(self.update_sys_ui)

        self.app_screen.sig_req_logout.connect(self.on_logout)

    # --- LOGIC ĐO (Tương tự cũ, có thêm phần lưu DB) ---
    def on_btn_action_click(self):
        if not self.app_screen.is_running:
            self.start_test()
        else:
            self.cancel_test()

    def start_test(self):
        self.app_screen.is_running = True
        self.app_screen.btn_action.setText("HỦY BỎ")
        self.app_screen.lbl_status.setText("Đang đo...")
        self.app_screen.lbl_status.setStyleSheet("color: orange;")
        self.app_screen.btn_action.setObjectName("BtnCancel")
        self.app_screen.btn_action.setStyleSheet(STYLESHEET)
        self.app_screen.btn_show_login.setEnabled(False)
        self.app_screen.btn_logout.setEnabled(False) # Vô hiệu hóa nút đăng xuất
        
        # Reset UI
        self.app_screen.val_ping.setText("--- ms")
        self.app_screen.val_down.setText("---")
        self.app_screen.val_up.setText("---")
        self.app_screen.progress.setValue(0)
        self.app_screen.lbl_isp.setText("Đang tìm...")
        
        # Reset biến lưu kết quả
        self.last_result = {"ping": "---", "down": 0, "up": 0, "isp": "---", "ip": "---"}

        # Cập nhật lại IP mới nhất trước khi đo
        threading.Thread(target=self.thread_lay_thong_tin, daemon=True).start()
        
        logic_mang.reset_trang_thai()
        threading.Thread(target=self.worker_speedtest, daemon=True).start()

    def cancel_test(self):
        self.app_screen.btn_action.setEnabled(False)
        self.app_screen.lbl_status.setText("Đang hủy...")
        logic_mang.kich_hoat_lenh_huy()

    def worker_speedtest(self):
        try:
            # 1. Ping
            if not self.check_continue(): return
            self.sig_update_progress.emit(5)
            
            ping = logic_mang.lay_ping()
            if ping: 
                self.last_result['ping'] = f"{ping} ms"
                self.sig_update_ping.emit(f"{ping} ms")
            else:
                self.last_result['ping'] = "Lỗi"
                self.sig_update_ping.emit("Lỗi")
                
            self.sig_update_progress.emit(15)

            # 2. Download
            if not self.check_continue(): return
            current_prog_down = 15
            def cb_down(val):
                nonlocal current_prog_down
                self.sig_update_down.emit(float(val)) # Ép kiểu float cho chắc
                if current_prog_down < 55:
                    current_prog_down += 1
                    self.sig_update_progress.emit(current_prog_down)
            
            final_down = logic_mang.do_download(callback_func=cb_down)
            
            # --- SỬA LỖI TẠI ĐÂY ---
            # Nếu final_down là None (lỗi), gán bằng 0.0 để không crash
            if final_down is None:
                final_down = 0.0
            
            self.last_result['down'] = final_down
            self.sig_update_down.emit(float(final_down)) # Luôn gửi số thực
            self.sig_update_progress.emit(55)

            # 3. Upload
            if not self.check_continue(): return
            current_prog_up = 55
            def cb_up(val):
                nonlocal current_prog_up
                self.sig_update_up.emit(float(val))
                if current_prog_up < 95:
                    current_prog_up += 1
                    self.sig_update_progress.emit(current_prog_up)
            
            final_up = logic_mang.do_upload(callback_func=cb_up)
            
            # --- SỬA LỖI TẠI ĐÂY ---
            if final_up is None:
                final_up = 0.0
                
            self.last_result['up'] = final_up
            self.sig_update_up.emit(float(final_up))

            # 4. Lưu Database
            self.sig_update_progress.emit(98)
            if not logic_mang.co_lenh_huy:
                user_email = self.app_screen.current_email
                result_to_save = {
                    'ping': self.last_result.get('ping', '---'),
                    'download': self.last_result.get('down', 0.0),
                    'upload': self.last_result.get('up', 0.0),
                    'isp': self.last_result.get('isp', '---'),
                    'ip': self.last_result.get('ip', '---')
                }
                
                if user_email: # Nếu đã đăng nhập
                    try:
                        database.luu_ket_qua(user_email, **result_to_save)
                    except Exception as e:
                        print(f"Lỗi lưu DB: {e}")
                else: # Nếu chưa đăng nhập (khách)
                    self.temp_history.append(result_to_save)
                    print(f"Lưu tạm kết quả: {result_to_save}")
                    # Tải lại tab lịch sử để hiển thị kết quả tạm mới
                    self.app_screen.load_history_data()

            self.sig_update_progress.emit(100)


        except Exception as e:
            print(f"Lỗi Worker: {e}") # In lỗi ra terminal để debug
            
        finally:
            self.sig_finish.emit() #to always reset UI

    def on_process_finished(self):
        # Đánh dấu là đã dừng chạy
        self.app_screen.is_running = False
        
        # Đổi nút HỦY BỎ (Đỏ) thành BẮT ĐẦU ĐO (Xanh)
        self.app_screen.btn_action.setText("BẮT ĐẦU ĐO")
        self.app_screen.btn_action.setObjectName("BtnStart")
        
        # Dòng này cực quan trọng: Ép giao diện vẽ lại màu xanh ngay lập tức
        self.app_screen.btn_action.setStyleSheet(STYLESHEET) 
        
        # Mở khóa nút bấm
        self.app_screen.btn_action.setEnabled(True)
        
        # Cập nhật dòng trạng thái
        if logic_mang.co_lenh_huy:
            self.app_screen.lbl_status.setText("Đã hủy đo")
            self.app_screen.lbl_status.setStyleSheet("color: red;")
            self.app_screen.progress.setValue(0)
        else:
            self.app_screen.lbl_status.setText("Hoàn tất!")
            self.app_screen.lbl_status.setStyleSheet("color: #4CAF50;")
            # Tải lại bảng lịch sử để hiện kết quả mới vừa đo
            if self.app_screen.current_email:
                self.app_screen.load_history_data()
        
        # Mở khóa lại nút đăng nhập/đăng xuất
        self.app_screen.btn_show_login.setEnabled(True)
        self.app_screen.btn_logout.setEnabled(True)

    def check_continue(self):
        if logic_mang.co_lenh_huy:
            self.sig_finish.emit()
            return False
        return True

    def thread_lay_thong_tin(self):
        info = logic_mang.lay_thong_tin_ip()
        if info: self.sig_info.emit(info)

    def update_info_ui(self, info):
        self.app_screen.lbl_isp.setText(info['isp'])
        self.app_screen.lbl_ip_loc.setText(f"IP: {info['ip']} | {info['city']}")
        self.last_result['isp'] = info['isp']
        self.last_result['ip'] = info['ip']

    def toggle_monitor(self):
        if self.app_screen.btn_monitor.isChecked():
            self.app_screen.btn_monitor.setText("STOP")
            self.app_screen.btn_monitor.setStyleSheet("background-color: #E91E63; color: white; border-radius: 5px")
            def cb_mon(down, up): self.sig_update_sys_monitor.emit(down, up)
            self.app_screen.monitor_core = logic_mang.chay_giam_sat_he_thong(cb_mon)
        else:
            self.app_screen.btn_monitor.setText("MONITOR")
            self.app_screen.btn_monitor.setStyleSheet("background-color: #555; color: white; border-radius: 5px")
            if self.app_screen.monitor_core: self.app_screen.monitor_core.dung_giam_sat()
            self.app_screen.sys_down.setText("↓ 0.0 MB/s")

    def update_sys_ui(self, down, up):
        self.app_screen.sys_down.setText(f"↓ {down:.2f} MB/s")
        self.app_screen.sys_up.setText(f"↑ {up:.2f} MB/s")

    def on_logout(self):
        # 1. Nếu đang đo dở thì hủy ngay
        if self.app_screen.is_running:
            self.cancel_test() 

        # 2. Dọn dẹp form đăng nhập và trạng thái user
        self.login_screen.reset_form()
        self.app_screen.reset_user_state()

        self.app_screen.val_ping.setText("--- ms")
        self.app_screen.val_down.setText("---")
        self.app_screen.val_up.setText("---")
        self.app_screen.progress.setValue(0)
        self.app_screen.lbl_isp.setText("Đang tìm...")
        
        # 3. Chuyển về màn hình App (ở trạng thái khách)
        self.show_app_screen()