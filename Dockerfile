ARG PYTHON_VERSION=3.11-slim-bookworm

### Bun JS build for Vue components
FROM oven/bun:1.2.1 AS js-build

WORKDIR /js-build

# Copy base JS files first for dependency installation
COPY bun.lock package.json ./
RUN bun install --frozen-lockfile

# Copy all configuration files
COPY tsconfig*.json .
COPY vite.config.ts .
COPY .eslintrc.* .
COPY .prettierrc* .
COPY .dockerignore .

# Copy source files
COPY core/js/ core/js/
COPY sboms/js/ sboms/js/
COPY teams/js/ teams/js/

RUN bun run build

### Base Python stage
FROM python:${PYTHON_VERSION} AS python-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install psycopg2 dependencies.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /code
WORKDIR /code

# Install Python dependencies
RUN pip install poetry
COPY pyproject.toml poetry.lock README.md /code/
RUN poetry config virtualenvs.create false

# Install only main and prod dependencies
RUN poetry install --no-root --only main,prod --no-interaction

# Copy Python application code
COPY manage.py /code/
COPY sbomify/ /code/sbomify/
COPY access_tokens/ /code/access_tokens/
COPY core/ /code/core/
COPY sboms/ /code/sboms/
COPY teams/ /code/teams/

# Install the package itself
RUN poetry install --only-root --no-interaction

### Migrations target
FROM python-base AS migrations
CMD ["poetry", "run", "python", "manage.py", "migrate"]

### Main application target
FROM python-base AS application
# Copy built JS assets to static directory
COPY --from=js-build /js-build/static/* /code/static/

# Collect static files
RUN poetry run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "--bind", ":8000", "--workers", "2", "sbomify.wsgi"]
