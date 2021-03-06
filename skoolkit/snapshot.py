# Copyright 2009-2013, 2015-2020 Richard Dymond (rjdymond@gmail.com)
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

import textwrap
import zlib

from skoolkit import SkoolKitError, get_int_param, read_bin_file
from skoolkit.components import get_snapshot_reader

# http://www.worldofspectrum.org/faq/reference/z80format.htm
Z80_REGISTERS = {
    'a': 0,
    'f': 1,
    'bc': 2,
    'c': 2,
    'b': 3,
    'hl': 4,
    'l': 4,
    'h': 5,
    'sp': 8,
    'i': 10,
    'r': 11,
    'de': 13,
    'e': 13,
    'd': 14,
    '^bc': 15,
    '^c': 15,
    '^b': 16,
    '^de': 17,
    '^e': 17,
    '^d': 18,
    '^hl': 19,
    '^l': 19,
    '^h': 20,
    '^a': 21,
    '^f': 22,
    'iy': 23,
    'ix': 25,
    'pc': 32
}

def can_read(fname):
    """
    Return whether this snapshot reader can read the file `fname`.
    """
    return fname[-4:].lower() in ('.sna', '.z80', '.szx')

def get_snapshot(fname, page=None):
    """
    Read a snapshot file and produce a 65536-element list of byte values.

    :param fname: The snapshot filename.
    :param page: The page number to map to addresses 49152-65535 (C000-FFFF).
                 This is relevant only when reading a 128K snapshot file.
    :return: A 65536-element list of byte values.
    """
    if not can_read(fname):
        raise SnapshotError("{}: Unknown file type".format(fname))
    data = read_bin_file(fname)
    ext = fname[-4:].lower()
    if ext == '.sna':
        ram = _read_sna(data, page)
    elif ext == '.z80':
        ram = _read_z80(data, page)
    elif ext == '.szx':
        ram = _read_szx(data, page)
    if len(ram) != 49152:
        raise SnapshotError("RAM size is {0}".format(len(ram)))
    mem = [0] * 16384
    mem.extend(ram)
    return mem

def make_snapshot(fname, org, start=0, end=65536, page=None):
    snapshot_reader = get_snapshot_reader()
    if snapshot_reader.can_read(fname):
        return snapshot_reader.get_snapshot(fname, page), max(16384, start), end
    ram = read_bin_file(fname, 65536)
    if org is None:
        org = 65536 - len(ram)
    mem = [0] * 65536
    mem[org:org + len(ram)] = ram
    return mem, max(org, start), min(end, org + len(ram))

def set_z80_registers(z80, *specs):
    for spec in specs:
        reg, sep, val = spec.lower().partition('=')
        if sep:
            if reg.startswith('^'):
                size = len(reg) - 1
            else:
                size = len(reg)
            if reg == 'pc' and z80[6:8] != [0, 0]:
                offset = 6
            else:
                offset = Z80_REGISTERS.get(reg, -1)
            if offset >= 0:
                try:
                    value = get_int_param(val, True)
                except ValueError:
                    raise SkoolKitError("Cannot parse register value: {}".format(spec))
                lsb, msb = value % 256, (value & 65535) // 256
                if size == 1:
                    z80[offset] = lsb
                elif size == 2:
                    z80[offset:offset + 2] = [lsb, msb]
                if reg == 'r' and lsb & 128:
                    z80[12] |= 1
            else:
                raise SkoolKitError('Invalid register: {}'.format(spec))

def print_reg_help(short_option=None):
    options = ['--reg name=value']
    if short_option:
        options.insert(0, '-{} name=value'.format(short_option))
    reg_names = ', '.join(sorted(Z80_REGISTERS))
    print("""
Usage: {}

Set the value of a register or register pair. For example:

  --reg hl=32768
  --reg b=17

To set the value of an alternate (shadow) register, use the '^' prefix:

  --reg ^hl=10072

Recognised register names are:

  {}
""".format(', '.join(options), '\n  '.join(textwrap.wrap(reg_names, 70))).strip())

