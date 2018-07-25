
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
from .send_self import send_self, get_next_method
import sublime

def loop_status_msg(frames, speed, view=None, key=''):
    """ Creates and runs a generator which continually sets the status
    text to a series of strings. Returns a function which, when called,
    stops the generator.
    Useful for creating 'animations' in the status bar.
    Parameters:
        `frames`: A sequence of strings displayed in order on the status bar
        `speed`: Delay between frame shifts, in seconds
        `view`: View to set the status on. If not provided, then
                sublime.status_message is used.
        `key`: Key used when setting the status on a view. Ignored if no
               view is given.
    To stop the loop, the returned function must be called with no arguments,
    or a single argument for which `bool(arg) == true`. As a special condition,
    if the first argument is a callable for which `bool(arg) == True`, then
    the argument will be called after the last animation loop has finished.
    If for the the given argument, `bool(arg) == False`, nothing will
    happen.
    """
    flag = _FlagObject()
    flag.flag = False

    @send_self
    def loop_status_generator():
        self = yield

        # Get the correct status function
        set_timeout = sublime.set_timeout
        if view is None:
            set_status = sublime.status_message
        else:
            set_status = lambda f: view.set_status(key, f)

        # Main loop
        while not flag.flag:
            for frame in frames:
                set_status(frame)
                yield set_timeout(get_next_method(self), int(speed * 1000))
        if callable(flag.flag):
            flag.flag()
        set_status('')
        yield

    def stop_status_loop(callback=True):
        flag.flag = callback

    sublime.set_timeout(loop_status_generator, 0)
    return stop_status_loop


def static_status_msg(frame, speed=1):
    """ Creates and runs a generator which displays an updatable message in
    the current window.
    Parameters:
        `frame`: Initial message text
        `speed`: Update speed, in seconds. Faster speed means faster message
                 update, but more CPU usage. Slower update speed means less
                 CPU usage, but slower message update.
    To update the loop, call the returned function with the new message.
    To stop displaying the message, call the returned function with 'true' or
    a callable as the second parameter.
    """
    flag = _FlagObject()
    flag.flag = False
    flag.frame = frame

    @send_self
    def static_status_generator():
        self = yield

        # Get the correct status function
        set_timeout = sublime.set_timeout
        set_status = sublime.status_message

        # Main loop
        while not flag.flag:
            set_status(flag.frame)
            yield set_timeout(get_next_method(self), int(speed * 1000))
        if callable(flag.flag):
            flag.flag()
        yield

    def update_status_loop(message, stop=False):
        flag.flag = stop
        flag.frame = message

    sublime.set_timeout(static_status_generator, 0)
    return update_status_loop


class _FlagObject(object):

    """
    Used with loop_status_msg to signal when a status message loop should end.
    """
    __slots__ = ['flag', 'frame']

    def __init__(self):
        self.flag = False
        self.frame = None
