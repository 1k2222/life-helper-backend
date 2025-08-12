FROM arm64v8/ubuntu:24.04

RUN apt update -y
RUN apt install -y python3.12
RUN apt install -y python3-pip
RUN apt install -y gir1.2-gstreamer-1.0
RUN apt install -y gstreamer1.0-tools
RUN apt install -y gir1.2-gst-plugins-base-1.0
RUN apt install -y gstreamer1.0-plugins-good
RUN apt install -y gstreamer1.0-plugins-ugly

COPY requirements.txt /life-helper-backend/requirements.txt
WORKDIR /life-helper-backend
RUN pip3 install -r requirements.txt --break-system-packages
COPY . /life-helper-backend

CMD ["sh", "-c", "python3 -m fastapi run main.py"]