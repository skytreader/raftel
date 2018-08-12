# raftel

An exercise in implementing [Raft](https://raft.github.io/).

## Running

Create a virtualenv, install the requirements and then in separate tabs issue:

```
(raft)$ python src/overseer.py 16981
(raft)$ python src/raftnode.py 16981
```

Of course, the port number can be changed.

## Type Checking

This makes use of [mypy](http://mypy-lang.org) to add type annotations to the
code. To check that your modifications are type-consistent:

    mypy --ignore-missing-imports src/*.py

We ignore missing imports because gevent does not have mypy types as of this
writing.
