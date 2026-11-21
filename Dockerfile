# 用 3.12：requirements.txt 里 contourpy==1.4.0 需要 Python >=3.12，
# 同时避开 3.14 下 ragas/scikit-network 没有 cp314 wheel 的坑。
FROM python:3.12-slim

# 构建期依赖：numpy/pandas 等包需要 gcc
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先拷依赖再装：利用 Docker 分层缓存，改代码不用重装 140 个包
COPY requirements.txt .
# pywin32 是 Windows 专属包，Linux 容器里装不了，构建时过滤掉
RUN sed 's/\r$//' requirements.txt | grep -v '^pywin32==' > requirements-docker.txt \
    && pip install --no-cache-dir \
        --timeout 120 --retries 8 \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        -r requirements-docker.txt

# 再拷代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
