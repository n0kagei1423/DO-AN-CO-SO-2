import tkinter as tk
from tkinter import ttk
import threading
import os
import csv
from datetime import datetime
from core import do_ping, do_download, do_upload
#Biểu đồ 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
HISTORY_FILE = "history.csv"

# Hàm lưu lịch sử
def save_history(ping, download, upload):
    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "ping_ms", "download_mbps", "upload_mbps"])
        writer.writerow([datetime.now(), ping, download, upload])

# Hàm đọc 10 lần đo gần nhất
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    history = []
    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            history.append(row)
    return history[-10:]  # 10 lần gần nhất

class NetworkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Speed Test")
        self.geometry("500x300")
        self.resizable(False, False)
        self.build_ui()

    def build_ui(self):
        # Labels
        self.lbl_ping = ttk.Label(self, text="Ping: — ms", font=("Arial", 14))
        self.lbl_ping.pack(pady=10)

        self.lbl_download = ttk.Label(self, text="Download: — Mbps", font=("Arial", 14))
        self.lbl_download.pack(pady=10)

        self.lbl_upload = ttk.Label(self, text="Upload: — Mbps", font=("Arial", 14))
        self.lbl_upload.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=400)
        self.progress.pack(pady=20)

        # Start button
        self.btn_start = ttk.Button(self, text="Start Test", command=self.start_test)
        self.btn_start.pack()
        # Frame cho biểu đồ
        self.chart_frame = tk.Frame(self)
        self.chart_frame.pack(pady=10)

        # Tạo figure + axes
        self.fig = Figure(figsize=(4,3), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Nhúng vào Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack()


    # Hàm chạy test trong thread để UI không treo
    def start_test(self):
        self.btn_start.config(state="disabled")
        self.progress.start(10)
        threading.Thread(target=self.run_test, daemon=True).start()

    def run_test(self):
        # Đo Ping
        ping = do_ping()
        self.lbl_ping.config(text=f"Ping: {ping if ping else 'Lỗi'} ms")

        # Đo Download
        download = do_download()
        self.lbl_download.config(text=f"Download: {download if download else 'Lỗi'} Mbps")

        # Đo Upload
        upload = do_upload()
        self.lbl_upload.config(text=f"Upload: {upload if upload else 'Lỗi'} Mbps")

        # Kết thúc progress
        self.progress.stop()
        self.btn_start.config(state="normal")

if __name__ == "__main__":
    app = NetworkApp()
    app.mainloop()

print("á")