import sys
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor

import core as logic_mang

# --- STYLE SHEET ---
STYLESHEET = """
QMainWindow { background-color: #1e1e1e; }
QLabel { color: #ffffff; font-family: 'Segoe UI', sans-serif; }
QFrame#Card { background-color: #2d2d2d; border-radius: 15px; border: 1px solid #3d3d3d; }
QFrame#CardPing { border-left: 5px solid #FF9800; }
QFrame#CardDown { border-left: 5px solid #2196F3; }
QFrame#CardUp { border-left: 5px solid #9C27B0; }

QPushButton#BtnStart {
    background-color: #00C853; color: white; border-radius: 25px; font-weight: bold; font-size: 16px;
}
QPushButton#BtnStart:hover { background-color: #00E676; }
QPushButton#BtnStart:disabled { background-color: #555555; }

QPushButton#BtnCancel {
    background-color: #D32F2F; color: white; border-radius: 25px; font-weight: bold; font-size: 16px;
}
QPushButton#BtnCancel:hover { background-color: #EF5350; }

QProgressBar {
    border: 1px solid #333;
    background-color: #2d2d2d;
    border-radius: 5px;
    height: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #2196F3;
    border-radius: 5px;
}
"""

class MainWindow(QMainWindow):
    # --- KHAI BÁO SIGNALS ---
    sig_update_ping = pyqtSignal(str)
    sig_update_down = pyqtSignal(float)
    sig_update_up = pyqtSignal(float)
    sig_update_sys_monitor = pyqtSignal(float, float)
    sig_finish = pyqtSignal()
    sig_info = pyqtSignal(dict)
    
    # QUAN TRỌNG: Signal riêng cho thanh progress
    sig_update_progress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 SpeedTest Pro")
        self.setFixedSize(450, 700)
        
        self.is_running = False
        self.is_monitoring = False
        self.monitor_core = None

        self.setup_ui()
        self.setup_connections()
        self.setStyleSheet(STYLESHEET)
        
        threading.Thread(target=self.thread_lay_thong_tin, daemon=True).start()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header
        self.lbl_isp = QLabel("Đang tải ISP...")
        self.lbl_isp.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_isp.setStyleSheet("color: #4facfe;")
        self.lbl_isp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_isp)

        self.lbl_ip_loc = QLabel("IP: --- | Location: ---")
        self.lbl_ip_loc.setStyleSheet("color: #aaaaaa;")
        self.lbl_ip_loc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_ip_loc)

        # 2. Cards
        # Ping
        self.card_ping = QFrame()
        self.card_ping.setObjectName("Card")
        self.card_ping.setProperty("class", "CardPing") 
        self.card_ping.setObjectName("CardPing")
        l_ping = QHBoxLayout(self.card_ping)
        l_ping.addWidget(QLabel("PING"))
        self.val_ping = QLabel("--- ms")
        self.val_ping.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.val_ping.setStyleSheet("color: #FF9800;")
        self.val_ping.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_ping.addWidget(self.val_ping)
        main_layout.addWidget(self.card_ping)

        # Down
        self.card_down = QFrame()
        self.card_down.setObjectName("CardDown")
        l_down = QVBoxLayout(self.card_down)
        lbl_d_title = QLabel("DOWNLOAD")
        lbl_d_title.setStyleSheet("color: #2196F3; font-weight: bold;")
        l_down.addWidget(lbl_d_title, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.val_down = QLabel("---")
        self.val_down.setFont(QFont("Segoe UI", 40, QFont.Weight.Bold))
        self.val_down.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        l_down.addWidget(self.val_down)
        l_down.addWidget(QLabel("Mbps", alignment=Qt.AlignmentFlag.AlignHCenter))
        main_layout.addWidget(self.card_down)

        # Up
        self.card_up = QFrame()
        self.card_up.setObjectName("CardUp")
        l_up = QVBoxLayout(self.card_up)
        lbl_u_title = QLabel("UPLOAD")
        lbl_u_title.setStyleSheet("color: #9C27B0; font-weight: bold;")
        l_up.addWidget(lbl_u_title, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.val_up = QLabel("---")
        self.val_up.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.val_up.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        l_up.addWidget(self.val_up)
        l_up.addWidget(QLabel("Mbps", alignment=Qt.AlignmentFlag.AlignHCenter))
        main_layout.addWidget(self.card_up)

        # 3. Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        main_layout.addWidget(self.progress)

        self.lbl_status = QLabel("Sẵn sàng")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(self.lbl_status)

        # 4. Button
        self.btn_action = QPushButton("BẮT ĐẦU ĐO")
        self.btn_action.setObjectName("BtnStart")
        self.btn_action.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action.setFixedHeight(50)
        self.btn_action.clicked.connect(self.on_btn_action_click)
        main_layout.addWidget(self.btn_action)

        main_layout.addStretch()

        # 5. Footer
        self.frame_footer = QFrame()
        self.frame_footer.setStyleSheet("background-color: #151515; border-radius: 10px;")
        l_footer = QVBoxLayout(self.frame_footer)
        h_foot = QHBoxLayout()
        h_foot.addWidget(QLabel("GIÁM SÁT HỆ THỐNG", styleSheet="color: gray; font-weight: bold; font-size: 10px;"))
        self.btn_monitor = QPushButton("BẬT")
        self.btn_monitor.setCheckable(True)
        self.btn_monitor.setFixedSize(50, 20)
        self.btn_monitor.setStyleSheet("QPushButton { background-color: #555; border-radius: 10px; color: white; font-size: 10px;} QPushButton:checked { background-color: #E91E63; }")
        self.btn_monitor.clicked.connect(self.toggle_monitor)
        h_foot.addWidget(self.btn_monitor, alignment=Qt.AlignmentFlag.AlignRight)
        l_footer.addLayout(h_foot)
        h_sys = QHBoxLayout()
        self.sys_down = QLabel("↓ 0.00 MB/s")
        self.sys_down.setStyleSheet("color: #4CAF50; font-family: Consolas; font-size: 14px;")
        self.sys_up = QLabel("↑ 0.00 MB/s")
        self.sys_up.setStyleSheet("color: #FFC107; font-family: Consolas; font-size: 14px;")
        h_sys.addWidget(self.sys_down)
        h_sys.addStretch()
        h_sys.addWidget(self.sys_up)
        l_footer.addLayout(h_sys)
        main_layout.addWidget(self.frame_footer)

    def setup_connections(self):
        self.sig_update_ping.connect(self.val_ping.setText)
        self.sig_update_down.connect(lambda v: self.val_down.setText(f"{v}"))
        self.sig_update_up.connect(lambda v: self.val_up.setText(f"{v}"))
        self.sig_finish.connect(self.on_process_finished)
        self.sig_info.connect(self.update_info_ui)
        self.sig_update_sys_monitor.connect(self.update_sys_ui)
        
        # KẾT NỐI QUAN TRỌNG NHẤT: Signal -> Slot của Progress Bar
        self.sig_update_progress.connect(self.progress.setValue)

    def on_btn_action_click(self):
        if not self.is_running:
            self.start_test()
        else:
            self.cancel_test()

    def start_test(self):
        self.is_running = True
        self.btn_action.setText("HỦY BỎ")
        self.btn_action.setObjectName("BtnCancel")
        self.btn_action.setStyleSheet(STYLESHEET)
        self.val_ping.setText("--- ms")
        self.val_down.setText("---")
        self.val_up.setText("---")
        self.progress.setValue(0)
        logic_mang.reset_trang_thai()
        threading.Thread(target=self.worker_speedtest, daemon=True).start()

    def cancel_test(self):
        self.lbl_status.setText("Đang hủy...")
        self.btn_action.setEnabled(False)
        logic_mang.kich_hoat_lenh_huy()

    def on_process_finished(self):
        self.is_running = False
        self.btn_action.setText("BẮT ĐẦU ĐO")
        self.btn_action.setObjectName("BtnStart")
        self.btn_action.setStyleSheet(STYLESHEET)
        self.btn_action.setEnabled(True)
        if logic_mang.co_lenh_huy:
            self.lbl_status.setText("ĐÃ HỦY ĐO")
            self.lbl_status.setStyleSheet("color: #EF5350; font-style: italic;")
            self.progress.setValue(0)
        else:
            self.lbl_status.setText("HOÀN TẤT!")
            self.lbl_status.setStyleSheet("color: #00C853; font-weight: bold;")
            self.progress.setValue(100)

    # --- WORKER THREAD ---
    def worker_speedtest(self):
        # 0. Giai đoạn Ping (0 -> 15%)
        if not self.check_continue(): return
        self.set_status_safe("Đang đo Ping...", "white")
        
        self.sig_update_progress.emit(5) # Bắn tín hiệu cập nhật
        ping = logic_mang.lay_ping()
        if ping: self.sig_update_ping.emit(f"{ping} ms")
        self.sig_update_progress.emit(15)

        # 1. Giai đoạn Download (15% -> 55%)
        if not self.check_continue(): return
        self.set_status_safe("Đang đo Download...", "#2196F3")
        
        current_prog_down = 15
        def cb_down(val):
            nonlocal current_prog_down
            self.sig_update_down.emit(val)
            # Tăng dần progress bar
            if current_prog_down < 55:
                current_prog_down += 1
                self.sig_update_progress.emit(current_prog_down) # Bắn tín hiệu
        
        final_down = logic_mang.do_download(callback_func=cb_down)
        if final_down: self.sig_update_down.emit(final_down)
        self.sig_update_progress.emit(55)

        # 2. Giai đoạn Upload (55% -> 95%)
        if not self.check_continue(): return
        self.set_status_safe("Đang đo Upload...", "#9C27B0")
        
        current_prog_up = 55
        def cb_up(val):
            nonlocal current_prog_up
            self.sig_update_up.emit(val)
            if current_prog_up < 95:
                current_prog_up += 1
                self.sig_update_progress.emit(current_prog_up) # Bắn tín hiệu

        final_up = logic_mang.do_upload(callback_func=cb_up)
        if final_up: self.sig_update_up.emit(final_up)
        
        # 3. Kết thúc (100%)
        self.sig_update_progress.emit(100)
        self.sig_finish.emit()

    def check_continue(self):
        if logic_mang.co_lenh_huy:
            self.sig_finish.emit()
            return False
        return True

    def set_status_safe(self, text, color):
        # Wrapper để cập nhật text an toàn từ thread
        QTimer.singleShot(0, lambda: self._update_lbl(text, color))

    def _update_lbl(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; font-style: italic;")

    def toggle_monitor(self):
        if self.btn_monitor.isChecked():
            self.btn_monitor.setText("TẮT")
            self.is_monitoring = True
            def cb_mon(down, up): self.sig_update_sys_monitor.emit(down, up)
            self.monitor_core = logic_mang.chay_giam_sat_he_thong(cb_mon)
        else:
            self.btn_monitor.setText("BẬT")
            self.is_monitoring = False
            if self.monitor_core: self.monitor_core.dung_giam_sat()
            self.sys_down.setText("↓ 0.00 MB/s")
            self.sys_up.setText("↑ 0.00 MB/s")

    def update_sys_ui(self, down, up):
        if self.is_monitoring:
            self.sys_down.setText(f"↓ {down:.2f} MB/s")
            self.sys_up.setText(f"↑ {up:.2f} MB/s")

    def thread_lay_thong_tin(self):
        info = logic_mang.lay_thong_tin_ip()
        if info: self.sig_info.emit(info)

    def update_info_ui(self, info):
        self.lbl_isp.setText(info['isp'])
        self.lbl_ip_loc.setText(f"IP: {info['ip']} | {info['city']}, {info['country']}")