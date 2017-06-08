# Copyright 2017 Richard Dymond (rjdymond@gmail.com)
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

from os.path import expanduser

from skoolkit import find_file
from skoolkit.refparser import RefParser

COMMANDS = {
    'sna2skool': {
        'CtlHex': (0, 'ctl_hex'),
        'DefbMod': (1, 'defb_mod'),
        'DefbSize': (8, 'defb_size'),
        'DefbZfill': (0, 'zfill'),
        'DefmSize': (66, 'defm_width'),
        'Erefs': (0, 'write_refs'),
        'LineWidth': (79, 'line_width'),
        'LowerCase': (0, 'asm_lower'),
        'SkoolHex': (0, 'asm_hex'),
        'Text': (0, 'text'),
        'EntryPointRef': ('This entry point is used by the routine at {ref}.', ''),
        'EntryPointRefs': ('This entry point is used by the routines at {refs} and {ref}.', ''),
        'Ref': ('Used by the routine at {ref}.', ''),
        'Refs': ('Used by the routines at {refs} and {ref}.', ''),
        'Title-b': ('Data block at {address}', ''),
        'Title-c': ('Routine at {address}', ''),
        'Title-g': ('Game status buffer entry at {address}', ''),
        'Title-i': ('Ignored', ''),
        'Title-s': ('Unused', ''),
        'Title-t': ('Message at {address}', ''),
        'Title-u': ('Unused', ''),
        'Title-w': ('Data block at {address}', '')
    },
    'skool2html': {
        'AsmLabels': (0, 'asm_labels'),
        'AsmOnePage': (0, 'asm_one_page'),
        'Base': (0, 'base'),
        'Case': (0, 'case'),
        'CreateLabels': (0, 'create_labels'),
        'JoinCss': ('', 'single_css'),
        'OutputDir': ('.', 'output_dir'),
        'Quiet': (0, 'quiet'),
        'RebuildImages': (0, 'new_images'),
        'Search': ('', 'search'),
        'Theme': ('', 'themes'),
        'Time': (0, 'show_timings')
    },
    'skool2asm': {
        'Base': (0, 'base'),
        'Case': (0, 'case'),
        'CreateLabels': (0, 'create_labels'),
        'Quiet': (0, 'quiet'),
        'Warnings': (1, 'warn')
    }
}

def get_config(name):
    config = {k: v[0] for k, v in COMMANDS.get(name, {}).items()}
    skoolkit_ini = find_file('skoolkit.ini', ('', expanduser('~/.skoolkit')))
    if skoolkit_ini:
        ref_parser = RefParser()
        ref_parser.parse(skoolkit_ini)
        for k, v in ref_parser.get_dictionary(name).items():
            if isinstance(config.get(k), int):
                try:
                    config[k] = int(v)
                except ValueError:
                    pass
            else:
                config[k] = v
    return config

def update_options(name, options, specs, config=None):
    def_config = COMMANDS.get(name, {})
    for spec in specs:
        param, sep, value = spec.partition('=')
        if sep and param in def_config:
            def_value, attr_name = def_config[param]
            try:
                if isinstance(def_value, int):
                    value = int(value)
                if attr_name:
                    setattr(options, attr_name, value)
                if config:
                    config[param] = value
            except ValueError:
                pass
