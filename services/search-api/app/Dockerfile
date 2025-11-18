FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /usr/src/app

# Install dependencies
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire repository to preserve package structure
COPY . .

# Launch FastAPI app (module path lives under the app/ package)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
