FROM python:3.13-slim-trixie@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev libpq-dev git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY container/requirements.lock /build/requirements.lock
COPY container/wheel_lock.py /build/wheel_lock.py
COPY pyproject.toml README.rst LICENSE manage.py /build/collection/
COPY obcollection /build/collection/obcollection

# Package versions and public wheel hashes are reviewed together in application.json.
COPY container/application.py container/application-policy.json container/application.json /build/application/
ARG COLLECTION_VERSION
RUN python /build/application/application.py download --directory /application-wheels
RUN test -n "$COLLECTION_VERSION" \
    && SETUPTOOLS_SCM_PRETEND_VERSION="$COLLECTION_VERSION" \
       pip wheel --no-deps --wheel-dir /collection-wheel /build/collection \
    && set -- /collection-wheel/*.whl && test "$#" -eq 1 \
    && pip wheel --wheel-dir /wheels -c /build/requirements.lock \
       -r /build/requirements.lock /application-wheels/*.whl \
       "$1[production]" \
    && python /build/wheel_lock.py /wheels \
    && python -m venv /opt/obcollection/venv \
    && /opt/obcollection/venv/bin/pip install --no-index --find-links=/wheels \
       --require-hashes -r /wheels/install.lock \
    && /opt/obcollection/venv/bin/pip check \
    && cp /wheels/install.lock /opt/obcollection/requirements.lock \
    && cp /build/application/application.json /opt/obcollection/application.json \
    && cp /build/collection/manage.py /opt/obcollection/manage.py

FROM python:3.13-slim-trixie@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=settings \
    PYTHONPATH=/etc/opt/obcollection:/opt/obcollection \
    PATH=/opt/obcollection/venv/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 pandoc texlive-xetex texlive-latex-extra fonts-dejavu \
    fonts-liberation ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 373 obcollection \
    && useradd --uid 373 --gid 373 --no-create-home obcollection \
    && mkdir -p /etc/opt/obcollection /var/opt/obcollection/static \
       /var/opt/obcollection/media /var/opt/obcollection/silk \
    && chown -R 373:373 /var/opt/obcollection \
    && chgrp 373 /etc/opt/obcollection && chmod 0750 /etc/opt/obcollection
COPY --from=builder /opt/obcollection /opt/obcollection
RUN dpkg-query -W > /opt/obcollection/os-packages.txt
USER 373:373
WORKDIR /opt/obcollection
EXPOSE 8080
CMD ["gunicorn", "-c", "/etc/opt/obcollection/gunicorn.conf.py"]
