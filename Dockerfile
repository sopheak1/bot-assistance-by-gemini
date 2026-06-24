FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project configuration
COPY pyproject.toml .
# Also copy README if referenced by pyproject.toml to avoid pip errors
COPY README.md .

# Install dependencies into the system environment to avoid virtualenv overhead in Docker
RUN uv pip install --system -e .

# Copy source code
COPY src/ /app/src/

# Ensure data directory exists and has correct permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Run the bot
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "lifesync"]
