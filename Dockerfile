FROM python:3.11-slim-bookworm

USER root
WORKDIR /usr/app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r ./requirements.txt
USER 1000
COPY watch.py .

CMD ["python3", "./watch.py"]

