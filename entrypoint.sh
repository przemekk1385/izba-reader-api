#!/bin/sh

until nc -z -v -w30 redis 6379
do
  echo "Waiting for Redis..."
  sleep 5
done

exec "$@"
