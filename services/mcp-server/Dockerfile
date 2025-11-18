FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY config.py server.py ./

# Create non-root user for security
RUN useradd -m -u 1000 docsplorer && \
    chown -R docsplorer:docsplorer /app
USER docsplorer

# Expose HTTP port
EXPOSE 8505

# Environment variables (can be overridden)
ENV TRANSPORT=http
ENV HOST=0.0.0.0
ENV PORT=8505

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8505/ || exit 1

# Default: Run with HTTP transport
# Override with: docker run ... python server.py --transport stdio
CMD ["python", "server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8505"]
