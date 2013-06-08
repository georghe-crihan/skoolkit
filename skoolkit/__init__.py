# -*- coding: utf-8 -*-

# Copyright 2011-2013 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import textwrap

VERSION = '3.4b1'
ENCODING = 'utf-8'
PY3 = sys.version_info >= (3,)
PACKAGE_DIR = os.path.dirname(__file__)

def error(msg):
    sys.stderr.write('ERROR: {0}\n'.format(msg))
    sys.exit(1)

def warn(msg):
    sys.stderr.write('WARNING: {0}\n'.format(msg))

def info(msg):
    sys.stderr.write('{0}\n'.format(msg))

def show_package_dir():
    write_line(PACKAGE_DIR)
    sys.exit(0)

def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()

def write_line(text):
    sys.stdout.write('{0}\n'.format(text))

def write_text(text):
    sys.stdout.write(text)

def wrap(text, width):
    return textwrap.wrap(text, width, break_long_words=False, break_on_hyphens=False)

def get_int_param(num_str):
    if num_str.startswith('$'):
        return int(num_str[1:], 16)
    return int(num_str)

def parse_int(num_str, default=None):
    try:
        return get_int_param(num_str)
    except ValueError:
        return default

def get_chr(code):
    return chr(code) if PY3 else unichr(code).encode(ENCODING)

def get_class(name_spec):
    if ':' in name_spec:
        path, name = name_spec.split(':')
        if path not in sys.path:
            sys.path.insert(0, os.path.expanduser(path))
    else:
        name = name_spec
    if '.' not in name:
        raise SkoolKitError("Invalid class name: '{0}'".format(name))
    elements = name.split('.')
    mod_name = '.'.join(elements[:-1])
    cls_name = elements[-1]
    try:
        m = __import__(mod_name, globals(), locals(), [cls_name])
    except ImportError as e:
        raise SkoolKitError("Failed to import class {0}: {1}".format(name, e.args[0]))
    try:
        return getattr(m, cls_name)
    except AttributeError:
        raise SkoolKitError("No class named '{0}' in module '{1}'".format(cls_name, mod_name))

def open_file(fname):
    if fname == '-':
        return sys.stdin
    try:
        return open(fname, 'r')
    except IOError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise

def read_bin_file(fname):
    try:
        with open(fname, 'rb') as f:
            return bytearray(f.read()) # PY: 'return f.read()' in Python 3
    except IOError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise

class SkoolKitError(Exception):
    pass

class SkoolParsingError(SkoolKitError):
    pass
