# syntax=docker/dockerfile:1
FROM ghcr.io/chris-mcdo/pandoc2-python39:latest

ARG OBAPI_VERSION=0.3.0
ARG OBPAGES_VERSION=0.2.0

ENV DJANGO_PROJECT=obcollection
ENV DJANGO_USER=${DJANGO_PROJECT}
ENV DJANGO_GROUP=${DJANGO_USER}
ENV DJANGO_USER_UID=373
ENV DJANGO_GROUP_GUID=373
ENV PYTHONPATH="/etc/opt/${DJANGO_PROJECT}:/opt/${DJANGO_PROJECT}"
ENV DJANGO_SETTINGS_MODULE=settings

# Create system user and group
RUN addgroup --system --gid ${DJANGO_GROUP_GUID} ${DJANGO_GROUP}; \
    adduser --system --home=/var/opt/${DJANGO_PROJECT} --shell=/bin/bash \
    --uid ${DJANGO_USER_UID} --ingroup=${DJANGO_GROUP} --disabled-password \
    ${DJANGO_USER}

# Install runtime dependencies (psycopg)
RUN apt-get update; \
    apt-get install -y --no-install-recommends libpq5; \
    rm -rf /var/lib/apt/lists/*;

# Add source code
COPY . /tmp/code/${DJANGO_PROJECT}

# Install from source in a virtual environment, then cleanup 
RUN \
    # Build dependencies
    savedAptMark="$(apt-mark showmanual)"; \
    apt-get update; \
    apt-get install -y --no-install-recommends libpq-dev gcc python3-dev musl-dev; \
    \
    # Set up virtual environment
    /usr/local/bin/python3 -m venv /opt/${DJANGO_PROJECT}/venv; \
    # Upgrade pip
    /opt/${DJANGO_PROJECT}/venv/bin/pip3 install --no-cache-dir --upgrade pip; \
    # Explicitly install main dependencies
    /opt/${DJANGO_PROJECT}/venv/bin/pip3 install --no-cache-dir django-overcomingbias-api==${OBAPI_VERSION}; \
    /opt/${DJANGO_PROJECT}/venv/bin/pip3 install --no-cache-dir django-overcomingbias-pages==${OBPAGES_VERSION}; \
    # Install package and production dependencies
    /opt/${DJANGO_PROJECT}/venv/bin/pip3 install --no-cache-dir /tmp/code/${DJANGO_PROJECT}/[production]; \
    # Copy management script
    mv /tmp/code/${DJANGO_PROJECT}/manage.py /opt/${DJANGO_PROJECT}/; \
    # Make config directory
    mkdir /etc/opt/${DJANGO_PROJECT}; \
    chgrp ${DJANGO_GROUP} /etc/opt/${DJANGO_PROJECT}; \
    chmod 750 /etc/opt/${DJANGO_PROJECT}; \
    # Remove source code
    rm -rf /tmp/*; \
    # Purge build dependencies
    apt-mark auto '.*' > /dev/null; \
    apt-mark manual $savedAptMark; \
    apt-get purge -y --auto-remove libpq-dev; \
    rm -rf /var/lib/apt/lists/*;


EXPOSE 8080/tcp

USER ${DJANGO_USER}

CMD /opt/${DJANGO_PROJECT}/venv/bin/gunicorn --workers=4 --bind="[::]:8000" ${DJANGO_PROJECT}.wsgi:application
