# Docker Deployment Guide

This guide explains how to build and run the MacroBuilder application using Docker.

## Prerequisites

- Docker installed on your system ([Install Docker](https://docs.docker.com/get-docker/))
- OpenAI API key (for AI-powered narrative generation)

## Building the Docker Image

From the repository root directory, run:

```bash
docker build -t macrobuilder:latest .
```

This will:
- Use Python 3.10 as the base image
- Install system dependencies for Kaleido/Plotly (chromium and related libraries)
- Install Python dependencies from requirements.txt
- Copy the application code
- Expose port 8501 (Streamlit default)

## Running the Container

### Basic Usage

```bash
docker run -p 8501:8501 macrobuilder:latest
```

Then open your browser to: http://localhost:8501

### With Environment Variables

To pass your OpenAI API key:

```bash
docker run -p 8501:8501 \
  -e OPENAI_API_KEY='your-api-key-here' \
  macrobuilder:latest
```

### With Volume Mounting (for persistence)

To persist saved configurations and generated PDFs:

```bash
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/_charts_tmp \
  -e OPENAI_API_KEY='your-api-key-here' \
  macrobuilder:latest
```

### Running in Detached Mode

```bash
docker run -d -p 8501:8501 \
  --name macrobuilder \
  -e OPENAI_API_KEY='your-api-key-here' \
  macrobuilder:latest
```

To view logs:
```bash
docker logs -f macrobuilder
```

To stop the container:
```bash
docker stop macrobuilder
```

To remove the container:
```bash
docker rm macrobuilder
```

## Docker Compose (Optional)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  macrobuilder:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/_charts_tmp
    restart: unless-stopped
```

Then run:

```bash
export OPENAI_API_KEY='your-api-key-here'
docker-compose up -d
```

## Health Check

The container includes a health check that monitors the Streamlit application:

```bash
docker ps  # Check the STATUS column for health status
```

## Troubleshooting

### Container fails to start
- Check logs: `docker logs <container-id>`
- Verify port 8501 is not already in use: `lsof -i :8501`

### Kaleido/PDF export issues
- The Dockerfile installs chromium and required libraries
- If issues persist, check container logs for missing dependencies

### Memory issues
- Increase Docker memory limit (Docker Desktop → Settings → Resources)
- Default Streamlit memory usage is typically 200-500MB

### Network issues (FRED data fetching)
- Ensure container has internet access
- Check firewall/proxy settings
- FRED API may have rate limits

## Advanced Configuration

### Custom Port

```bash
docker run -p 8080:8501 macrobuilder:latest
```

Then access at: http://localhost:8080

### Custom Streamlit Configuration

Create `.streamlit/config.toml` and mount it:

```bash
docker run -p 8501:8501 \
  -v $(pwd)/.streamlit:/app/.streamlit \
  macrobuilder:latest
```

## Production Deployment

For production deployment, consider:

1. **Use a reverse proxy** (nginx, traefik) with SSL/TLS
2. **Set resource limits**:
   ```bash
   docker run --memory="1g" --cpus="2" -p 8501:8501 macrobuilder:latest
   ```
3. **Use docker-compose** or orchestration (Kubernetes, Docker Swarm)
4. **Set up monitoring** (Prometheus, Grafana)
5. **Configure log rotation**
6. **Use secrets management** for API keys (Docker secrets, Vault)

## Size Optimization

The current image is ~600-800MB. To reduce size:

1. Use multi-stage builds
2. Use alpine-based images (requires compilation of dependencies)
3. Remove unnecessary system packages after installation

## Support

For issues or questions:
- GitHub Issues: [Repository Issues](https://github.com/PresidentofMexico/MacroEconDataArchive/issues)
- Documentation: [README.md](README.md)
