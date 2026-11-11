FROM python:3.12.3
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
# DiscordChatExporter for the archive commands. It needs ICU.
RUN apt-get update && apt-get install -y --no-install-recommends libicu-dev && rm -rf /var/lib/apt/lists/*
RUN python scripts/install_dce.py
CMD python bot.py