# cpr
cpr monitors your docker containers, performing healthchecks defined in docker labels, and restarting them when necessary. 

It's fairly similar to projects like [docker-autoheal](https://github.com/willfarrell/docker-autoheal), the main differences being:

* it doesn't fork a new process each time it performs a healthcheck, which on some limited hardware can be a little inefficient
* it uses special `cpr.*` docker labels as opposed to requiring the `HEALTHCHECK` directive in your `Dockerfile`s. 