#!/bin/bash
set -e

echo "Building Docker image..."
docker-compose build

echo "Starting Docker container..."
docker-compose up -d

echo "Application is running at http://localhost:1001"
