FROM python:3.9.10-alpine3.15

ARG TIMESTAMP

LABEL org.opencontainers.image.authors=james@inpulsetech.io
LABEL org.opencontainers.image.created=${TIMESTAMP}
LABEL org.opencontainers.image.url=https://github.com/jwbennet/daily-summary-generator
LABEL org.opencontainers.image.source=https://github.com/jwbennet/daily-summary-generator
LABEL org.opencontainers.image.vendor="Inpulse Technologies, LLC"

RUN mkdir -p /usr/src/app/config && \
    adduser -S app && \
    addgroup -S app && \
    chown -R app:app /usr/src/app
    
WORKDIR /usr/src/app
USER app

COPY --chown=app:app Pipfile Pipfile.lock /usr/src/app/

RUN pip install --user --no-cache pipenv && \
    /home/app/.local/bin/pipenv install

COPY --chown=app:app *.py /usr/src/app/
