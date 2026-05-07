# syntax=docker/dockerfile:1.7

FROM cgr.dev/chainguard/python:latest-dev

USER root
WORKDIR /workspace

RUN apk add --no-cache git

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install \
        "copier>=9.0,<10.0" \
        "jinja2-time>=0.2.0,<0.3.0"

COPY --chown=nonroot:nonroot copier.yml /template/copier.yml
COPY --chown=nonroot:nonroot template /template/template

ARG VERSION=dev
ARG REVISION=unknown

LABEL org.opencontainers.image.title="copier-shopware-plugin" \
      org.opencontainers.image.description="Opinionated Copier template for Shopware 6 plugins" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/leifelralf/copier-shopware-plugin" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}"

USER nonroot

ENTRYPOINT ["copier", "copy", "--trust", "/template"]
CMD ["--help"]