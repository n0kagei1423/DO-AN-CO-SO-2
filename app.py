import tkinter as tk
from tkinter import ttk
import threading
import csv
import os
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core import tcp_ping, download_speed, upload_speed

HISTORY_FILE = "history.csv"


def save_history(ping, dl, up):
    exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["timestamp", "ping_ms", "download_mbps", "upload_mbps"])
        writer.writerow([datetime.now(), ping, dl, up])


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    rows = []
    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows[-10:]   # lấy 10 lần gần nhất cho nhẹ


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Speed Test – Python")
        self.geometry("650x450")
        self.resizable(False, False)

        self.build_ui()
        self.update_chart()

    def build_ui(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        self.lbl_ping = ttk.Label(frame, text="Ping: — ms", font=("Arial", 12))
        self.lbl_download = ttk.Label(frame, text="Download: — Mbps", font=("Arial", 12))
        self.lbl_upload = ttk.Label(frame, text="Upload: — Mbps", font=("Arial", 12))

        self.lbl_ping.grid(row=0, column=0, sticky="w")
        self.lbl_download.grid(row=1, column=0, sticky="w")
        self.lbl_upload.grid(row=2, column=0, sticky="w")

        self.btn = ttk.Button(frame, text="Start Test", command=self.start_test)
        self.btn.grid(row=3, column=0, pady=10)

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=4, column=0, sticky="ew", pady=5)

        # Chart
        fig = Figure(figsize=(4, 3), dpi=100)
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(fig, master=frame)
        self.canvas.get_tk_widget().grid(row=0, column=1, rowspan=10, padx=20)

    def start_test(self):
        self.btn.config(state="disabled")
        self.progress.start(10)

        t = threading.Thread(target=self.run_test)
        t.daemon = True
        t.start()

    def run_test(self):
        ping = tcp_ping()
        dl = download_speed()
        up = upload_speed()

        save_history(ping, dl, up)

        self.after(0, lambda: self.update_ui(ping, dl, up))

    def update_ui(self, ping, dl, up):
        self.progress.stop()
        self.btn.config(state="normal")

        self.lbl_ping.config(text=f"Ping: {ping:.2f} ms")
        self.lbl_download.config(text=f"Download: {dl:.2f} Mbps")
        self.lbl_upload.config(text=f"Upload: {up:.2f} Mbps")

        self.update_chart()

    def update_chart(self):
        data = load_history()
        if not data:
            return

        pings = [float(x["ping_ms"]) for x in data]
        dls = [float(x["download_mbps"]) for x in data]
        ups = [float(x["upload_mbps"]) for x in data]

        self.ax.clear()
        self.ax.plot(pings, label="Ping (ms)")
        self.ax.plot(dls, label="Download (Mbps)")
        self.ax.plot(ups, label="Upload (Mbps)")
        self.ax.legend()
        self.ax.set_title("Lịch sử 10 lần gần nhất")
        self.canvas.draw()
        