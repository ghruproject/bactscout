# Multi-stage Dockerfile for bactscout using pixi
FROM ghcr.io/prefix-dev/pixi:latest AS source

ARG BACTSCOUT_DATABASE_SOURCE=bactscout_dbs
WORKDIR /src
COPY . .
RUN mkdir -p /src/bactscout_dbs && \
    if [ -d "/src/${BACTSCOUT_DATABASE_SOURCE}" ] && [ "${BACTSCOUT_DATABASE_SOURCE}" != "bactscout_dbs" ]; then \
        cp -a "/src/${BACTSCOUT_DATABASE_SOURCE}/." /src/bactscout_dbs/; \
    fi

# Final stage
FROM ghcr.io/prefix-dev/pixi:latest

# Set metadata
LABEL maintainer="Nabil-Fareed Alikhan <nabil@happykhan.com>"
LABEL description="BactScout - Bacterial genome QC and analysis tool"
LABEL version="1.4.1"

# Set working directory
WORKDIR /app
# Create output directory
RUN mkdir -p /app/bactscout_output
# Copy pixi configuration and lock file
COPY pixi.toml pixi.lock* ./

# Install dependencies
RUN pixi install --locked

# Copy application code
COPY bactscout/ ./bactscout/
COPY --from=source /src/bactscout_dbs/ /app/bactscout_dbs/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Reuse database files copied from bactscout_dbs/ and set up any missing files.
RUN pixi run bactscout preflight --database /app/bactscout_dbs

# Create a bactscout wrapper script in /usr/local/bin
RUN mkdir -p /usr/local/bin && \
    echo '#!/bin/bash' > /usr/local/bin/bactscout && \
    echo 'cd /app' >> /usr/local/bin/bactscout && \
    echo 'exec pixi run bactscout "$@"' >> /usr/local/bin/bactscout && \
    chmod +x /usr/local/bin/bactscout

# No ENTRYPOINT, just use default bash
CMD ["/bin/bash"]
