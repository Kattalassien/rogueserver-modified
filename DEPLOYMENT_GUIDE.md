# Deployment guide

## What should not be used as the primary host

GitHub Pages and GitHub Codespaces are not the correct primary deployment targets for this repo as it exists today.

This project is a Go HTTP API with MariaDB persistence and Docker/Podman deployment artifacts. The server reads runtime configuration from environment variables such as `dbaddr`, `dbuser`, `dbpass`, `dbname`, `gameurl`, and `callbackurl`, and the example stack in `docker-compose.Development.yml` runs both the API and MariaDB together.

That means the app needs:

- a real runtime (container or VM)
- a reachable database service
- a public hostname for callbacks and game URL config

GitHub Pages only serves static files. GitHub Codespaces is a development environment, not a production public host.

## Recommended hosting paths

### 1) Fastest path: Railway or Render

Best if the goal is: "get a public API running quickly without managing the OS."

Why it fits:

- supports a Docker-based app
- supports a managed MySQL/MariaDB service
- exposes a public URL for the API
- has simple env-var configuration

Recommended flow:

1. Deploy the app as a Docker service
2. Add a MariaDB/MySQL service
3. Set environment variables:
   - `dbaddr`
   - `dbuser`
   - `dbpass`
   - `dbname`
   - `gameurl`
   - `callbackurl`
   - `debug`
4. Set the public API URL and public game URL as the final hostnames
5. Test the health endpoint and game API routes

This is the easiest choice for a public test link.

### 2) GitHub-first path: GitHub Actions + Google Cloud Run + Cloud SQL

Best if the goal is: "GitHub-driven deployment with a more production-like setup."

Why it fits:

- Cloud Run can host the Go container
- Cloud SQL can host the database
- GitHub Actions can build and deploy automatically
- keeps the stack in a modern, managed cloud environment

Recommended flow:

1. Build and push the Docker image to GHCR
2. Authenticate GitHub Actions to Google Cloud
3. Deploy the container to Cloud Run
4. Provision a Cloud SQL instance or MariaDB-compatible database
5. Wire secrets and environment variables into Cloud Run
6. Set `callbackurl` and `gameurl` to the public Cloud Run URL

This is the best long-term production option if you want GitHub to be the deployment control point.

### 3) AWS-native path: ECS/Fargate or EC2

Best if the goal is: "I want AWS and I’m comfortable managing more of the stack."

Why it fits:

- the app is already container-friendly
- AWS can host both the API and the database
- gives full control if you already know the AWS stack

Tradeoff:

- more setup and more cost awareness
- more moving parts than Railway / Render

### 4) Fly.io

Best if the goal is: "quick Docker deploy with a public hostname."

Fly.io is a good middle ground between a beginner-friendly platform and a more configurable cloud setup.

## What not to choose for this repo

### GitHub Pages

GitHub Pages is static-only; it absolutely cannot host this app as it exists today.

It may be a place for a small static frontend later, but not the Go API or the MariaDB database.

### GitHub Codespaces

Codespaces is an excellent development environment and can be used to test or code against the repo, but it is not the right choice for a public production API deployment.

## Required deployment config

The app expects the following to be configured at runtime:

- `debug`
- `dbaddr`
- `dbuser`
- `dbpass`
- `dbname`
- `gameurl`
- `callbackurl`
- optionally `proto`, `addr`, `dbproto`, and TLS fields

In production, store these as secret environment variables instead of checking them into source control.

## Recommended minimum setup for public testing

If the goal is simply to get a public test link for the API:

- Use Railway or Render
- Deploy the Go app in Docker
- Add managed MariaDB
- Set `gameurl` and `callbackurl` to the public deployment URL
- Set strict access rules and only expose the required ports

This is the lowest-effort route to verifying the app on a real public endpoint.

## Example GitHub Actions deployment (Cloud Run)

This repo already has GitHub Actions for CI and GHCR publishing. A production deployment can be built on that pattern.

See `.github/workflows/deploy-cloudrun.yml` for a ready-to-customize example.

## Production caveats to handle before going public

Before exposing the app publicly:

- replace `localhost`-based URLs with the actual public host
- ensure the database is reachable from the running container
- set `callbackurl` to the real public API host
- set `gameurl` to the actual game frontend URL
- use secrets for DB credentials and auth data
- add a health endpoint and startup validation before traffic arrives
- consider a reverse proxy or Cloud Run ingress policy for better security

## Best recommendation

For this repo, the best immediate plan is:

- choose Railway or Render for the fastest public test deployment
- if you want a GitHub-native production workflow, choose GitHub Actions + Cloud Run + Cloud SQL
- keep GitHub Pages only for a static frontend if you split the app later

This is the practical way to move from a local Docker stack to a public service without rewriting the app architecture.
