FROM python:3.11-slim

# System deps for audio & opencv
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    espeak \
    espeak-ng \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi uvicorn

COPY . .

# Ensure data dirs
RUN mkdir -p data/faces assets && \
    echo '{"user_name": "Sir", "preferences": {}, "history": [], "todo": [], "reminders": [], "learned_facts": {}}' > data/memory.json || true

# Default env
ENV TEXT_MODE=true
ENV TTS_ENGINE=auto

EXPOSE 8000

# Default run API + text mode
CMD ["python", "server.py"]
