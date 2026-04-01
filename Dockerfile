FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Ensure youtube transcript dependency is always present even if dependency resolver/cache misbehaves.
RUN python -m pip install --no-cache-dir youtube-transcript-api==0.6.3 \
    && python -c "import youtube_transcript_api"

COPY . /app

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]