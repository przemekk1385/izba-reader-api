FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y netcat

ENV VIRTUAL_ENV=/usr/local/python

RUN python -m pip install --upgrade pip
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install poetry

WORKDIR /code

COPY . /code/

RUN poetry install --without=dev

ENTRYPOINT ["/code/entrypoint.sh"]
