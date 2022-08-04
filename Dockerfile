FROM python:3.10.4-bullseye

RUN apt-get update && apt-get install -y netcat

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH="${PATH}:/root/.poetry/bin"

RUN poetry config virtualenvs.create false

WORKDIR /code
COPY ./ .

RUN poetry install --no-dev

ENTRYPOINT ["./entrypoint.sh"]
