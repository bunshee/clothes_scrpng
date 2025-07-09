#!/bin/bash
# docker-entrypoint.sh

set -e

host="db"
port="5432"
cmd="$@"

# Wait for PostgreSQL to be ready
until pg_isready -h "$host" -p "$port" -U postgres; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

echo "Executing command: python main.py \"$@\""
exec python main.py "$@"