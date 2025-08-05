FROM python:3.13-slim

WORKDIR /app/frontend

COPY . .

# Install curl
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and add it to PATH
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.3
ENV PATH="/root/.local/bin:$PATH"

# Install project
RUN poetry install --only main

EXPOSE 8501

CMD ["bash", "-c", "poetry run streamlit run frontend/main.py"]
