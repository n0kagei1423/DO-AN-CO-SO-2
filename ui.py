import sys
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QProgressBar,
                             QStackedWidget, QLineEdit, QMessageBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor, QIcon

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtWidgets import QGraphicsOpacityEffect

import core as logic_mang
import database # Import file database mới tạo

from utils import otp as email_service  # Import module otp từ utils

# --- STYLE SHEET ---
STYLESHEET = """
QMainWindow { background-color: #1e1e1e; }
QLabel { color: #ffffff; font-family: 'Segoe UI', sans-serif; }
QLineEdit { 
    padding: 10px; border-radius: 5px; border: 1px solid #555; 
    background-color: #2d2d2d; color: white; font-size: 14px;
}
QTableWidget {
    background-color: #2d2d2d; color: white; gridline-color: #444; border: none;
}
QHeaderView::section {
    background-color: #333; color: white; padding: 5px; border: 1px solid #444;
}
QTabWidget::pane { border: 1px solid #444; }
QTabBar::tab {
    background: #333; color: white; padding: 10px 20px;
}
QTabBar::tab:selected {
    background: #2196F3; font-weight: bold;
}
/* Các style cũ giữ nguyên */
QFrame#Card { background-color: #2d2d2d; border-radius: 15px; border: 1px solid #3d3d3d; }
QFrame#CardPing { border-left: 5px solid #FF9800; }
QFrame#CardDown { border-left: 5px solid #2196F3; }
QFrame#CardUp { border-left: 5px solid #9C27B0; }
QPushButton#BtnStart { background-color: #00C853; color: white; border-radius: 25px; font-weight: bold; font-size: 16px; }
QPushButton#BtnStart:hover { background-color: #00E676; }
QPushButton#BtnCancel { background-color: #D32F2F; color: white; border-radius: 25px; font-weight: bold; font-size: 16px; }
QProgressBar { border: 1px solid #333; background-color: #2d2d2d; border-radius: 5px; height: 10px; text-align: center; }
QProgressBar::chunk { background-color: #2196F3; border-radius: 5px; }
"""

