FROM python:3.13-slim

WORKDIR /app/frontend

COPY . .
RUN pip install --upgrade pip && pip install --no-cache-dir .

EXPOSE 8501

CMD ["bash", "-c", "streamlit run frontend/main.py"]
