#-------------------------------------------------------------------------------
# elftools: common/utils.py
#
# Miscellaneous utilities for elftools
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
#-------------------------------------------------------------------------------
from contextlib import contextmanager
from .exceptions import ELFParseError, ELFError, DWARFError
from .py3compat import int2byte
from ..construct import ConstructError


def merge_dicts(*dicts):
    "Given any number of dicts, merges them into a new one."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def bytelist2string(bytelist):
    """ Convert a list of byte values (e.g. [0x10 0x20 0x00]) to a bytes object
        (e.g. b'\x10\x20\x00').
    """
    return b''.join(int2byte(b) for b in bytelist)


def struct_parse(struct, stream, stream_pos=None):
    """ Convenience function for using the given struct to parse a stream.
        If stream_pos is provided, the stream is seeked to this position before
        the parsing is done. Otherwise, the current position of the stream is
        used.
        Wraps the error thrown by construct with ELFParseError.
    """
    try:
        if stream_pos is not None:
            stream.seek(stream_pos)
        return struct.parse_stream(stream)
    except ConstructError as e:
        raise ELFParseError(str(e))


def parse_cstring_from_stream(stream, stream_pos=None):
    """ Parse a C-string from the given stream. The string is returned without
        the terminating \x00 byte. If the terminating byte wasn't found, None
        is returned (the stream is exhausted).
        If stream_pos is provided, the stream is seeked to this position before
        the parsing is done. Otherwise, the current position of the stream is
        used.
        Note: a bytes object is returned here, because this is what's read from
        the binary file.
    """
    if stream_pos is not None:
        stream.seek(stream_pos)
    CHUNKSIZE = 64
    chunks = []
    found = False
    while True:
        chunk = stream.read(CHUNKSIZE)
        end_index = chunk.find(b'\x00')
        if end_index >= 0:
            chunks.append(chunk[:end_index])
            found = True
            break
        else:
            chunks.append(chunk)
        if len(chunk) < CHUNKSIZE:
            break
    return b''.join(chunks) if found else None


def elf_assert(cond, msg=''):
    """ Assert that cond is True, otherwise raise ELFError(msg)
    """
    _assert_with_exception(cond, msg, ELFError)


def dwarf_assert(cond, msg=''):
    """ Assert that cond is True, otherwise raise DWARFError(msg)
    """
    _assert_with_exception(cond, msg, DWARFError)


@contextmanager
def preserve_stream_pos(stream):
    """ Usage:
        # stream has some position FOO (return value of stream.tell())
        with preserve_stream_pos(stream):
            # do stuff that manipulates the stream
        # stream still has position FOO
    """
    saved_pos = stream.tell()
    yield
    stream.seek(saved_pos)


def roundup(num, bits):
    """ Round up a number to nearest multiple of 2^bits. The result is a number
        where the least significant bits passed in bits are 0.
    """
    return (num - 1 | (1 << bits) - 1) + 1


class lazy(object):
    """ A decorator for an instance method which morphs the method to a
        read-only attribute which value is evaluated lazily during first
        access. Then the value is cached and consequently reused. So, it's
        evaluated only once.

        The intent of that a decorator is to implement an attribute which value
        evaluation is a computationally intensive task and its result is always
        constant.

        Because returned reference will be reused many times, it's robust to
        return an immutable instance, like `tuple`, if possible.

        Anther application is to create a related instance which is better to
        reuse across entire program than create multiple copies.
    """

    def __init__(self, getter):
        self._getter = getter
        # Preserve document string.
        if getter.__doc__:
            self.__doc__ = getter.__doc__

    def __get__(self, obj, _):
        getter = self._getter
        val = getter(obj)
        # Add evaluated value to `__dict__` of `obj` to prevent consequent call
        # to `__get__` of this non-data descriptor. Note that direct access to
        # the `__dict__` instead of `getattr` prevents possible conflict with
        # custom `__getattr__` / `__getattribute__` implementation.
        # See: https://docs.python.org/2/howto/descriptor.html
        obj.__dict__[getter.__name__] = val
        return val

#------------------------- PRIVATE -------------------------

def _assert_with_exception(cond, msg, exception_type):
    if not cond:
        raise exception_type(msg)