# --- MÀN HÌNH LOGIN ---
class LoginWidget(QWidget):
    sig_login_success = pyqtSignal(str) # Tín hiệu báo đăng nhập thành công

    # Tín hiệu báo kết quả gửi mail (Thành công/Thất bại, Lời nhắn)
    # Đây là cầu nối giúp luồng phụ báo cáo về mà không làm treo máy
    sig_gui_mail_xong = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Logo/Title
        lbl_title = QLabel("SPEEDTEST PRO")
        lbl_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Input Email
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Nhập Email của bạn...")
        self.txt_email.setFixedWidth(300)
        layout.addWidget(self.txt_email)

        # Nút lấy OTP
        self.btn_get_otp = QPushButton("Gửi mã OTP")
        self.btn_get_otp.setFixedWidth(300)
        self.btn_get_otp.setFixedHeight(40)
        self.btn_get_otp.setStyleSheet("background-color: #2196F3; color: white; border-radius: 5px; font-weight: bold;")
        self.btn_get_otp.clicked.connect(self.gui_otp)
        layout.addWidget(self.btn_get_otp)

        # Input OTP (Ẩn lúc đầu)
        self.txt_otp = QLineEdit()
        self.txt_otp.setPlaceholderText("Nhập mã 6 số...")
        self.txt_otp.setFixedWidth(300)
        self.txt_otp.setVisible(False)
        layout.addWidget(self.txt_otp)

        # Nút Đăng nhập (Ẩn lúc đầu)
        self.btn_login = QPushButton("Xác nhận Đăng nhập")
        self.btn_login.setFixedWidth(300)
        self.btn_login.setFixedHeight(40)
        self.btn_login.setStyleSheet("background-color: #00C853; color: white; border-radius: 5px; font-weight: bold;")
        self.btn_login.setVisible(False)
        self.btn_login.clicked.connect(self.xac_thuc_otp)
        layout.addWidget(self.btn_login)

        # --- KẾT NỐI TÍN HIỆU ---
        # Khi tín hiệu "Gửi xong" phát ra -> Chạy hàm "xu_ly_ket_qua"
        self.sig_gui_mail_xong.connect(self.xu_ly_ket_qua_gui_mail)

        self.current_otp = None

        # Thêm timer để đếm ngược
        self.timer_countdown = QTimer()
        self.timer_countdown.timeout.connect(self.cap_nhat_dem_nguoc)
        self.thoi_gian_cho = 15

    def gui_otp(self):
        email = self.txt_email.text()
        if "@" not in email:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Email hợp lệ!")
            return
        
        # GỌI TỪ FILE MỚI TRONG THƯ MỤC UTIL
        self.current_otp = email_service.sinh_ma_otp()
        
        # 2. Khóa giao diện lại để báo đang xử lý
        self.btn_get_otp.setText("Đang gửi OTP...")
        self.btn_get_otp.setEnabled(False) # Khóa nút không cho bấm nữa
        self.txt_email.setEnabled(False)   # Khóa ô nhập email
        
        threading.Thread(target=self.luong_gui_mail, args=(email, self.current_otp)).start()

    def luong_gui_mail(self, email, otp):
        """Hàm này chạy ngầm, tuyệt đối không đụng vào UI (MessageBox, setText...)"""
        try:
            # Gửi mail (Giả lập hoặc thật tùy file util của bạn)
            ket_qua = email_service.gui_otp_qua_email(email, otp)
            
            if ket_qua:
                # Nếu gửi được -> Bắn tín hiệu True
                self.sig_gui_mail_xong.emit(True, f"Đã gửi mã tới {email}")
            else:
                # Nếu lỗi -> Bắn tín hiệu False
                self.sig_gui_mail_xong.emit(False, "Gửi thất bại. Kiểm tra kết nối.")
                
        except Exception as e:
            self.sig_gui_mail_xong.emit(False, str(e))

    def xu_ly_ket_qua_gui_mail(self, thanh_cong, loi_nhan):
        """Hàm này chạy ở Luồng Chính -> Được phép vẽ giao diện"""
        
        # Mở khóa lại nút gửi (để lỡ sai thì bấm lại)
        self.btn_get_otp.setText("Gửi lại OTP")
        self.btn_get_otp.setEnabled(True)
        self.txt_email.setEnabled(True)
        
        if thanh_cong:
            # Hiện thông báo thành công
            QMessageBox.information(self, "Thành công", loi_nhan)
            # Hiện ô nhập OTP
            self.txt_otp.setVisible(True)
            self.btn_login.setVisible(True)
            self.txt_otp.setFocus() # Đưa con trỏ chuột vào ô nhập OTP luôn cho tiện

            # --- BẮT ĐẦU ĐẾM NGƯỢC ---
            self.thoi_gian_cho = 15
            self.btn_get_otp.setEnabled(False) # Khóa nút
            self.btn_get_otp.setStyleSheet("background-color: gray; color: white; border-radius: 5px; font-weight: bold;")
            self.timer_countdown.start(1000) # Cứ 1 giây gọi hàm 1 lần
        else:
            # Hiện thông báo lỗi
            QMessageBox.critical(self, "Lỗi", loi_nhan)
            self.btn_get_otp.setText("Gửi mã OTP")
            self.btn_get_otp.setEnabled(True)
            self.btn_get_otp.setStyleSheet("background-color: #2196F3; color: white; border-radius: 5px; font-weight: bold;")
            self.txt_email.setEnabled(True)

    def xac_thuc_otp(self):
        otp_nhap = self.txt_otp.text().strip()
        if otp_nhap == self.current_otp:
            self.sig_login_success.emit(self.txt_email.text())
        else:
            QMessageBox.critical(self, "Sai mã", "Mã OTP không chính xác!")

    # --- HÀM MỚI: CẬP NHẬT SỐ GIÂY TRÊN NÚT ---
    def cap_nhat_dem_nguoc(self):
        self.thoi_gian_cho -= 1
        self.btn_get_otp.setText(f"Gửi lại OTP ({self.thoi_gian_cho}s)")
        self.btn_get_otp.setStyleSheet("background-color: gray; color: white; border-radius: 5px; font-weight: bold;")

        
        if self.thoi_gian_cho <= 0:
            self.timer_countdown.stop()
            self.btn_get_otp.setText("Gửi lại OTP")
            self.btn_get_otp.setStyleSheet("background-color: #2196F3; color: white; border-radius: 5px; font-weight: bold;")
            self.btn_get_otp.setEnabled(True)

    def reset_form(self):
        """Xóa trắng form đăng nhập để đón người mới"""
        self.txt_email.clear()
        self.txt_otp.clear()
        self.txt_otp.setVisible(False)
        self.btn_login.setVisible(False)
        self.btn_get_otp.setEnabled(True)
        self.btn_get_otp.setText("Gửi mã OTP")
        self.current_otp = None

