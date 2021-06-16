# HubGrep crawlers


## Setup

Make a copy of the file `.env.dist`, rename it to `.env` and fill out the variables in it to fit your setup.

Start the service:

    docker-compose up

Additionally, if this is the first time you run this setup and you intend to use the `CLI`, we need a shell in the container to init a DB:

    docker-compose run --rm service /bin/bash
    
From within this shell:

    flask cli db-create
    flask cli db-init
    
OR, if you want to play around in localdev, we have a simple bootstrap script:

    sh ./localdev_init.sh
    
This will register some platforms that you can crawl right away.

## API

TODO - API is a currently a dead-end, but eventually used for health/monitoring purposes.

## CLI

The CLI is meant as a localdev tool, storing crawled data locally.

To use the CLI, you must first have a shell inside a running container. Run:

    docker-compose run --rm service /bin/bash

Then, run a command (omit command to list all commands):

    flask cli <COMMAND>

## Backup

Make a dump from repo objects in the database:

    flask cli export - | gzip -c > export.json.gz

## Restore a backup

TODO


