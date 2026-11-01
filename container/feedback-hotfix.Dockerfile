# Rebuild: docker build -f container/feedback-hotfix.Dockerfile -t obcollection:feedback-fix-8eaec965 .
# Retain the exact production runtime and dependencies; replace only the fixed view.
FROM ghcr.io/chris-mcdo/django-overcomingbias-collection@sha256:385c26a72d45a6a2420c8fa0b8e91c2d17cf345643f93dd6009cdfe7b6f28e15
LABEL org.overcomingbias.feedback-fix.revision="8eaec96578692996f24b62fa231ebc7d1eb3d35d"
USER root
ADD https://raw.githubusercontent.com/chris-mcdo/django-overcomingbias-pages/8eaec96578692996f24b62fa231ebc7d1eb3d35d/obpages/views.py /opt/obcollection/venv/lib/python3.13/site-packages/obpages/views.py
RUN python -c "import hashlib,pathlib; p=pathlib.Path('/opt/obcollection/venv/lib/python3.13/site-packages/obpages/views.py'); assert hashlib.sha256(p.read_bytes()).hexdigest() == '7d8ff3aa18faff83e74ff469d5729e2683345e7b75db451c541862b293a19c2b'; p.chmod(0o644)"
USER 373:373