# --- MÀN HÌNH CHÍNH (APP) ---
class AppWidget(QWidget):
    sig_req_logout = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.layout_main.addWidget(self.tabs)

        # Tab 1: Đo tốc độ
        self.tab_speed = QWidget()
        self.setup_tab_speed()
        self.tabs.addTab(self.tab_speed, "Đo Tốc Độ")

        # Tab 2: Lịch sử
        self.tab_history = QWidget()
        self.setup_tab_history()
        self.tabs.addTab(self.tab_history, "Lịch Sử Đo")
        
        # Biến Logic
        self.is_running = False
        self.monitor_core = None
        self.current_email = "" # Lưu email người dùng đang đăng nhập

    def setup_tab_speed(self):
        layout = QVBoxLayout(self.tab_speed)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header Info
        header_user_layout = QHBoxLayout()

        self.lbl_user = QLabel("Xin chào: ---")
        self.lbl_user.setStyleSheet("color: #4facfe; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_user)

        header_user_layout.addStretch()

        # Nút Đăng xuất nhỏ gọn màu đỏ
        self.btn_logout = QPushButton("Đăng xuất")
        self.btn_logout.setFixedSize(80, 25)
        self.btn_logout.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_logout.setStyleSheet("""
            QPushButton { background-color: #333; color: #ff5252; border: 1px solid #ff5252; border-radius: 5px; font-weight: bold; font-size: 11px;}
            QPushButton:hover { background-color: #ff5252; color: white; }
        """)
        # Kết nối nút bấm với tín hiệu logout
        self.btn_logout.clicked.connect(self.sig_req_logout.emit)
        
        header_user_layout.addWidget(self.btn_logout)
        
        # Thêm layout ngang này vào layout chính
        layout.addLayout(header_user_layout)

        self.lbl_isp = QLabel("Đang tải ISP...")
        self.lbl_isp.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_isp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_isp)

        self.lbl_ip_loc = QLabel("IP: --- | Location: ---")
        self.lbl_ip_loc.setStyleSheet("color: #aaaaaa;")
        self.lbl_ip_loc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_ip_loc)

        # 2. Cards Display
        # -- Ping --
        self.card_ping = QFrame()
        self.card_ping.setObjectName("Card"); self.card_ping.setProperty("class", "CardPing"); self.card_ping.setObjectName("CardPing")
        l_ping = QHBoxLayout(self.card_ping)
        l_ping.addWidget(QLabel("PING"))
        self.val_ping = QLabel("--- ms")
        self.val_ping.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 14px")
        l_ping.addWidget(self.val_ping, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.card_ping)

        # -- Download --
        self.card_down = QFrame()
        self.card_down.setObjectName("CardDown")
        l_down = QVBoxLayout(self.card_down)
        l_down.addWidget(QLabel("DOWNLOAD", styleSheet="color: #2196F3; font-weight: bold;"), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.val_down = QLabel("---")
        self.val_down.setFont(QFont("Segoe UI", 40, QFont.Weight.Bold))
        l_down.addWidget(self.val_down, alignment=Qt.AlignmentFlag.AlignHCenter)
        l_down.addWidget(QLabel("Mbps"), alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.card_down)

        # -- Upload --
        self.card_up = QFrame()
        self.card_up.setObjectName("CardUp")
        l_up = QVBoxLayout(self.card_up)
        l_up.addWidget(QLabel("UPLOAD", styleSheet="color: #9C27B0; font-weight: bold;"), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.val_up = QLabel("---")
        self.val_up.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        l_up.addWidget(self.val_up, alignment=Qt.AlignmentFlag.AlignHCenter)
        l_up.addWidget(QLabel("Mbps"), alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.card_up)

        # 3. Progress Bar & Status
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("Sẵn sàng")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # 4. Main Button
        self.btn_action = QPushButton("BẮT ĐẦU ĐO")
        self.btn_action.setObjectName("BtnStart")
        self.btn_action.setFixedHeight(50)
        self.btn_action.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.btn_action)

        layout.addStretch()

        # 5. Footer Monitor (Giản lược hiển thị)
        frame_footer = QFrame()
        frame_footer.setStyleSheet("background-color: #151515; border-radius: 10px;")
        l_foot = QHBoxLayout(frame_footer)
        
        l_foot.addWidget(QLabel("System: ", styleSheet="color: gray"))
        self.sys_down = QLabel("↓ 0.0 MB/s", styleSheet="color: #4CAF50; font-family: Consolas")
        l_foot.addWidget(self.sys_down)
        self.sys_up = QLabel("↑ 0.0 MB/s", styleSheet="color: #FFC107; font-family: Consolas")
        l_foot.addWidget(self.sys_up)
        
        l_foot.addStretch()
        
        self.btn_monitor = QPushButton("MONITOR")
        self.btn_monitor.setCheckable(True)
        self.btn_monitor.setFixedSize(60, 20)
        self.btn_monitor.setStyleSheet("""
            QPushButton { background-color: #555; color: white; border-radius: 5px; font-size: 10px; }
            QPushButton:checked { background-color: #E91E63; }
        """)
        l_foot.addWidget(self.btn_monitor)
        
        layout.addWidget(frame_footer)

    def setup_tab_history(self):
        layout = QVBoxLayout(self.tab_history)
        
        # Bảng hiển thị (6 cột)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Thời gian", "Ping", "Down", "Up", "Mạng"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Ẩn cột dọc (số thứ tự mặc định)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Không cho sửa
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Chọn cả hàng
        layout.addWidget(self.table)
        
        # Nút làm mới
        btn_refresh = QPushButton("Làm mới danh sách")
        btn_refresh.clicked.connect(self.load_history_data)
        btn_refresh.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        layout.addWidget(btn_refresh)

        self.adjustSize()

    def load_history_data(self):
        """Logic nạp dữ liệu từ DB riêng của user"""
        if not self.current_email:
            return 
            
        # Gọi hàm lấy lịch sử với tham số email (để tìm đúng file db)
        data = database.lay_lich_su(self.current_email)
        
        self.table.setRowCount(0) # Xóa dữ liệu cũ trên bảng
        
        for row_number, row_data in enumerate(data):
            self.table.insertRow(row_number)
            
            # CẤU TRÚC ROW_DATA TỪ DB RIÊNG (Không có cột email):
            # (id, thoi_gian, ping, download, upload, isp, ip)
            # Index: 0, 1, 2, 3, 4, 5, 6
            
            display_data = [
                row_data[0], # ID
                row_data[1], # Thời gian
                row_data[2], # Ping
                row_data[3], # Down
                row_data[4], # Up
                row_data[5]  # ISP
            ]
            
            for column_number, cell_data in enumerate(display_data):
                item = QTableWidgetItem(str(cell_data))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_number, column_number, item)

    def set_user_email(self, email):
        """Hàm này được gọi từ MainWindow sau khi Login thành công"""
        self.current_email = email
        self.lbl_user.setText(f"User: {email}")
        # Tự động tải lịch sử của user này
        self.load_history_data()

