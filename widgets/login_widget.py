import threading
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

import utils.otp as email_service  # Import core.py và đặt bí danh là email_service

# --- MÀN HÌNH LOGIN ---
class LoginWidget(QWidget):
    sig_login_success = pyqtSignal(str) # Tín hiệu báo đăng nhập thành công
    sig_back_requested = pyqtSignal() # Tín hiệu yêu cầu quay lại

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

        # Nút Quay lại màn hình chính (hiển thị ngay từ đầu)
        self.btn_back_main = QPushButton("Quay lại")
        self.btn_back_main.setFixedWidth(300)
        self.btn_back_main.setFixedHeight(40)
        self.btn_back_main.setStyleSheet("background-color: #757575; color: white; border-radius: 5px;")
        self.btn_back_main.clicked.connect(self.sig_back_requested.emit)
        layout.addWidget(self.btn_back_main)

        # Input OTP (Ẩn lúc đầu)
        self.txt_otp = QLineEdit()
        self.txt_otp.setPlaceholderText("Nhập mã 6 số...")
        self.txt_otp.setFixedWidth(300)
        self.txt_otp.setVisible(False)
        layout.addWidget(self.txt_otp)

        # Layout cho các nút bên dưới
        button_layout = QHBoxLayout()

        # Nút Đăng nhập (Ẩn lúc đầu)
        self.btn_login = QPushButton("Xác nhận Đăng nhập")
        self.btn_login.setFixedHeight(40)
        self.btn_login.setStyleSheet("background-color: #00C853; color: white; border-radius: 5px; font-weight: bold;")
        self.btn_login.setVisible(False)
        self.btn_login.clicked.connect(self.xac_thuc_otp)
        button_layout.addWidget(self.btn_login)

        # Nút Quay lại (để hủy nhập OTP, ẩn lúc đầu)
        self.btn_back = QPushButton("Quay lại")
        self.btn_back.setFixedHeight(40)
        self.btn_back.setStyleSheet("background-color: #757575; color: white; border-radius: 5px;")
        self.btn_back.setVisible(False)
        self.btn_back.clicked.connect(self.sig_back_requested.emit)
        button_layout.addWidget(self.btn_back)

        layout.addLayout(button_layout)

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
            self.btn_back.setVisible(True)
            self.btn_back_main.setVisible(False) # Ẩn nút quay lại chính
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
        self.btn_back.setVisible(False)
        self.btn_back_main.setVisible(True) # Hiện lại nút quay lại chính
        self.btn_get_otp.setEnabled(True)
        self.btn_get_otp.setText("Gửi mã OTP")
        self.current_otp = None