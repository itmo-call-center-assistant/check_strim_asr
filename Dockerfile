FROM python:3.11

WORKDIR /app

# install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN ["pip", "install", "--no-deps", "--no-cache-dir", "--upgrade", "-r", "/app/requirements.txt"]

COPY ./configs /app/configs
COPY ./src /app/src

EXPOSE 8001
CMD ["python," "-m", "src.api.audio_api", "--port", "8001"]
