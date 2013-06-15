# -*- coding: utf-8 -*-
import sys, time, json
from threading import Thread

__all__ = ['RPC', 'NullStream']

class RPC(object):
    # string formatting is faster than json.dumps
    REQUEST_PATTERN  = '["%s",%s,%s]\n'
    RESPONSE_PATTERN = '[[%s],%s]\n'

    def __init__(self, target={}, stdin=None, stdout=None, pattern='%s', listen=True):
        # attributes
        self.target      = target
        self.pattern     = pattern
        self.__callbacks = {}
        self.__count     = 0
        # store streams
        self.__stdin  = stdin or sys.stdin
        self.__stdout = stdout or sys.stdout

        # determine the handler function for incomming calls
        if isinstance(target, dict):
            self.__handler = self.__handle_dict
        elif isinstance(target, object):
            self.__handler = self.__handle_object
        else:
            raise Exception('ERROR: unknown target type: %s' % type(target))

        # a thread that 'asynchronously' listens to stdin
        self.__listener = Thread(target=Listener, args=(self,), kwargs={'stream': self.__stdin})
        self._listen = True
        if listen:
            self.listen()

    def listen(self):
        self.__listener.start()

    def unlisten(self):
        self._listen = False

    def _handle(self, line):
        (name, args, cbid) = RPC.parse(line)
        # reponse of a local call or request of an incomming call?
        if name is None:
            # response
            if cbid and cbid in self.__callbacks:
                # expand error?
                if len(args) and args[0] is not None:
                    args[0] = RPC.expand_error(args[0])
                self.__callbacks[cbid](*args)
                del self.__callbacks[cbid]
        else:
            # request
            data = None
            try:
                result = self.__handler(self.pattern % name, args)
                if cbid != -1:
                    data = RPC.RESPONSE_PATTERN % ('null,%s' % json.dumps(result), cbid)
            except Exception as e:
                data = RPC.RESPONSE_PATTERN % (RPC.flatten_error(e), cbid)
            if data:
                self.__stdout.write(data)
                self.__stdout.flush()

    def __handle_object(self, name, args):
        if not hasattr(self.target, name):
            raise Exception('ERROR: unknown object member: %s' % name)
        return getattr(self.target, name)(*args)

    def __handle_dict(self, name, args):
        if name not in self.target:
            raise Exception('ERROR: unknown dict member: %s' % name)
        return self.target[name](*args)

    def rpc(self, name, args=[], cb=None):
        # create a remote call using the REQUEST_PATTERN
        # store the callback that will be called when the corresponding response is received
        if cb:
            self.__count += 1
            self.__callbacks[self.__count] = cb
        self.__stdout.write(RPC.REQUEST_PATTERN % (name, json.dumps(args), self.__count if cb else -1))
        self.__stdout.flush()
        # unlikely but consistent
        if cb and self.__count == sys.maxint:
            self.__count = 0

    def wrap(self, keys=[]):
        wrapper = Wrapper()
        for key in keys:
            def cb(*args):
                args, cb = list(args), None
                if len(args) and hasattr(args[len(args)-1], '__call__'):
                    cb = args.pop()
                self.rpc(key, args, cb=cb)
            setattr(wrapper, key, cb)
        return wrapper

    @staticmethod
    def parse(line):
        # a line looks like '[name,args,cbid]'
        cbid, args, name = 0, [], None
        try:
            data = json.loads(line)
            cbid = data.pop()
            args = data.pop()
            name = data.pop()
        except:
            pass
        return (name, args, cbid)

    @staticmethod
    def expand_error(err):
        e = Exception(err.get('message', 'ERROR'))
        for key, value in err.items():
            setattr(e, key, value)
        return e

    @staticmethod
    def flatten_error(err):
        if err is None:
            return 'null'
        return '{"message":"%s"}' % err.message

class Wrapper(object):
    pass

class Listener(object):
    def __init__(self, rpc, stream=None, delay=0.002):
        self.__rpc = rpc
        self.__stream = stream or sys.stdin
        self.__listen(delay)

    def __listen(self, delay):
        while self.__rpc._listen:
            line = self.__stream.readline().rstrip()
            if line:
                self.__rpc._handle(line)
            time.sleep(delay)

class NullStream(object):
    def write(self, *args, **kwargs):
        pass

    def read(self, *args, **kwargs):
        pass

    def end(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass
