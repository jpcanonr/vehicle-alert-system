FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Usamos Gunicorn con UvicornWorker para manejar múltiples solicitudes concurrentes de manera eficiente, 4 workers para aprovechar múltiples núcleos de CPU
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--workers", "4", "--bind", "0.0.0.0:8000"]