def set_z80_state(z80, *specs):
    for spec in specs:
        name, sep, val = spec.lower().partition('=')
        try:
            if name == 'iff':
                z80[27] = z80[28] = get_int_param(val) & 255
            elif name == 'im':
                z80[29] &= 252 # Clear bits 0 and 1
                z80[29] |= get_int_param(val) & 3
            elif name == 'border':
                z80[12] &= 241 # Clear bits 1-3
                z80[12] |= (get_int_param(val) & 7) * 2 # Border colour
            else:
                raise SkoolKitError("Invalid parameter: {}".format(spec))
        except ValueError:
            raise SkoolKitError("Cannot parse integer: {}".format(spec))

def print_state_help(short_option=None):
    options = ['--state name=value']
    if short_option:
        options.insert(0, '-{} name=value'.format(short_option))
    print("""
Usage: {}

Set a hardware state attribute. Recognised names and their default values are:

  border - border colour (default=0)
  iff    - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
  im     - interrupt mode (default=1)
""".format(', '.join(options)).strip())

def make_z80_ram_block(data, page):
    block = []
    prev_b = None
    count = 0
    for b in data:
        if b == prev_b or prev_b is None:
            prev_b = b
            if count < 255:
                count += 1
                continue
        if count > 4 or (count > 1 and prev_b == 237):
            block.extend((237, 237, count, prev_b))
        elif prev_b == 237:
            block.extend((237, b))
            prev_b = None
            count = 0
            continue
        else:
            block.extend((prev_b,) * count)
        prev_b = b
        count = 1
    if count > 4 or (count > 1 and prev_b == 237):
        block.extend((237, 237, count, prev_b))
    else:
        block.extend((prev_b,) * count)
    length = len(block)
    return [length % 256, length // 256, page] + block

def make_z80v3_ram_blocks(ram):
    blocks = []
    for bank, data in ((5, ram[:16384]), (1, ram[16384:32768]), (2, ram[32768:49152])):
        blocks.extend(make_z80_ram_block(data, bank + 3))
    return blocks

def write_z80v3(fname, ram, registers, state):
    z80 = [0] * 86
    z80[30] = 54 # Indicate a v3 Z80 snapshot
    set_z80_registers(z80, 'i=63', 'iy=23610', *registers)
    set_z80_state(z80, 'iff=1', 'im=1', *state)
    with open(fname, 'wb') as f:
        f.write(bytes(z80 + make_z80v3_ram_blocks(ram)))

def move(snapshot, param_str):
    params = param_str.split(',', 2)
    if len(params) < 3:
        raise SkoolKitError("Not enough arguments in move spec (expected 3): {}".format(param_str))
    try:
        src, length, dest = [get_int_param(p, True) for p in params]
    except ValueError:
        raise SkoolKitError('Invalid integer in move spec: {}'.format(param_str))
    snapshot[dest:dest + length] = snapshot[src:src + length]

def poke(snapshot, param_str):
    try:
        addr, val = param_str.split(',', 1)
    except ValueError:
        raise SkoolKitError("Value missing in poke spec: {}".format(param_str))
    try:
        if val.startswith('^'):
            value = get_int_param(val[1:], True)
            poke_f = lambda b: b ^ value
        elif val.startswith('+'):
            value = get_int_param(val[1:], True)
            poke_f = lambda b: (b + value) & 255
        else:
            value = get_int_param(val, True)
            poke_f = lambda b: value
    except ValueError:
        raise SkoolKitError('Invalid value in poke spec: {}'.format(param_str))
    try:
        values = [get_int_param(i, True) for i in addr.split('-', 2)]
    except ValueError:
        raise SkoolKitError('Invalid address range in poke spec: {}'.format(param_str))
    addr1, addr2, step = values + [values[0], 1][len(values) - 1:]
    for a in range(addr1, addr2 + 1, step):
        snapshot[a] = poke_f(snapshot[a])

def _read_sna(data, page=None):
    if len(data) <= 49179 or page is None:
        return data[27:49179]
    paged_bank = data[49181] & 7
    banks = [5, 2, paged_bank]
    for i in range(8):
        if i not in banks:
            banks.append(i)
    page_index = banks.index(page)
    if page_index < 3:
        index = 27 + page_index * 16384
    else:
        index = 49183 + (page_index - 3) * 16384
    return data[27:32795] + data[index:index + 16384]

def _read_z80(data, page=None):
    if sum(data[6:8]) > 0:
        version = 1
    else:
        version = 2
    if version == 1:
        header_size = 30
    else:
        header_size = 32 + data[30]
    header = data[:header_size]
    if version == 1:
        if header[12] & 32:
            return _decompress_block(data[header_size:-4])
        return data[header_size:]
    machine_id = data[34]
    extension = ()
    if (version == 2 and machine_id < 2) or (version == 3 and machine_id in (0, 1, 3)):
        if data[37] & 128:
            banks = (5,) # 16K
            extension = [0] * 32768
        else:
            banks = (5, 1, 2) # 48K
    else:
        if page is None:
            page = data[35] & 7
        banks = (5, 2, page) # 128K
    return _decompress(data[header_size:], banks, extension)

def _read_szx(data, page=None):
    extension = ()
    machine_id = data[6]
    if machine_id == 0:
        banks = (5,) # 16K
        extension = [0] * 32768
    elif machine_id == 1:
        banks = (5, 2, 0) # 48K
    else:
        if page is None:
            specregs = _get_zxstblock(data, 8, 'SPCR')[1]
            if specregs is None:
                raise SnapshotError("SPECREGS (SPCR) block not found")
            page = specregs[1] & 7
        banks = (5, 2, page) # 128K
    pages = {}
    for bank in banks:
        pages[bank] = None
    i = 8
    while 1:
        i, rampage = _get_zxstblock(data, i, 'RAMP')
        if rampage is None:
            break
        page = rampage[2]
        if page in pages:
            ram = rampage[3:]
            if rampage[0] & 1:
                try:
                    ram = zlib.decompress(ram)
                except zlib.error as e:
                    raise SnapshotError("Error while decompressing page {0}: {1}".format(page, e.args[0]))
            if len(ram) != 16384:
                raise SnapshotError("Page {0} is {1} bytes (should be 16384)".format(page, len(ram)))
            pages[page] = ram
    return _concatenate_pages(pages, banks, extension)

def _get_zxstblock(data, index, block_id):
    block = None
    while index < len(data) and block is None:
        size = data[index + 4] + 256 * data[index + 5] + 65536 * data[index + 6] + 16777216 * data[index + 7]
        dw_id = ''.join([chr(b) for b in data[index:index + 4]])
        if dw_id == block_id:
            block = data[index + 8:index + 8 + size]
        index += 8 + size
    return index, block

def _concatenate_pages(pages, banks, extension):
    ram = []
    for bank in banks:
        if pages[bank] is None:
            raise SnapshotError("Page {0} not found".format(bank))
        ram.extend(pages[bank])
    ram.extend(extension)
    return ram

def _decompress(ramz, banks, extension):
    pages = {}
    for bank in banks:
        pages[bank] = None
    j = 0
    while j < len(ramz):
        length = ramz[j] + 256 * ramz[j + 1]
        page = ramz[j + 2] - 3
        if length == 65535:
            if page in pages:
                pages[page] = ramz[j + 3:j + 16387]
            j += 16387
        else:
            if page in pages:
                pages[page] = _decompress_block(ramz[j + 3:j + 3 + length])
            j += 3 + length
    return _concatenate_pages(pages, banks, extension)

def _decompress_block(ramz):
    block = []
    i = 0
    while i < len(ramz):
        b = ramz[i]
        i += 1
        if b == 237:
            c = ramz[i]
            i += 1
            if c == 237:
                length, byte = ramz[i], ramz[i + 1]
                if length == 0:
                    raise SnapshotError("Found ED ED 00 {0:02X}".format(byte))
                block += [byte] * length
                i += 2
            else:
                block += [b, c]
        else:
            block.append(b)
    return block

# API (SnapshotReader)
class SnapshotError(SkoolKitError):
    """Raised when an error occurs while reading a snapshot file."""
