#!/bin/sh

# Create the logs directory if it doesn't exist
mkdir -p /app/logs

# Create the npda.log file if it doesn't exist
touch /app/logs/npda.log

# Execute
exec "$@"