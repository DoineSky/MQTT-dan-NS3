FROM python:3.10-slim

WORKDIR /app

COPY pub.py .

RUN pip install paho-mqtt

CMD ["python", "pub.py"]
