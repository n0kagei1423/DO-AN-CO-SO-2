import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QProgressBar, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

import database

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
        # Tham chiếu đến danh sách lịch sử tạm thời của MainWindow
        self.temp_history_ref = []

    def setup_tab_speed(self):
        layout = QVBoxLayout(self.tab_speed)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Header Info
        header_user_layout = QHBoxLayout()
        
        # Nút đăng nhập, sẽ được ẩn khi đã đăng nhập
        self.btn_show_login = QPushButton("Đăng nhập")
        self.btn_show_login.setFixedSize(100, 30)
        self.btn_show_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_show_login.setStyleSheet("background-color: #2196F3; color: white; border-radius: 5px; font-weight: bold;")
        header_user_layout.addWidget(self.btn_show_login)
        
        # Label hiển thị email, sẽ được ẩn khi chưa đăng nhập
        self.lbl_user = QLabel("Xin chào: ---")
        self.lbl_user.setStyleSheet("color: #4facfe; font-weight: bold; font-size: 14px;")
        self.lbl_user.setVisible(False) # Ẩn ban đầu
        header_user_layout.addWidget(self.lbl_user)

        header_user_layout.addStretch()

        self.btn_logout = QPushButton("Đăng xuất")
        self.btn_logout.setFixedSize(80, 25)
        self.btn_logout.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_logout.setStyleSheet("""
            QPushButton { background-color: #333; color: #ff5252; border: 1px solid #ff5252; border-radius: 5px; font-weight: bold; font-size: 11px;}
            QPushButton:hover { background-color: #ff5252; color: white; }
        """)
        self.btn_logout.clicked.connect(self.sig_req_logout.emit)
        self.btn_logout.setVisible(False) # Ẩn ban đầu
        
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
        self.table.setRowCount(0) # Xóa dữ liệu cũ trên bảng
        
        if self.current_email:
            # --- Chế độ đã đăng nhập: Lấy từ DB ---
            data = database.lay_lich_su(self.current_email)
            for row_number, row_data in enumerate(data):
                self.table.insertRow(row_number)
                # Cấu trúc từ DB: (id, thoi_gian, ping, download, upload, isp, ip)
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
        else:
            # --- Chế độ khách: Lấy từ danh sách tạm ---
            # Đảo ngược danh sách để kết quả mới nhất hiện lên đầu
            temp_data_reversed = reversed(self.temp_history_ref)
            for row_number, row_data in enumerate(temp_data_reversed):
                thoi_gian = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.table.insertRow(row_number)
                # Cấu trúc từ temp_history: dict {'ping': ..., 'download': ...}
                display_data = [
                    "Tạm", # ID
                    thoi_gian, # Thời gian
                    row_data.get('ping', '---'),
                    row_data.get('download', 0.0),
                    row_data.get('upload', 0.0),
                    row_data.get('isp', '---')
                ]
                for column_number, cell_data in enumerate(display_data):
                    item = QTableWidgetItem(str(cell_data))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    # Tô màu khác để phân biệt
                    item.setForeground(Qt.GlobalColor.yellow)
                    self.table.setItem(row_number, column_number, item)

    def set_user_email(self, email):
        """Hàm này được gọi từ MainWindow sau khi Login thành công"""
        self.current_email = email
        self.lbl_user.setText(f"User: {email}")
        # Tự động tải lịch sử của user này
        self.load_history_data()
        
        # Cập nhật UI
        self.lbl_user.setVisible(True)
        self.btn_logout.setVisible(True)
        self.btn_show_login.setVisible(False)

    def reset_user_state(self):
        self.current_email = ""
        self.lbl_user.setVisible(False)
        self.btn_logout.setVisible(False)
        self.btn_show_login.setVisible(True)
        # Tải lại bảng lịch sử (lúc này sẽ là lịch sử tạm)
        self.load_history_data()