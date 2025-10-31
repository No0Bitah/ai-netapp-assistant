# "slim" means a minimal Debian-based image with just Python essentials, reducing image size compared to the full Python image

FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir setuptools wheel && \
pip install --no-cache-dir -e .
COPY app /app/app