FROM python:3.10-slim

WORKDIR /app

COPY sub.py .

RUN pip install paho-mqtt matplotlib numpy scipy

CMD ["python", "sub.py"]
