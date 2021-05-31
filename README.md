# HubGrep crawlers


## Setup

Start the service:

    docker-compose up

Additionally, if this is the first time you run this setup, we need a shell in the container to init the DB:

    docker-compose run --rm service /bin/bash
    
From within this shell:

    flask cli db-create
    flask cli db-init

## API

Note: the API does not store crawled data, but rather sends it to the callback url received in the `/crawl` route.

## CLI

Note: the CLI is meant as a localdev tool, storing crawled data locally.

To use the CLI, you must first have a shell inside a running container. Run:

    docker-compose run --rm service /bin/bash

Then, run a command (omit command to list all commands):

    flask cli <COMMAND>

## Backup

    flask cli export - | gzip -c > export.json.gz

## Restore a backup

TODO


