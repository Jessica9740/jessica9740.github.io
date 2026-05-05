FROM python:3.11-slim
RUN apt-get update && apt-get install -y git openssh-client && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn
COPY . .
RUN pip install --no-cache-dir -e .
EXPOSE 8000
CMD ["uvicorn", "auto_blog.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
