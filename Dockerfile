FROM python:3.12-slim

# Install system dependencies, Korean fonts, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# Copy application source
COPY src/ /app/src/

# Warm up typst package cache (pre-fetch @preview/mitex if needed or install local packages)
ENV TYPST_FONT_PATHS=/usr/share/fonts/opentype/noto:/usr/share/fonts/truetype
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "create_pdf_mcp.server"]
