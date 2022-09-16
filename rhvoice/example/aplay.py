#!/usr/bin/env python3

import subprocess
import requests
import argparse
import sys

"""
Usage:
    ls --help | ./aplay.py
    echo 'Hello world' | ./aplay.py
    ./aplay.py 'Hello world'
"""


class RHVoiceREST:
    BUFF_SIZE = 1024

    def __init__(self, text, audio_format='wav', speaker='anna', url='http://127.0.0.1:8080'):
        self._url = '{}/say'.format(url)
        self._params = {
            'text': text,
            'format': audio_format,
            'voice': speaker
        }
        self._data = None
        self._request()

    def _request(self):
        try:
            self._rq = requests.get(self._url, params=self._params, stream=True, timeout=60)
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
            raise RuntimeError(str(e))
        if not self._rq.ok:
            raise RuntimeError('{}: {}'.format(self._rq.status_code, self._rq.reason))
        self._data = self._rq.iter_content

    def iter_me(self):
        if self._data is None:
            raise RuntimeError('No data')
        for chunk in self._data(chunk_size=self.BUFF_SIZE):
            yield chunk

    def save_fp(self, fp):
        for chunk in self.iter_me():
            fp.write(chunk)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('text', nargs='?', default=sys.stdin, help='Text-To-Speech')
    parser.add_argument('-p', default='anna', metavar='voice', help='Voice')
    parser.add_argument('-u', default='http://127.0.0.1:8080', metavar='url', help='rhvoice-rest url')
    args = parser.parse_args()
    popen = subprocess.Popen(['aplay', '-q', '-'], stdin=subprocess.PIPE)
    try:
        if isinstance(args.text, str):
            RHVoiceREST(text=args.text, speaker=args.p, url=args.u).save_fp(popen.stdin)
        else:
            for line in args.text.readlines():
                line = ' '.join([x for x in line.splitlines() if x])
                if line:
                    RHVoiceREST(text=line, speaker=args.p, url=args.u).save_fp(popen.stdin)
    except RuntimeError as e:
        print(e)
        popen.stdin.close()
        exit(1)
    else:
        popen.stdin.close()
        popen.wait(300)


if __name__ == '__main__':
    main()
