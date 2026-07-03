# Development Guide

## Prerequisites

- Docker Compose
- Python 3.11

## Setting Up the Development Environment

### Clone the Repository

```sh
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Dashboard-Backend.git
cd MQP-Dashboard-Backend
```

### Install dependencies

```sh
pdm install
```

### Update project
```sh
pdm update
```

### Environment Variables

To run the project locally, update the environment variables in file .env:

1. Locate the .env.example file in the project root
2. Create a copy of this file and rename it to .env
3. Open the .env file and update the configuration values to match your local setup.

### Build and run Docker Container

**Build Docker Container**

To build Docker Container for developed environment, first enable mounted volumes in docker-compose.yaml. This action helps developer avoiding to build container in every update.

replace in docker-compose.yaml:
```sh
#volumes:
#    - ./mqp_dashboard_backend:/mqp-dashboard-backend-server/mqp_dashboard_backend
#    - ./.env:/mqp-dashboard-backend-server/.env
```
by:
```sh
volumes:
    - ./mqp_dashboard_backend:/mqp-dashboard-backend-server/mqp_dashboard_backend
    - ./.env:/mqp-dashboard-backend-server/.env
```
For building a production version, this mounted volumes should be disabled again.

Command to build container:
```sh
docker compose -f docker-compose.yaml build --no-cache
```
or
```sh
make build
```

**Start Container**
```sh
docker compose up -d
```
or
```sh
make up
```

To make environment variables affected to the application inside container, run this command:
```sh
make run-image
```

More commands will be found in `Makefile`

Application should run at: http://localhost:5000


### Testing

This project uses PDM for package and dependency management. The public local test suite is intended to run from the `tests/` directory with environment values loaded from a local `.env` file.

1. Install the development dependencies with PDM:

```sh
pdm install -G dev
```

2. Copy the safe example environment file to a private local `.env` file:

```sh
cp .env.example .env
```

3. Load the variables into your shell before running tests:

```sh
set -a
source .env
set +a
```

4. Run the normal public test suite:

```sh
pdm run python -m pytest tests
```

The `.env.example` file contains placeholder values that are safe for local development and testing.

These placeholder values are for local development/testing only. The `.env` file is local and private, and real `.env` files must not be committed. Do not include private credentials, private LDAP details, or deployment-specific information in this public README.

If tests try to connect to PostgreSQL through `/var/run/postgresql/.s.PGSQL.5432`, the `.env` variables were probably not loaded or `QUANTUM_DB_TESTING=TRUE` is missing. Reload `.env` and confirm the testing variables are set before rerunning the tests.

LDAP integration tests may require an explicitly configured LDAP test server and should not be expected to pass in a normal public/local setup. Run LDAP-dependent tests only when explicitly enabled and configured, for example with `RUN_LDAP_TESTS=TRUE` if that is how the tests are configured.

CI or test workflows may use `uv` for execution, for example:

```sh
UV_PROJECT_ENVIRONMENT=.venv-ci uv run python -m pytest tests
```

This does not replace PDM; PDM remains the project package and dependency manager.


### Linting and Ruff check

```sh
pdm run ruff check .
pdm run black --check .
```

### Development Workflow

1. Create a feature branch
2. Make changes
3. Add/update tests
4. Run linting and tests locally
5. Submit a pull request


## Building Documentation

To build the documentation, follow these steps:

**Install MkDocs and the Material theme:**
```sh
uv sync
```

**Build the documentation:**
```sh
uv run mkdocs build
```

**Local deployment:**

Run the following and browse the documentation locally at: http://localhost:8000
```sh
uv run mkdocs serve
```
