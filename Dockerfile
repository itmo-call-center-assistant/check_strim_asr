FROM python:3.11

WORKDIR /app

# install dependencies
RUN apt-get update
RUN apt-get install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev ffmpeg -y
COPY ./requirements.txt /app/requirements.txt
RUN ["pip", "install", "--no-deps", "--no-cache-dir", "--upgrade", "-r", "/app/requirements.txt"]

COPY ./configs /app/configs
COPY ./src /app/src

EXPOSE 8001
CMD ["python", "-m", "src.api.audio_api", "--port", "8001"]