class FadeStackedWidget(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.duration = 500  # Thời gian hiệu ứng (ms)
        self.easing_curve = QEasingCurve.Type.InOutQuad # Kiểu chuyển động mượt

    def fade_to_widget(self, widget):
        """Hàm chuyển trang có hiệu ứng Fade"""
        if self.currentWidget() == widget:
            return

        # 1. Chuẩn bị widget mới (Set độ trong suốt = 0 để ẩn nó đi)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0)
        
        # 2. Chuyển stack sang widget mới ngay lập tức
        self.setCurrentWidget(widget)
        
        # 3. Tạo Animation: Tăng độ rõ từ 0 lên 1
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(self.duration)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(self.easing_curve)
        
        # 4. Khi chạy xong thì xóa hiệu ứng opacity để tiết kiệm ram
        self.anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        
        self.anim.start()

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

        self.stack = FadeStackedWidget() 
        self.setCentralWidget(self.stack)

        self.login_screen = LoginWidget()
        self.login_screen.sig_login_success.connect(self.on_login_success)
        self.stack.addWidget(self.login_screen)

        self.app_screen = AppWidget()
        self.stack.addWidget(self.app_screen)
        
        self.app_screen.tabs.currentChanged.connect(self.tu_dong_resize_tab)
        
        # Kết nối Signal cho App Screen
        self.setup_connections()
        
        # Biến tạm lưu kết quả để ghi DB
        self.last_result = {} 

        # 3. TỰ ĐỘNG CO GIÃN CHIỀU CAO VÀ KHÓA LẠI
        # adjustSize(): Lệnh này ép cửa sổ co lại vừa khít với nội dung bên trong
        self.adjustSize()
        
        # Sau khi co lại xong, ta lấy chiều cao đó khóa cứng luôn
        # Để người dùng không kéo dài xuống dưới được nữa
        self.setFixedSize(self.width(), self.height())

    def on_login_success(self, email):
        # Khi đăng nhập xong mới tạo/kết nối DB riêng của user đó
        database.khoi_tao_db(email) 
        
        self.app_screen.set_user_email(email)
        self.stack.fade_to_widget(self.app_screen)
        threading.Thread(target=self.thread_lay_thong_tin, daemon=True).start()
        self.app_screen.load_history_data()

        # Mở khóa chiều cao tạm thời
        self.setMaximumHeight(16777215) 
        self.setMinimumHeight(0)
        
        # Yêu cầu tính toán lại kích thước cho vừa với màn hình App (nhiều nút hơn)
        self.adjustSize()

        self.tu_dong_resize_tab(0)

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
        
        # Reset UI
        self.app_screen.val_ping.setText("--- ms")
        self.app_screen.val_down.setText("---")
        self.app_screen.val_up.setText("---")
        self.app_screen.progress.setValue(0)
        self.app_screen.lbl_isp.setText("Đang đo...")
        
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
                try:
                    user_email = self.app_screen.current_email
                    database.luu_ket_qua(
                        user_email,
                        self.last_result.get('ping', '---'),
                        self.last_result.get('down', 0.0),
                        self.last_result.get('up', 0.0),
                        self.last_result.get('isp', '---'),
                        self.last_result.get('ip', '---')
                    )
                except Exception as e:
                    print(f"Lỗi lưu DB: {e}")

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
            self.app_screen.load_history_data()

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
            
        # 2. Xóa thông tin user hiện tại
        self.app_screen.current_email = ""
        self.app_screen.lbl_user.setText("Xin chào: ---")
        
        # 3. Dọn dẹp form đăng nhập cho sạch sẽ
        self.login_screen.reset_form()
        
        # 4. Chuyển màn hình về Login (có hiệu ứng Fade nếu bạn dùng FadeStackedWidget)
        # Nếu dùng QStackedWidget thường thì là: self.stack.setCurrentWidget(self.login_screen)
        self.stack.fade_to_widget(self.login_screen)
            
        # 5. Resize cửa sổ về kích thước nhỏ (cho màn hình Login)
        self.setFixedSize(500, 350)
        
        # Căn giữa lại màn hình cho đẹp
        frame_geo = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geo.moveCenter(screen_center)
        self.move(frame_geo.topLeft())