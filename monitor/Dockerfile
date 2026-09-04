FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements-monitor.txt .
RUN pip install --no-cache-dir -r requirements-monitor.txt

COPY monitor.py .

CMD ["python", "monitor.py"]