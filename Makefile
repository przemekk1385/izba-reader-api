run:
	doppler run -c dev -- gunicorn -k izba_reader.workers.UvicornWorker -b 127.0.0.1:8000 izba_reader.main:app

build:
	doppler run -c dev_docker -- docker compose build

build-dev:
	doppler run -c dev -- docker compose -f docker-compose.dev.yml build

up:
	doppler run -c dev_docker -- docker compose up

up-dev:
	doppler run -c dev -- docker compose -f docker-compose.dev.yml up
