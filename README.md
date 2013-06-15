rpyc-stream
===========

A simple (130 loc), one-file Python RPC System that is based on Streams allowing for cross-language/SSH usage.

This is a port of the [nodejs RPC system by @dominictarr](https://github.com/dominictarr/rpc-stream).

## Examples using SSH

#### Local Code
Python (`local.py`):
```python
# -*- coding: utf-8 -*-
from rpycstream import RPC
from subprocess import Popen, PIPE, STDOUT

def main():
    # python
    worker = Popen(['ssh', 're.mo.te.ip', 'python', 'remote.py'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    # nodejs
    # worker = Popen(['ssh', 're.mo.te.ip', 'node', 'remote.js'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    # pipe into each other
    rpc = RPC(stdin=worker.stdout, stdout=worker.stdin)
    # remote call
    remote = rpc.wrap(['hello'])
    remote.hello('Carlo', cb)
    # which is equivalent to
    rpc.rpc('hello', ['John'], cb)

def cb(err, msg=None):
    if err:
        raise err
    print "msg:", msg

if __name__ == '__main__':
    main()

```
NodeJs (`local.js`):
```javascript
var cp  = require('child_process');
var rpc = require('rpc-stream');

// nodejs
var worker = cp.exec('ssh re.mo.te.ip node remote.js');
// python
// var worker = cp.exec('ssh re.mo.te.ip python remote.py');

var client = rpc();
client.pipe(worker.stdin);
worker.stdout.pipe(client);

client.rpc('hello', ['John'], function(err, msg) {
    if(err) throw err;
    console.log("msg:", msg);
});

```

#### Remote Code

Python (`remote.py`):
```python
# -*- coding: utf-8 -*-
from rpycstream import RPC

class MyClass:
    def hello(self, name):
        return '%s was bitten by a python' % name

if __name__ == '__main__':
    rpc = RPC(target=MyClass())

```

NodeJs (`remote.js`):
```javascript
// see https://github.com/dominictarr/rpc-stream
var rpc = require('rpc-stream');

var server = rpc({
    hello: function(name, cb) {
        cb(null, 'Hello, ' + name);
    }
});

server.pipe(process.stdout);
process.stdin.pipe(server);

```


## Development

- Source hosted at [GitHub](https://github.com/riga/rpyc-stream)
- Report issues, questions, feature requests on
[GitHub Issues](https://github.com/riga/rpyc-stream/issues)


## Authors

Marcel R. ([riga](https://github.com/riga))
