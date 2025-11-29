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