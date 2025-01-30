# sbomify backend

Backend for sbomify.com

## Releases

For information about cutting new releases, see [RELEASE.md](RELEASE.md).

## Local Development

### Prerequisites

- Python 3.12+
- Poetry
- Docker (for running PostgreSQL and Minio)
- Bun (for JavaScript development)

### API Documentation

The API documentation is available at:

- Interactive API docs (Swagger UI): `http://localhost:8000/api/v1/docs`
- OpenAPI specification: `http://localhost:8000/api/v1/openapi.json`

These endpoints are available when running the development server.

### Setup

- Copy `.env.example` to `.env` and adjust values as needed:

```bash
cp .env.example .env
```

- You can run the application in two ways:

#### Using Docker Compose (recommended)

```bash
docker compose up
```

This will start all required services:

- PostgreSQL database for data storage
- MinIO S3-compatible storage (accessible at `http://localhost:9001`)
- Django development server

#### Running Locally (without Docker for Django)

- Start required services in Docker:

```bash
# Start both PostgreSQL and MinIO
docker compose up sbomify-db sbomify-minio sbomify-createbuckets -d
```

- Install dependencies:

```bash
poetry install
bun install  # for JavaScript dependencies
```

- Run migrations:

```bash
poetry run python manage.py migrate
```

- Start the development servers:

```bash
# In one terminal, start Django
poetry run python manage.py runserver

# In another terminal, start Vite
bun run dev
```

### Configuration

#### Development Server Settings

The application uses Vite for JavaScript development. The following environment
variables control the development servers:

```bash
# Vite development settings
DJANGO_VITE_DEV_MODE=True
DJANGO_VITE_DEV_SERVER_PORT=5170
DJANGO_VITE_DEV_SERVER_HOST=http://localhost

# Static and development server settings
STATIC_URL=/static/
DEV_JS_SERVER=http://127.0.0.1:5170
WEBSITE_BASE_URL=http://127.0.0.1:8000
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_WEBSITE_BASE_URL=http://127.0.0.1:8000
```

These settings are preconfigured in the `.env.example` file.

#### S3/Minio Storage

The application uses S3-compatible storage for storing files and assets. In
development, we use Minio as a local S3 replacement.

- When running with Docker Compose, everything is configured automatically
- When running locally (Django outside Docker):
  1. Make sure Minio is running via Docker:
     `docker compose up sbomify-minio sbomify-createbuckets -d`
  2. Set `AWS_S3_ENDPOINT_URL=http://localhost:9000` in your `.env`
  3. The required buckets (`sbomify-media` and `sbomify-sboms`) will be created
     automatically

You can access the Minio console at:

- `http://localhost:9001`
- Default credentials: minioadmin/minioadmin

### Running test cases

```shell
poetry run coverage run -m pytest --pdb -x -s
poetry run coverage report
```

### JS build tooling

For frontend JS work, setting up JS tooling is required.

#### Bun

```shell
curl -fsSL https://bun.sh/install | bash
```

In the project folder at the same level as `package.json`:

```shell
bun install
```

#### Linting

For JavaScript/TypeScript linting:

```shell
# Check for linting issues (used in CI and can be run locally)
bun lint

# Fix linting issues automatically (local development only)
bun lint-fix
```

#### Run vite dev server

```shell
bun run dev
```

## Production Deployment

### Prerequisites

- Docker and Docker Compose
- S3-compatible storage (like MinIO)
- PostgreSQL database
- Auth0 account for authentication (Note: Migration to Keycloak is planned)
- Reverse proxy (e.g., Nginx) for production deployments

### Docker Compose Configuration

The application uses two Docker Compose files:
- `docker-compose.yml`: Base configuration with development defaults
- `docker-compose.prod.yml`: Production overrides that:
  - Remove development-specific settings
  - Add production-specific configurations
  - Configure proper restart policies
  - Remove exposed ports except for the web interface
  - Remove development volume mounts

### Reverse Proxy Setup

For production deployments, it's strongly recommended to put a reverse proxy (such as Nginx) in front of the application server. This provides:
- SSL/TLS termination
- Better security
- Static file serving
- Load balancing (if needed)
- Request buffering
- Gzip compression

### Authentication

#### Current: Auth0 Configuration

> **Note**: The application is planned to migrate from Auth0 to Keycloak. See [#1](https://github.com/sbomify/sbomify/issues/1) for details.

Create a "Regular Web Application" in Auth0 with the following settings:

| Setting | Value |
|---------|-------|
| APPLICATION LOGIN URI | https://[yourdomain] |
| ALLOWED CALLBACK URLs | https://[yourdomain]/complete/auth0 |
| ALLOWED LOGOUT URLs | https://[yourdomain] |
| ALLOWED WEB ORIGINS | https://[yourdomain] |

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
POSTGRES_PASSWORD=<secure-password>

# Security
SECRET_KEY=<django-secret-key>

# Auth0
SOCIAL_AUTH_AUTH0_DOMAIN=<your-auth0-domain>
SOCIAL_AUTH_AUTH0_KEY=<your-auth0-client-id>
SOCIAL_AUTH_AUTH0_SECRET=<your-auth0-client-secret>

# Storage (MinIO/S3)
AWS_ACCESS_KEY_ID=<your-s3-access-key>
AWS_SECRET_ACCESS_KEY=<your-s3-secret-key>

# Application
APP_BASE_URL=https://[your-domain]
```

### Running in Production

1. Build and start the production stack:
```bash
# Build the images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start the stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

2. Create a superuser account (first time only):
```bash
docker compose exec sbomify-backend poetry run python manage.py createsuperuser
```

3. The application will be available at `http://[your-domain]:8000`

### SBOM Upload via API

#### CycloneDX

```shell
curl -v -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  --data-binary @cyclonedx-format-sbom-file.json \
  https://[your-domain]/api/v1/sboms/artifact/cyclonedx/<component-id>
```

#### SPDX

```shell
curl -v -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  --data-binary @spdx-format-sbom-file.json \
  https://[your-domain]/api/v1/sboms/artifact/spdx/<component-id>
```

### Backup and Restore

```shell
# Take DB backup
docker compose exec sbomify-db pg_dump -U sbomify sbomify > backup.sql

# Restore DB from backup
cat backup.sql | docker compose exec -T sbomify-db psql -U sbomify sbomify
```

### Generating Pydantic Models

For sbom formats, models for new versions can be generated using
`datamodel-codegen` which is installed as a dev dependency.

```shell
poetry run datamodel-codegen \
  --url https://github.com/CycloneDX/specification/raw/refs/tags/1.6/schema/bom-1.6.schema.json \
  --output-model-type pydantic_v2.BaseModel \
  --use-standard-collections \
  --use-subclass-enum \
  --use-double-quotes \
  --use-schema-description \
  --target-python-version 3.10 \
  --use-annotated \
  --output cyclonedx
```
