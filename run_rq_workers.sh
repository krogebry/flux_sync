#!/usr/bin/env bash
# kill -9 $(ps auxww|grep "rq worker"|grep -v "grep"|awk '{print $2}')

# Just run 1 worker in this terminal.
rq worker

# Run in the background.
# rq worker &
# rq worker &
# rq worker &
# rq worker &
