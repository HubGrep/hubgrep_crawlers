# HubGrep crawlers


## Development Setup
Web-frontend:
docker-compose up
Navigate to 0.0.0.0:8080 in your browser to search. The config for what is included is found in docker-compose.yml.

## API

## CLI:

To use the CLI, you must first have a shell inside a running container. Run:

    docker-compose run --rm service /bin/bash

Then, run a command (omit command to list all commands):

    flask cli <COMMAND>

## Backup

    flask cli export - | gzip -c > export.json.gz

## Restore a backup

TODO


