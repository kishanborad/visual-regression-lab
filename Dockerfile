FROM python:3.12-slim

LABEL maintainer="Kishan Borad <kishanborad27@gmail.com>"
LABEL description="Visual regression testing engine with PIL-based pixel comparison"

WORKDIR /app

# Install system dependencies for Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY python/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY python/ ./

# Run tests to verify installation
RUN pytest tests/ -v --tb=short

# Default entrypoint: run the comparison engine
ENTRYPOINT ["python", "diff_engine.py"]
CMD ["--help"]
