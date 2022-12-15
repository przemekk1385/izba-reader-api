[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Overview

`izba-reader` is an app created for gathering news from RSS feeds and scraped websites.

# Configuration

All variables that do not have a default value must be set to get the app up and running.

| Name                                | Description                                      | Default                 |
|-------------------------------------|--------------------------------------------------|-------------------------|
| API_KEY                             | API key                                          |
| SERVICE_PORT                        | port the app runs on (`docker-compose.yml` only) |
| BROWSER_URL                         | browser service URL                              | http://localhost:3000   |
| ENVIRONMENT                         | environment name                                 | production              |
| EX                                  | cache expiration time                            | 28800 seconds (8 hours) |
| MAIL_FROM                           | email from                                       |
| MAIL_PASSWORD                       | email password                                   |
| MAIL_PORT                           | mail server port                                 |
| MAIL_SERVER                         | mail server address                              |
| MAIL_SUBJECT                        | email subject                                    |
| MAIL_USERNAME                       | email username                                   |
| OBJC_DISABLE_INITIALIZE_FORK_SAFETY | development only                                 | YES                     |
| REDIS_URL                           | Redis URL                                        | redis://localhost:6379  |
| ROLLBAR_ACCESS_TOKEN                | Rollbar **post_server_item** token               |

# Doppler configs
Project can be run using [Doppler](https://www.doppler.com).

### dev

App runs on localhost, services inside Docker container.

    $ make docker/up/dev
    $ make uvicorn/run

### dev_docker / prd

App and services runs inside Docker container, `dev_docker` is production-like.

    $ make docker/up
