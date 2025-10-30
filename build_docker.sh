#!/bin/bash

# Get version from bactscout/__version__.py
VERSION=$(python -c "from bactscout.__version__ import __version__; print(__version__)")
echo "Building BactScout Docker image version: $VERSION"

# Build the Docker image
echo "Building Docker image..."
docker build -t bactscout:latest -t bactscout:$VERSION -f docker/Dockerfile .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi
echo "✅ Docker build successful"

# Remove test output directory if it exists
echo "Cleaning up test directory..."
rm -rf docker_test

# Run test
echo "Running test sample through Docker..."
docker run -v $(pwd):/data bactscout:latest bactscout collect \
    /data/test_data/Sample_213aab83semb_R1.fastq.gz \
    /data/test_data/Sample_213aab83semb_R2.fastq.gz \
    --output /data/docker_test

if [ $? -ne 0 ]; then
    echo "❌ Docker test run failed"
    exit 1
fi
echo "✅ Docker test run successful"

# Check if output file exists
if [ ! -f "docker_test/Sample_213aab83semb/Sample_213aab83semb_summary.csv" ]; then
    echo "❌ Output file not found: docker_test/Sample_213aab83semb/Sample_213aab83semb_summary.csv"
    exit 1
fi
echo "✅ Output file verified"

# Push to Docker Hub
echo "Pushing to Docker Hub..."
docker push ghruproject/bactscout:latest
docker push ghruproject/bactscout:$VERSION

if [ $? -eq 0 ]; then
    echo "✅ Docker image pushed successfully"
    echo "📦 Images:"
    echo "   - ghruproject/bactscout:latest"
    echo "   - ghruproject/bactscout:$VERSION"
else
    echo "⚠️  Docker push failed (Docker Hub credentials may not be configured)"
    exit 1
fi