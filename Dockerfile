# ---- Stage 1: train ----
FROM python:3.11-slim AS train

WORKDIR /app
COPY train/requirements-train.txt .
RUN pip install --no-cache-dir -r requirements-train.txt

COPY train/train.py .
RUN mkdir -p /data
RUN python train.py

# ---- Stage 2: serve ----
FROM python:3.11-slim AS serve

WORKDIR /app
COPY serve/requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt

COPY serve/serve.py .

COPY --from=train /data/ /data/

EXPOSE 5000
CMD ["python", "serve.py"]