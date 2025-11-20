import tkinter as tk
from ui import UngDungSpeedTest

# Đây là điểm bắt đầu của chương trình
if __name__ == "__main__":
    # Tạo cửa sổ gốc
    root = tk.Tk()
    
    # Nạp ứng dụng vào cửa sổ gốc
    app = UngDungSpeedTest(root)
    
    # Giữ cửa sổ hiển thị
    root.mainloop()