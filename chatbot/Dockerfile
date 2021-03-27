FROM python:3.8-slim AS base

# Create temporary container to build dependencies
FROM base AS python-deps
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN apt-get update && apt-get install git gcc libpq-dev -y && PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# Make runtime container
FROM base AS runtime
WORKDIR /chatbot
COPY --from=python-deps /.venv/ .venv/
ENV PATH="/chatbot/.venv/bin:$PATH"
COPY ./chatbot ./chatbot
COPY ./wait-for /wait-for
RUN apt-get update && apt-get install gcc libpq-dev netcat -y