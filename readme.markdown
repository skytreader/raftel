# raftel

An exercise in implementing [Raft](https://raft.github.io/).

## Running

Create a python3 virtualenv, install the requirements and then in separate tabs
issue:

```
(raft)$ python src/overseer.py -p 16981
(raft)$ python src/raftnode.py -H 127.0.0.1 -p 16981
```

Of course, the port number can be changed.

## Type Checking

This makes use of [mypy](http://mypy-lang.org) to add type annotations to the
code. To check that your modifications are type-consistent:

    mypy --ignore-missing-imports src/*.py

We ignore missing imports because gevent does not have mypy types as of this
writing.

## Debugging

To debug either overseer or raftnode, just set the `raftel_log_level`
environment variable to 10 (the actual value of `logging.DEBUG` in Python). Note
that you can set the envvar for the current command only via

    raftel_log_level=10 python src/raftnode.py -H 127.0.0.1 -p 16981
