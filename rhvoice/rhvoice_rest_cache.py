import collections
import hashlib
import os
import tempfile
import threading
import time


class BaseInstance:
    def read(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError


class CacheWorker(threading.Thread):
    # TODO: Make file operations thread safe
    def __init__(self, cache_path, say):
        self._run = False
        self._path = cache_path
        self._lifetime = self._get_lifetime()
        self._noatime = False
        self._tmp = tempfile.gettempdir()
        self._dyn_cache = DynCache(say)
        print('Dynamic cache: enable.')
        if self._path:
            print('File cache: {}'.format(self._path))
        if self._path and self._lifetime:
            super().__init__()
            self._check_interval = 60 * 60
            self._wait = threading.Event()
            self._run = True
            self._noatime = self._noatime_enable()
            self.start()

    def _noatime_enable(self):
        test = os.path.join(self._path, 'atime.test')
        with open(test, 'wb') as fp:
            fp.write(b'test')
        old_atime = os.stat(test).st_atime
        time.sleep(3)
        with open(test, 'rb') as fp:
            _ = fp.read()
        new_atime = os.stat(test).st_atime
        os.remove(test)
        if old_atime == new_atime:
            print('FS mount with noatime, atime will update manually')
        return old_atime == new_atime

    @staticmethod
    def _get_lifetime():
        try:
            lifetime = int(os.environ.get('RHVOICE_FCACHE_LIFETIME', 0))
        except (TypeError, ValueError):
            return 0
        return lifetime if lifetime > 0 else 0

    def join(self, timeout=None):
        if self._run:
            self._run = False
            self._wait.set()
            super().join(timeout)

    def run(self):
        print('Cache lifetime: {} hours'.format(self._lifetime))
        self._lifetime *= 60 * 60
        while self._run:
            current_time = time.time()
            for file in os.listdir(self._path):
                file_path = os.path.join(self._path, file)
                if os.path.isfile(file_path):
                    last_read = os.path.getatime(file_path)
                    diff = current_time - last_read
                    if diff > self._lifetime:
                        self.remove(file_path)
            self._wait.wait(self._check_interval)

    def _update_atime(self, path):
        if self._noatime:  # Обновляем atime и mtime вручную
            timestamp = time.time()
            os.utime(path, times=(timestamp, timestamp))

    def file_found(self, path):
        if os.path.isfile(path):
            self._update_atime(path)
            return True
        return False

    @staticmethod
    def remove(path):
        try:
            os.remove(path)
        except OSError as e:
            print('Error deleting {}: {}'.format(path, e))

    def get(self, text, voice, format_, sets) -> BaseInstance:
        str_sets = '.'.join(str(sets.get(k, 0.0)) for k in ['absolute_rate', 'absolute_pitch', 'absolute_volume'])
        name = hashlib.sha1('.'.join([text, voice, format_, str_sets]).encode()).hexdigest() + '.cache'
        path = os.path.join(self._path, name) if self._path else None
        if path and self.file_found(path):
            return FileCacheReaderInstance(path)
        return self._dyn_cache.get(name, path, text, voice, format_, sets)


class DynCache:
    def __init__(self, say):
        self._say = say
        self._lock = threading.Lock()
        self._data = {}

    def get(self, name: str, path: str, text, voice, format_, sets):
        def cb():
            with self._lock:
                del self._data[name]

        with self._lock:
            if name not in self._data:
                self._data[name] = DynCacheInstance(path, self._say(text, voice, format_, None, sets or None), cb)
            result = self._data[name]
        return result.acquire()


class DynCacheInstance(threading.Thread, BaseInstance):
    def __init__(self, path, generator, cb):
        threading.Thread.__init__(self)
        self._path = path
        self._tts = generator
        self._cb = cb
        self._mutex = threading.Condition(threading.Lock())
        self._lock = threading.Lock()
        self._deque = collections.deque()
        self.ended = False
        self.locked = False
        self._users = 0
        self.start()

    def run(self):
        try:
            with self._tts as read:
                for chunk in read:
                    self._deque.append(chunk)
                    if self.locked:
                        return
                    with self._mutex:
                        self._mutex.notify_all()

                self.ended = True
            self._save()
        finally:
            with self._mutex:
                self._mutex.notify_all()

    def read(self):
        pos = 0
        with self._mutex:
            while True:
                size = len(self._deque)
                while pos < size:
                    yield self._deque[pos]
                    pos += 1
                if self.ended:
                    if pos == len(self._deque):
                        break
                    else:
                        continue
                self._mutex.wait()

    def acquire(self):
        with self._lock:
            self._users += 1
            return self

    def release(self):
        with self._lock:
            self._users -= 1
            if not (self._users or self.locked):
                self.locked = True
                self._cb()
                self.join(timeout=10)

    def _save(self):
        if self._path:
            try:
                with open(self._path, 'wb') as fd:
                    fd.write(b''.join(self._deque))
            except OSError as e:
                print('Write error {}: {}'.format(self._path, e))


class FileCacheReaderInstance(BaseInstance):
    def __init__(self, path):
        self._path = path

    def read(self):
        try:
            with open(self._path, 'rb') as f:
                while True:
                    chunk = f.read(2048)
                    if not chunk:
                        break
                    yield chunk
        except OSError as e:
            print('Read error {}: {}'.format(self._path, e))

    def release(self):
        pass
