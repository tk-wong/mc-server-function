FROM python:3.14-slim
WORKDIR /app
COPY pyproject.toml main.py ./
RUN pip install . --no-cache-dir
EXPOSE 8080
CMD ["python", "-u", "main.py"]
