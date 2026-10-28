FROM python:3.12-slim

# Install system dependencies, Korean fonts, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install dependencies
COPY pyproject.toml README.md ./
RUN python -c 'import tomllib; c = tomllib.load(open("pyproject.toml", "rb")); print("\n".join(c["project"]["dependencies"]))' > requirements.txt \
    && pip install --no-cache-dir hatchling -r requirements.txt

# Copy application source
COPY src/ /app/src/

# Install application package
RUN pip install --no-cache-dir --no-build-isolation --no-deps .

# Warm up typst package cache (pre-fetch @preview/mitex if needed or install local packages)
ENV TYPST_FONT_PATHS=/app/src/create_pdf_mcp/assets/fonts:/usr/share/fonts/opentype/noto:/usr/share/fonts/truetype
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["python", "-m", "create_pdf_mcp.server"]
