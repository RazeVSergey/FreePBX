#!/usr/bin/env python3

import argparse
import os
import subprocess
import time

import requests


class Player:
    APLAY = ['aplay', '-q', '-']

    def __init__(self, dummy=False):
        self._dummy = dummy
        self._popen = None
        self._write = None

    def play_chunk(self, chunk: bytearray):
        if self._popen is None:
            self._init()
        self._write(chunk)

    def close(self):
        if self._popen is None:
            pass
        elif isinstance(self._popen, subprocess.Popen):
            self._popen.stdin.close()
            try:
                self._popen.wait(5)
            except subprocess.TimeoutExpired:
                pass
            self._popen.kill()
        else:
            self._popen.close()
        self._popen = None
        self._write = None

    def _init(self):
        if self._dummy:
            self._popen = open(os.devnull, 'wb')
            self._write = self._popen.write
        else:
            self._popen = subprocess.Popen(self.APLAY, stdin=subprocess.PIPE)
            self._write = self._popen.stdin.write


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


def pretty_time(sec) -> str:
    ends = ['sec', 'ms', 'ns']
    max_index = len(ends) - 1
    index = 0
    while sec < 1 and index < max_index and sec:
        sec *= 1000
        index += 1
    result = '{:.2f} {}'.format(sec, ends[index])
    return '{:>10}'.format(result)


def pretty_size(size):
    ends = ['byte', 'KB', 'MB']
    index = 0
    for _ in ends:
        if size < 1024:
            break
        size /= 1024
        index += 1
    result = '{:.2f} {}'.format(size, ends[index])
    return '{:>11}'.format(result)


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=open, help='Text file')
    parser.add_argument('-v', '--voice', default='anna', help='Voice (anna)')
    parser.add_argument('-i', '--ip', default='127.0.0.1', help='Server IP (127.0.0.1)')
    parser.add_argument('-p', '--port', default='8080', help='Server Port (8080)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Don\'t play voice (False')
    parser.add_argument('-c', '--chunks', default=500, type=int, help='Number of characters at a time (500)')
    return parser.parse_args()


def _print(text_size, reply_size, reply_time, write_time, full_time):
    full_time = full_time - write_time
    print('Send: {}, Receive: {}, Reply time: {}, Full time: {}, Play Time: {}'.format(
        text_size, pretty_size(reply_size), pretty_time(reply_time), pretty_time(full_time), pretty_time(write_time)))


def main():
    args = arg_parser()
    play = Player(dummy=args.quiet)
    text_size_all = 0
    reply_size_all = 0
    reply_time_all = 0
    full_time_all = 0
    write_time_all = 0
    counts = 0
    while True:
        text = args.file.read(args.chunks)
        if not text:
            break
        text_size = len(text)
        reply_size = 0
        full_time = time.time()
        reply_time = None
        write_time = 0
        for chunk in RHVoiceREST(text, speaker=args.voice, url='http://{}:{}'.format(args.ip, args.port)).iter_me():
            if reply_time is None:
                reply_time = time.time() - full_time
            reply_size += len(chunk)
            start_time = time.time()
            play.play_chunk(chunk)
            write_time += time.time() - start_time
        full_time = time.time() - full_time
        write_time_all + write_time
        text_size_all += text_size
        reply_size_all += reply_size
        reply_time_all += reply_time
        full_time_all += full_time
        counts += 1
        _print(text_size, reply_size, reply_time, write_time, full_time)
    args.file.close()
    play.close()
    if counts:
        print('Summary:')
        _print(text_size_all, reply_size_all, reply_time_all / counts, write_time_all, full_time_all)
    print('bye.')


if __name__ == '__main__':
    main()
