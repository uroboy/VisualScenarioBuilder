FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    android-platform-tools \
    adb \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libatlas-base-dev \
    libjasper-dev \
    libtiff-dev \
    libjasper1 \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libjasper1 \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードコピー
COPY test_framework_main.py .
COPY test_scenario_example.yaml .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

# ADB デーモン起動
EXPOSE 5037

ENTRYPOINT ["./entrypoint.sh"]
