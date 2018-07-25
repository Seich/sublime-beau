"""
The MIT License (MIT)
Copyright (c) 2015 Clay Sweetser
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from weakref import proxy, WeakKeyDictionary
from sys import version_info
from functools import wraps
import sublime

def get_next_method(generator_instance):
    if version_info[0] >= 3:
        return generator_instance.__next__
    else:
        return generator_instance.next


def send_self(use_proxy):
    """ A decorator which sends a generator a reference to itself via the first
    'yield' used.
    Useful for creating generators that can leverage callback-based functions
    in a linear style, by passing their 'send' method as callbacks.
    Note that by default, the generator instance reference sent is a weakly
    referenced proxy. To override this behavior, pass `False` or
    `use_proxy=False` as the first argument to the decorator.
    """
    _use_proxy = True

    # We either directly call this, or return it, to be called by python's
    # decorator mechanism.
    def _send_self(func):
        @wraps(func)
        def send_self_wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            generator.send(None)
            if _use_proxy:
                generator.send(proxy(generator))
            else:
                generator.send(generator)

        return send_self_wrapper

    # If the argument is a callable, we've been used without being directly
    # passed an arguement by the user, and thus should call _send_self directly
    if callable(use_proxy):
        # No arguments, this is the decorator
        return _send_self(use_proxy)
    else:
        # Someone has used @send_self(bool), and thus we need to return
        # _send_self to be called indirectly.
        _use_proxy = use_proxy
    return _send_self
