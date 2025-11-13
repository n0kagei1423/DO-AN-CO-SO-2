from flask import Flask, request
import time

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    start = time.time()
    _ = request.data  # đọc dữ liệu nhưng không lưu
    end = time.time()
    return {"processing_time": end - start}

if __name__ == "__main__":
    # chạy local, port 5000
    app.run(host="0.0.0.0", port=5000)
