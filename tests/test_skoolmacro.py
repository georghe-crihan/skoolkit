# -*- coding: utf-8 -*-
import re
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolmacro import parse_ints, parse_params, parse_address_range, MacroParsingError

class SkoolMacroTest(SkoolKitTestCase):
    def test_parse_ints_without_kwargs(self):
        # Test with the exact number of parameters
        text = '1,$2,3'
        end, p1, p2, p3 = parse_ints(text, 0, 3)
        self.assertEqual((p1, p2, p3), (1, 2, 3))
        self.assertEqual(end, len(text))

        # Test with default parameter values
        text = '$1,2,3'
        end, p1, p2, p3, p4, p5 = parse_ints(text, 0, 5, (4, 5))
        self.assertEqual((p1, p2, p3, p4, p5), (1, 2, 3, 4, 5))
        self.assertEqual(end, len(text))

        # Test with more than enough parameters
        text = '1,2,3'
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((p1, p2), (1, 2))
        self.assertEqual(end, 3)

        # Test with blank parameters
        text = '1,,$a,'
        end, p1, p2, p3, p4 = parse_ints(text, 0, 4)
        self.assertEqual((p1, p2, p3, p4), (1, None, 10, None))
        self.assertEqual(end, len(text))

        # Test with an empty parameter string
        end, p1 = parse_ints('', 0, 1, (1,))
        self.assertEqual(p1, 1)
        self.assertEqual(end, 0)

        # Test with adjacent non-numeric characters
        junk = 'xyz'
        text = '1,2{0}'.format(junk)
        end, p1, p2 = parse_ints(text, 0, 2)
        self.assertEqual((p1, p2), (1, 2))
        self.assertEqual(end, len(text) - len(junk))

        # Test with arithmetic expressions
        text = '-1,1+1,5-2,10-3*2,2+7/2'
        self.assertEqual([len(text), -1, 2, 3, 4, 5], parse_ints(text, 0, 5))

    def test_parse_ints_with_kwargs(self):
        for param_string, defaults, names, exp_params in (
            ('1,baz=3', (2, 4, 6), ('foo', 'bar', 'baz', 'qux'), [1, 2, 3, 6]),
            ('g=0,h=', (1, 2, 3), ('f', 'g', 'h'), [1, 0, 3]),
        ):
            params = parse_ints(param_string, defaults=defaults, names=names)[1:]
            self.assertEqual(exp_params, params)

    def test_parse_ints_not_enough_parameters(self):
        with self.assertRaisesRegexp(MacroParsingError, re.escape("Not enough parameters (expected 4): '1,2,$3'")):
            parse_ints('1,2,$3', num=4)

    def test_parse_ints_with_kwargs_not_enough_parameters(self):
        with self.assertRaisesRegexp(MacroParsingError, "Missing required argument 'a'"):
            parse_ints('b=4,c=5', defaults=(2, 3), names=('a', 'b', 'c'))

    def test_parse_ints_non_kwarg_after_kwarg(self):
        with self.assertRaisesRegexp(MacroParsingError, "Non-keyword argument after keyword argument: '3'"):
            parse_ints('1,bar=2,3', names=('foo', 'bar', 'baz'))

    def test_parse_ints_unknown_kwarg(self):
        with self.assertRaisesRegexp(MacroParsingError, "Unknown keyword argument: 'qux=2'"):
            parse_ints('foo=1,qux=2', names=('foo', 'bar'))

    def test_parse_params_default_valid_characters(self):
        text = '$5B'
        result = parse_params(text, 0)
        self.assertEqual(result, (len(text), '$5B', None))

        text = '$5B[foo]'
        result = parse_params(text, 0, 'qux')
        self.assertEqual(result, (text.index('['), '$5B', 'qux'))

        text = '1234(foo)'
        result = parse_params(text, 0, 'qux')
        self.assertEqual(result, (len(text), '1234', 'foo'))

        text = '#foo(bar)'
        result = parse_params(text, 0)
        self.assertEqual(result, (len(text), '#foo', 'bar'))

        text = '1,2,3,4(foo)'
        result = parse_params(text, 0)
        self.assertEqual(result, (1, '1', None))

    def test_parse_params_extra_valid_characters(self):
        text = '$5A,2'
        result = parse_params(text, 0, chars=',')
        self.assertEqual(result, (len(text), '$5A,2', None))

        text = '$5A,2.'
        result = parse_params(text, 0, 'xyzzy', chars=',',)
        self.assertEqual(result, (text.index('.'), '$5A,2', 'xyzzy'))

        text = '1;2#blah(hey)'
        result = parse_params(text, 0, 'xyzzy', chars=';',)
        self.assertEqual(result, (len(text), '1;2#blah', 'hey'))

    def test_parse_params_except_chars(self):
        text = '*foo,3;bar,$4:baz*'
        result = parse_params(text, 0, except_chars=' (')
        self.assertEqual(result, (len(text), '*foo,3;bar,$4:baz*', None))

        text = '*foo,3;bar,$4:baz* etc.'
        result = parse_params(text, 0, 'qux', except_chars=' (')
        self.assertEqual(result, (text.index(' '), '*foo,3;bar,$4:baz*', 'qux'))

        text = '*foo,3;bar,$4:baz*(qux)'
        result = parse_params(text, 0, except_chars=' (')
        self.assertEqual(result, (len(text), '*foo,3;bar,$4:baz*', 'qux'))

        text = '*foo,3(bar,$4){baz}* etc.'
        result = parse_params(text, 0, except_chars=' ')
        self.assertEqual(result, (text.index(' '), '*foo,3(bar,$4){baz}*', None))

    def test_parse_address_range(self):
        addr_specs = [
            ('1', 1, [1]),
            ('2x3', 1, [2] * 3),
            ('0-3', 1, [0, 1, 2, 3]),
            ('0-2x3', 1, [0, 1, 2] * 3),
            ('0-6-2', 1, [0, 2, 4, 6]),
            ('0-6-3x2', 1, [0, 3, 6] * 2),
            ('0-49-1-16', 2, [0, 1, 16, 17, 32, 33, 48, 49]),
            ('0-528-8-256x4', 3, [0, 8, 16, 256, 264, 272, 512, 520, 528] * 4),

            ('1+3', 1, [4]),
            ('(1+3)', 1, [4]),
            ('1-1+1', 2, [1, 2]),
            ('1-(3-1)', 2, [1, 2]),
            ('0-16-4*2', 3, [0, 8, 16]),
            ('0-16-(4*2)', 3, [0, 8, 16]),
            ('0-17-1-8+8', 2, [0, 1, 16, 17]),
            ('0-17-1-(8+8)', 2, [0, 1, 16, 17]),
            ('1x7/3', 2, [1, 1]),
            ('1x(1+1)', 2, [1, 1])
        ]
        for addr_spec, width, exp_addresses in addr_specs:
            self.assertEqual(exp_addresses, parse_address_range(addr_spec, width))

if __name__ == '__main__':
    unittest.main()
