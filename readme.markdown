# raftel

An exercise in implementing [Raft](https://raft.github.io/).

## running

Create a virtualenv, install the requirements and then in separate tabs issue:

```
(raft)$ python src/overseer.py 16981
(raft)$ python src/raftnode.py 16981
```

Of course, the port number can be changed.
