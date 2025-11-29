import sys
from PyQt6.QtWidgets import QApplication
from ui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())