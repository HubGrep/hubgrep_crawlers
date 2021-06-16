# HubGrep crawlers

These crawlers are intended as microservices connected to a indexer (https://github.com/HubGrep/hubgrep_indexer).

## Setup

Make a copy of the file `.env.dist`, rename it to `.env` and fill out the variables in it to fit your setup.

The important part, to automate the crawler, is to set `HUBGREP_CRAWLERS_JOB_URL` to connect to a running indexer.

Start the service:

    docker-compose up
    
Automation is started by using the `CLI` (see section below).

## API

TODO - API is a currently a dead-end, but eventually used for health/monitoring purposes.

## CLI

To use the CLI, you must first have a shell inside a running container. Run:

    docker-compose run --rm service /bin/bash

Then, run a command (omit command to list all commands):

    flask cli <COMMAND>


