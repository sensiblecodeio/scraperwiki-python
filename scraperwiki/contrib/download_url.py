#!/usr/bin/env python
# encoding: utf-8

import requests
from cStringIO import StringIO

__all__ = ['download_url']


_METHODS = {'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'DELETE': requests.delete,
            'HEAD': requests.head,
            'OPTIONS': requests.options}


def download_url(url, method='GET', retry=False, cache_seconds=None, **kwargs):
    """
    Thin wrapper for the 'requests' library. Implements retries for non-fatal
    errors and caching.
    Returns a file-like object containing response.content
    """
    func = _get_function_for_http_method(method)
    if cache_seconds is not None:
        raise NotImplementedError("Can't do cache yet, sorry.")
    if retry:
        raise NotImplementedError("Can't do retries yet, sorry.")
    response = func(url, **kwargs)
    response.raise_for_status()
    return StringIO(response.content)


def _get_function_for_http_method(method):
    try:
        func = _METHODS[method]
    except KeyError:
        raise NotImplementedError(
            "Unsupported method '{}', only support {}".format(
                ','.join(_METHODS.keys())))
    return func
