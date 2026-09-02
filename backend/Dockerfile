FROM python:3.12-slim

WORKDIR /app

# libreoffice-calc/writer: motor headless usado para converter os relatórios
# .xlsx/.docx em .pdf sob demanda (?formato=pdf) — sem eles, a API responde
# 503 nessas exportações (ver PdfConvert / LibreOfficeIndisponivel).
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev libreoffice-calc libreoffice-writer && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
