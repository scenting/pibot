FROM hypriot/rpi-python
MAINTAINER Miguel Gonzalez <scenting@gmail.com>

RUN apt-get update && apt-get install -y \
	transmission-cli \
	transmission-common \
	transmission-daemon \
	--no-install-recommends \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install pyTelegramBotAPI

COPY pibot.py /opt/pibot/pibot.py

ENTRYPOINT ["python", "/opt/pibot/pibot.py"]
CMD ["-h"]
