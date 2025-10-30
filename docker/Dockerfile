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
# Create directories for databases and output
RUN mkdir -p /app/bactscout_dbs /app/bactscout_output
# Copy database files 
COPY bactscout_dbs/ /app/bactscout_dbs/
# Copy pixi configuration and lock file
COPY pixi.toml pixi.lock* ./

# Install dependencies
RUN pixi install --locked

# Copy application code
COPY bactscout/ ./bactscout/
COPY bactscout.py ./
COPY filtered_metrics.csv ./
COPY bactscout_config.yml* ./


# Set environment variables
ENV PYTHONUNBUFFERED=1

# Alter bactscout_config.yml to set database paths to /app/bactscout_dbs
RUN sed -i "s|bactscout_dbs_path: .*|bactscout_dbs_path: '/app/bactscout_dbs'|" bactscout_config.yml

# Create a bactscout wrapper script in /usr/local/bin
RUN mkdir -p /usr/local/bin && \
    echo '#!/bin/bash' > /usr/local/bin/bactscout && \
    echo 'cd /app' >> /usr/local/bin/bactscout && \
    echo 'exec pixi run python bactscout.py "$@"' >> /usr/local/bin/bactscout && \
    chmod +x /usr/local/bin/bactscout

# No ENTRYPOINT, just use default bash
CMD ["/bin/bash"]