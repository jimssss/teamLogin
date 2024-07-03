# 使用 python:3.10-slim 映像作為基礎映像
FROM python:3.10-slim as base

# 創建一個名為 builder 的新階段，並使用 base 映像作為基礎映像
FROM base as builder

# 設定工作目錄為 /app
WORKDIR /app

# 複製 requirements.txt 到工作目錄
COPY requirements.txt ./

# 複製當前目錄下的所有文件到容器中的 /app 目錄
COPY . ./

# 安裝 Python 套件，並將 pip 的快取目錄掛載為 Docker 的快取
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8000
# 當 Docker 容器啟動時，執行 Uvicorn 伺服器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

