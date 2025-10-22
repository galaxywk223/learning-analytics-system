FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# 系统依赖：psycopg2（虽用binary但保守留libpq头）、Pillow/wordcloud所需图形库
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev libpng-dev \
 && rm -rf /var/lib/apt/lists/*

# 非root运行
RUN useradd -m -u 10001 appuser

# 先装依赖，利用分层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝项目
COPY . .

# 修正 Windows 行尾并赋可执行权限
RUN sed -i 's/\r$//' infra/entrypoint.sh && chmod +x infra/entrypoint.sh

# 运行时目录（挂载上传用）
RUN mkdir -p /data/uploads && chown -R appuser:appuser /data

RUN mkdir -p /app/instance && chown -R appuser:appuser /app/instance

USER appuser
EXPOSE 8000

# Flask 工厂在 run.py 里已创建 app 变量；Gunicorn 直接加载 run:app 即可 
ENV FLASK_APP=run.py \
    MATPLOTLIB_BACKEND=Agg

ENTRYPOINT ["bash","infra/entrypoint.sh"]
