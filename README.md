# flux_sync

Quick and dirty app to copy data from one place to another

# User Story

This project came about because of a rather tricky condition with InfluxDB.  We were running
InfluxDB in a container with the latest version of 1.8, which unfortunately kept crashing.
We decided to down grade to 1.4.3, which seemed to stop the crashing for the moment, but then
eventually began crashing.

In this case the dockerized InfluxDB ( IDB ) was running along with Timescale and a few other
services running in docker container.  There was obvious resource contention on the host, which
was most likely the cause of the crashing.  Downgrading the version was our only option at the
time until we were threw the R1 release.

Once R1 was complete we were able to build out a better infrastructure for the R2 release.  This 
new buildout included a dedicated IDB host and a dedicated services host, this way we're basically
able to separate out the resource contention.

This had a remarkable impact on overall performance and stability for the system in general.

However, there was 1 draw back in that during the migration from the old to the new, the backups
of the old data didn't 100% import into the new 1.8 IDB host.  We did get some data, but for
some reason, not all of the data was available.

The backup utilities for 1.4 don't support the `-portable` option, and as far as I can tell, peforming
a backup and restore with IDB is basically the same as copying the files around.  In that
you still have to shut down the server for a restore, monkey around with the files, and wait
10 years for the restore operation to muddle through it's agonizing slow process.

We had data running in the old system, which I was able to keep operational, and new data flowing
into the new system, which wasn't allowed to go down.  Thus, I needed a way to take data from the 
old thing to the new thing.

This seems like a common thing to happen in IT.  I would have writen this tool in Ruby using
resque, but we're more of a python shop, so we're going to use python and `rq`.  It's basically
the same idea.

# Learnings

The very first thing I did here was to test out the theory of what I was doing by writing a very
simple connection from left to right.

Here we're defining `left` as the old InfluxDB ( 1.4.3 ) service, and `right` as the new InfluxDB ( 1.8 )
service.

What I noticed immediately was that queries that return more than around 100k rows would crash the
server fairly consistently.  It appears as though keeping the connection open while transferring
a huge number of rows caused enough contention on the host to cause a problem with IDB.

This is why I decided to break things up into jobs and buckets with `LIMIT` and `OFFSET` in the queries. 
My thinking here is that each job will create and eventually close the connection to the server,
thus giving the service the opportunity to cleanup resources on the next garbage collection cycle.

This also allowed me to process large batches of data in parallel.  The downside to this was that
the old IDB instance was still prone to barfing under load, so pushing it with multiple threads
ended up being a no-go.  Eventually I had to settle on doing a single process and just letting
this run for as long as it was going to run for.

# Setup

Use docker-compose or whatever you want to get this done.

```bash
docker run -p 6379:6379 -d -e ALLOW_EMPTY_PASSWORD=yes bitnami/redis:5.0
```

Given my needs here, this was good enough.

# sync to create jobs

The sync job is going to create a batch of jobs to process the various work items.  We point it at a database
and a few things are going to happen:

* Get a list of all measurements via `SHOW MEASUREMENTS`
* For each hour in a day:
  * For each day this month ( we don't need data after the 25th )
    * Create a job representing this day, and this hour for this measurement

Depending on the data, this could be quite a number of jobs.

# RQ to process jobs

Each job will queue up n number of entries and write those entries to the new host in a way that makes
sense and works for the format that we're using here.

Once the job is complete, the resources from that job execution should be freed up.  At least that's the hope.

# TODO

* Authentication stuff would be nice.
* Better handling of failures is always good, along with maybe some tests of some kind.
* CLI stuff to pass in host names seems like a good idea.
