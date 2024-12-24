FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY processor.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "processor.py"]
