# Multi-stage Dockerfile for bactscout using pixi
FROM ghcr.io/prefix-dev/pixi:latest AS builder

# Set working directory
WORKDIR /app

# Copy pixi configuration files
COPY pixi.toml pixi.lock* ./

# Install dependencies using pixi
RUN pixi install --locked

# Copy the entire application
COPY . .

# Build/pack the environment (optional, for smaller final image)
# RUN pixi run pixi-pack pack

# Final stage
FROM ghcr.io/prefix-dev/pixi:latest

# Set metadata
LABEL maintainer="Nabil-Fareed Alikhan <nabil@happykhan.com>"
LABEL description="BactScout - Bacterial genome QC and analysis tool"
LABEL version="0.1.0"

# Set working directory
WORKDIR /app

# Copy pixi configuration and lock file
COPY pixi.toml pixi.lock* ./

# Install dependencies
RUN pixi install --locked

# Copy application code
COPY bactscout/ ./bactscout/
COPY bactscout.py ./
COPY bactscout_config.yml* ./

# Create directories for databases and output
RUN mkdir -p /app/bactscout_dbs /app/bactscout_output

# Set environment variables
ENV BACTSCOUT_DB_PATH=/app/bactscout_dbs
ENV PYTHONUNBUFFERED=1

# Expose any necessary ports (if needed for future web interface)
# EXPOSE 8000

# Set the entrypoint to use pixi run
ENTRYPOINT ["pixi", "run"]

# Default command
CMD ["bactscout", "--help"]
