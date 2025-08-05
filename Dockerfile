FROM python:3.13-slim

WORKDIR /app/frontend

COPY . .

RUN pip install --upgrade pip && \
    pip install --user pipx

ENV PATH="/root/.local/bin:$PATH"

RUN pipx install poetry==2.1.3 && \
    poetry install --only main

EXPOSE 8501

CMD ["bash", "-c", "poetry run streamlit run frontend/main.py"]
