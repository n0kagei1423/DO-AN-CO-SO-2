import sqlite3
import datetime
import os
import hashlib

def lay_ten_db(email):
    # Hash email để tạo tên file an toàn hơn, tránh lộ thông tin
    email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    return f"{email_hash}.db"

def khoi_tao_db(email):
    db_name = f'./database/{lay_ten_db(email)}'
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  thoi_gian TEXT,
                  ping TEXT,
                  download REAL,
                  upload REAL,
                  isp TEXT,
                  ip TEXT)''')
    conn.commit()
    conn.close()

def luu_ket_qua(email, ping, download, upload, isp, ip):
    db_name = f'./database/{lay_ten_db(email)}'
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    thoi_gian = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO history (thoi_gian, ping, download, upload, isp, ip) VALUES (?, ?, ?, ?, ?, ?)",
              (thoi_gian, ping, download, upload, isp, ip))
    conn.commit()
    conn.close()

def lay_lich_su(email):
    db_name = f'./database/{lay_ten_db(email)}'
    # Kiểm tra xem file có tồn tại không trước khi đọc
    if not os.path.exists(db_name):
        return []

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return data