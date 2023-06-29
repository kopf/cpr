FROM python:3.11-slim-bookworm

COPY requirements.txt /cpr/

RUN pip install --no-cache-dir -r /cpr/requirements.txt

COPY . /cpr

ARG CPR_BUILD_VER

ENV CPR_VERSION=$CPR_BUILD_VER

ENTRYPOINT ["python", "/cpr"]