# Overview

`izba-reader` is an app created for gathering news from RSS feeds and scraped websites.

# Installation

As described below.

## Environment variables

All variables that do not have a default value must be set to get the app up and running.

| Name                 | Description                        | Default                 |
|----------------------|------------------------------------|-------------------------|
| EX                   | cache expiration time              | 28800 seconds (8 hours) |
| REDIS_URL            | Redis URL                          | redis://localhost:6379  |
| MAIL_FROM            | email from                         |
| MAIL_PASSWORD        | email password                     |
| MAIL_PORT            | mail server port                   |
| MAIL_SERVER          | mail server address                |
| MAIL_SUBJECT         | email subject                      |
| MAIL_USERNAME        | email username                     |
| ENVIRONMENT          | environment name                   | production              |
| ROLLBAR_ACCESS_TOKEN | Rollbar **post_server_item** token |

## Heroku

App can work on the Heroku cloud platform. Required buildpacks are listed below.

```
https://github.com/heroku/heroku-buildpack-apt
https://github.com/jontewks/puppeteer-heroku-buildpack
https://github.com/moneymeets/python-poetry-buildpack.git
heroku/python
```

### CircleCI

To use CircleCI for automated Heroku deployments `izba-reader-prod` context with
`HEROKU_API_KEY` and `HEROKU_APP_NAME` environment variables must be created.

**Note**: deployments happens only from `master` branch.
