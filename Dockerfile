FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Create a script to run both services
RUN echo '#!/bin/bash\n\
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000 & \
streamlit run streamlit_app/app.py --server.port 8501 --server.address 0.0.0.0\n\
wait' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"] 