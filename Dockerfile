FROM python:3.11-slim-bookworm

COPY requirements.txt /cpr/

RUN pip install --no-cache-dir -r /cpr/requirements.txt

COPY . /cpr

ENTRYPOINT ["python", "/cpr"]