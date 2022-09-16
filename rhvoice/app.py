#!/usr/bin/env python3

import os
import sys
from shlex import quote
from urllib import parse

from flask import Flask, request, make_response, Response, stream_with_context, escape
from rhvoice_wrapper import TTS

from rhvoice_rest_cache import CacheWorker

try:
    from rhvoice_tools.text_prepare import text_prepare
except ImportError as err:
    print('Warning! Preprocessing disable: {}'.format(err))

    def text_prepare(text, stress_marker=False, debug=False):
        return text

DEFAULT_VOICE = 'anna'

FORMATS = {'wav': 'audio/wav', 'mp3': 'audio/mpeg', 'opus': 'audio/ogg', 'flac': 'audio/flac'}
DEFAULT_FORMAT = 'mp3'

app = Flask(__name__, static_url_path='')


def voice_streamer_nocache(text, voice, format_, sets):
    with tts.say(text, voice, format_, None, sets or None) as read:
        for chunk in read:
            yield chunk


def voice_streamer_cache(text, voice, format_, sets):
    inst = cache.get(text, voice, format_, sets)
    try:
        for chunk in inst.read():
            yield chunk
    finally:
        inst.release()


def chunked_stream(stream):
    b_break = b'\r\n'
    for chunk in stream:
        yield format(len(chunk), 'x').encode() + b_break + chunk + b_break
    yield b'0' + b_break * 2


def set_headers():
    if CHUNKED_TRANSFER:
        return {'Transfer-Encoding': 'chunked', 'Connection': 'keep-alive'}


@app.route('/say')
def say():
    text = ' '.join([x for x in parse.unquote(request.args.get('text', '')).splitlines() if x])
    voice = request.args.get('voice', DEFAULT_VOICE)
    format_ = request.args.get('format', DEFAULT_FORMAT)

    if voice not in SUPPORT_VOICES:
        return make_response('Unknown voice: \'{}\'. Support: {}.'.format(escape(voice), ', '.join(SUPPORT_VOICES)), 400)
    if format_ not in FORMATS:
        return make_response('Unknown format: \'{}\'. Support: {}.'.format(escape(format_), ', '.join(FORMATS)), 400)
    if not text:
        return make_response('Unset \'text\'.', 400)

    text = quote(text_prepare(text))
    sets = _get_sets(request.args)
    stream = voice_streamer(text, voice, format_, sets)
    if CHUNKED_TRANSFER:
        stream = chunked_stream(stream)
    return Response(stream_with_context(stream), mimetype=FORMATS[format_], headers=set_headers())


def _normalize_set(val):  # 0..100 -> -1.0..1
    try:
        return max(0, min(100, int(val)))/50.0-1
    except (TypeError, ValueError):
        return 0.0


def _get_sets(args):
    keys = {'rate': 'absolute_rate', 'pitch': 'absolute_pitch', 'volume': 'absolute_volume'}
    return {keys[key]: _normalize_set(args[key]) for key in keys if key in args}


def _get_def(any_, test, def_=None):
    if test not in any_ and len(any_):
        return def_ if def_ and def_ in any_ else next(iter(any_))
    return test


def _check_env(word: str) -> bool:
    return word in os.environ and os.environ[word].lower() not in ['no', 'disable', 'false', '']


def _get_cache_path():
    # Включаем поддержку кэша возвращая путь до него, или None
    if _check_env('RHVOICE_FCACHE'):
        path = os.path.join(os.path.abspath(sys.path[0]), 'rhvoice_rest_cache')
        os.makedirs(path, exist_ok=True)
        return path


def cache_init() -> CacheWorker or None:
    path = _get_cache_path()
    dyn_cache = _check_env('RHVOICE_DYNCACHE')
    return CacheWorker(path, tts.say) if path or dyn_cache else None


if __name__ == "__main__":
    tts = TTS()

    cache = cache_init()
    voice_streamer = voice_streamer_cache if cache else voice_streamer_nocache
    CHUNKED_TRANSFER = _check_env('CHUNKED_TRANSFER')
    print('Chunked transfer encoding: {}'.format(CHUNKED_TRANSFER))

    formats = tts.formats
    DEFAULT_FORMAT = _get_def(formats, DEFAULT_FORMAT, 'wav')
    FORMATS = {key: val for key, val in FORMATS.items() if key in formats}

    SUPPORT_VOICES = tts.voices
    DEFAULT_VOICE = _get_def(SUPPORT_VOICES, DEFAULT_VOICE)
    SUPPORT_VOICES = set(SUPPORT_VOICES)

    print('Threads: {}'.format(tts.thread_count))
    app.run(host='0.0.0.0', port=8080, threaded=True)
    if cache:
        cache.join()
    tts.join()
