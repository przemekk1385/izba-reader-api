[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CircleCI](https://circleci.com/gh/przemekk1385/izba-reader.svg?style=shield&circle-token=e583a0d895060bf37fa621a2b4ed066482c7baba)](https://app.circleci.com/pipelines/github/przemekk1385/izba-reader)

# Overview

`izba-reader` is an app created for gathering news from RSS feeds and scraped websites.

# Configuration

All variables that do not have a default value must be set to get the app up and running.

| Name                 | Description                        | Default                 |
|----------------------|------------------------------------|-------------------------|
| API_KEY              | API key                            |                         |
| BROWSER_URL          | browser service URL                | http://localhost:3000   |
| ENVIRONMENT          | environment name                   | production              |
| EX                   | cache expiration time              | 28800 seconds (8 hours) |
| MAIL_FROM            | email from                         |
| MAIL_PASSWORD        | email password                     |
| MAIL_PORT            | mail server port                   |
| MAIL_SERVER          | mail server address                |
| MAIL_SUBJECT         | email subject                      |
| MAIL_USERNAME        | email username                     |
| REDIS_URL            | Redis URL                          | redis://localhost:6379  |
| ROLLBAR_ACCESS_TOKEN | Rollbar **post_server_item** token |

# CircleCI pipeline

Current CircleCI configuration is allows to deploy dockerized app to DigitalOcean droplet.

Pipline uses SSH client image and custom `deploy-docker.sh` script placed on droplet.

Doppler CLI is used for injecting environment variables to Docker.

## Knowledge base

Below articles that might be handy:
* [How To Automate Deployment Using CircleCI and GitHub on Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-automate-deployment-using-circleci-and-github-on-ubuntu-18-04)
* [Install CLI](https://docs.doppler.com/docs/install-cli)

*deploy-docker.sh*
```
#!/bin/bash

cd "$1"
doppler run -t "$2" -- docker-compose down
git pull
doppler run -t "$2" -- docker-compose up --build -d

```

## Project settings

`USER`, `IP`, `DOPPLER_TOKEN` variables must be set in CircleCI project settings.
