import sqlite3
import datetime
import os

# Hàm tạo tên file DB dựa theo email
def lay_ten_db(email):
    # Ví dụ: speedtest_abc@gmail.com.db
    return f"speedtest_{email}.db"

def khoi_tao_db(email):
    """Tạo bảng riêng cho email này nếu chưa có"""
    db_name = f'./database/{lay_ten_db(email)}'
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    # Bỏ cột email đi, vì file này đã là của riêng user đó rồi
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
    """Lưu kết quả vào file DB riêng của email"""
    db_name = f'./database/{lay_ten_db(email)}'
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    thoi_gian = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert không cần cột email
    c.execute("INSERT INTO history (thoi_gian, ping, download, upload, isp, ip) VALUES (?, ?, ?, ?, ?, ?)",
              (thoi_gian, ping, download, upload, isp, ip))
    conn.commit()
    conn.close()

def lay_lich_su(email):
    """Đọc dữ liệu từ file DB riêng"""
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