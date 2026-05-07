# syntax=docker/dockerfile:1.7
#
# Multi-stage build for copier-shopware-plugin.
#
# Stage 1 ("builder")  — Chainguard Wolfi with shell + apk for installation.
# Stage 2 ("runtime")  — Chainguard distroless: no shell, no package manager,
#                        only Python + the prepared venv + the template.
#
# Final image: ~60 MB, hardened, daily-rebuilt by Chainguard upstream.

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM cgr.dev/chainguard/python:latest-dev AS builder

USER root
WORKDIR /build

# Git is required by Copier for VCS-aware operations (--vcs-ref, copier update).
# busybox provides the minimal shell utilities the build scripts here use.
RUN apk add --no-cache git

# Build a self-contained venv we can copy into the runtime stage.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Pin the major versions that match our test matrix.
RUN pip install \
        "copier>=9.0,<10.0" \
        "jinja2-time>=0.2.0,<0.3.0"

# ---------------------------------------------------------------------------
# Stage 2: runtime (distroless)
# ---------------------------------------------------------------------------
FROM cgr.dev/chainguard/python:latest

# Bring git binary + its helper dir along. Copier invokes `git` as a
# subprocess; without it, --vcs-ref and copier update fail.
COPY --from=builder /usr/bin/git /usr/bin/git
COPY --from=builder /usr/libexec/git-core /usr/libexec/git-core

# Bring the venv with copier + jinja2-time installed.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Embed the template itself. The image is the template — no clone needed.
COPY --chown=nonroot:nonroot copier.yml /template/copier.yml
COPY --chown=nonroot:nonroot template /template/template

# OCI labels for traceability.
ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="copier-shopware-plugin" \
      org.opencontainers.image.description="Opinionated Copier template for Shopware 6 plugins" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/leifelralf/copier-shopware-plugin" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}"

USER nonroot
WORKDIR /workspace

# Default invocation: `docker run -it ... <output-path>`.
# Override with `docker run ... <image> --help` to see all copier options,
# or `docker run ... <image> update <path>` to update an existing plugin.
ENTRYPOINT ["copier", "copy", "--trust", "/template"]
CMD ["--help"]
