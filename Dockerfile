# Hermetic analysis environment for the agentic-vs-human benchmark (paper §3.6).
# Building from a pinned base + pinned wheels + a pinned PMD release makes the
# pipeline deterministic: `make all` twice yields numerically identical output.
FROM python:3.11-slim

ARG PMD_VERSION=7.0.0
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# CPD (from PMD) needs a JRE; unzip to unpack the release; git for submodules.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-jre-headless unzip curl git ca-certificates make \
    && rm -rf /var/lib/apt/lists/*

# Install PMD/CPD and expose `pmd` on PATH.
RUN curl -fsSL -o /tmp/pmd.zip \
        "https://github.com/pmd/pmd/releases/download/pmd_releases%2F${PMD_VERSION}/pmd-dist-${PMD_VERSION}-bin.zip" \
    && unzip -q /tmp/pmd.zip -d /opt \
    && ln -s "/opt/pmd-bin-${PMD_VERSION}/bin/pmd" /usr/local/bin/pmd \
    && rm /tmp/pmd.zip

WORKDIR /work

COPY requirements-analysis.txt .
RUN pip install --no-cache-dir -r requirements-analysis.txt

COPY . .

# Default: run the whole pipeline. Snapshots are expected to be mounted or
# checked out under ./subjects (read-only is fine).
CMD ["make", "all"]
