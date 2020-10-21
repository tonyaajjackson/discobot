FROM python:3.8-slim AS base

# Create temporary container to build dependencies
FROM base AS python-deps
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# Make runtime container
FROM base AS runtime
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
COPY config.json .
COPY discobot.py .
COPY .cache .

ENTRYPOINT ["python", "-u", "discobot.py"]