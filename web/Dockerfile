FROM python:3.8-slim AS base

# Create temporary container to build dependencies
FROM base AS python-deps
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --verbose --deploy 2>&1 | grep Install 
# grep picks out packages installed from verbose output

# Make runtime container
FROM base AS runtime
ENV PYTHONUNBUFFERED=1
COPY --from=python-deps /.venv/ .venv/
ENV PATH="/.venv/bin:$PATH"
WORKDIR /web
COPY . /web/
COPY ./wait-for /wait-for
RUN apt-get update && apt-get install gcc libpq-dev netcat -y