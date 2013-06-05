# -*- coding: utf-8 -*-
import os
import unittest
import textwrap

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2asm, write_text, SkoolKitError, VERSION

TEST_NO_OPTIONS_SKOOL = """; @start
; @org=24593

; Let's test some @ofix directives
c24593 NOP
; @ofix=LD A,C
 24594 LD A,B
; @ofix-begin
 24595 LD B,A
; @ofix+else
 24595 LD B,C
; @ofix+end

; Let's test some @bfix directives
c24596 NOP
; @bfix=LD C,B
 24597 LD C,A
; @bfix-begin
 24598 LD D,A
; @bfix+else
 24598 LD D,B
; @bfix+end

; Let's test the @rfix block directive
c24599 NOP
; @rfix-begin
 24600 LD E,A
; @rfix+else
 24600 LD E,B
; @rfix+end

; Let's test the @ssub directive
; @ssub=JP (HL)
c24601 RET

; Let's test the @rsub block directive
c24602 NOP
; @rsub-begin
 24603 LD A,0
; @rsub+else
 24603 XOR A
; @rsub+end
"""

TEST_d_SKOOL = """; @start
; Begin
c$8000 RET
"""

TEST_t_SKOOL = """; @start
; @org=24576

; Routine
c24576 RET
"""

TEST_l_SKOOL = """; @start
; @org=24576

; Routine
; @label=DOSTUFF
c24576 NOP
"""

TEST_i_SKOOL = """; @start
; Do nothing
c50000 RET ; Return
"""

TEST_f_SKOOL = """; @start
; Let's test some @ofix directives
c24593 NOP
; @ofix=LD A,C
 24594 LD A,B
; @ofix-begin
 24595 LD B,A
; @ofix+else
 24595 LD B,C
; @ofix+end

; Let's test some @bfix directives
c24596 NOP
; @bfix=LD C,B
 24597 LD C,A
; @bfix-begin
 24598 LD D,A
; @bfix+else
 24598 LD D,B
; @bfix+end

; Let's test the @rfix block directive
c24599 NOP
; @rfix-begin
 24600 LD E,A
; @rfix+else
 24600 LD E,B
; @rfix+end
"""

TEST_s_SKOOL = """; @start
; Let's test the @ssub directive
; @ssub=JP (HL)
c24601 RET
"""

TEST_r_SKOOL = """; @start
; Let's test some @ofix directives
c24593 NOP
; @ofix=LD A,C
 24594 LD A,B
; @ofix-begin
 24595 LD B,A
; @ofix+else
 24595 LD B,C
; @ofix+end

; Let's test some @bfix directives
c24596 NOP
; @bfix=LD C,B
 24597 LD C,A
; @bfix-begin
 24598 LD D,A
; @bfix+else
 24598 LD D,B
; @bfix+end

; Let's test the @rfix block directive
c24599 NOP
; @rfix-begin
 24600 LD E,A
; @rfix+else
 24600 LD E,B
; @rfix+end

; Let's test the @ssub directive
; @ssub=JP (HL)
c24601 RET

; Let's test the @rsub block directive
c24602 NOP
; @rsub-begin
 24603 LD A,0
; @rsub+else
 24603 XOR A
; @rsub+end
"""

TEST_Q_SKOOL = """; @start
; Do nothing
c30000 RET
"""

TEST_W_SKOOL = """; This skool file generates warnings

; @start
; Routine at 24576
;
; Used by the routine at 24576.
c24576 JP 24576
"""

TEST_U_SKOOL = """; @start
; Start the game
; @label=start
c49152 nop
"""

TEST_D_SKOOL = """; @start
; Begin
c$8000 JP $ABCD
"""

TEST_H_SKOOL = """; @start
; Begin
c$8000 JP 56506
"""

TEST_C_SKOOL = """; @start
; Begin
c32768 JR 32770

; End
c32770 JR 32768
"""

TEST_NO_HTML_ESCAPE_SKOOL = """; @start
; Text
t24576 DEFM "&<>" ; a <= b & b >= c
"""

TEST_MACRO_EXPANSION_SKOOL = """; @start
; Data
b$6003 DEFB 123 ; #REGa=0
 $6004 DEFB $23 ; '#'
"""

TEST_WRITER_SKOOL = """; @start
; @writer={0}
; Begin
c24576 RET
"""

TEST_ASM_WRITER_MODULE = """from skoolkit.skoolasm import AsmWriter

class TestAsmWriter(AsmWriter):
    def write(self):
        self.write_line('{0}')
"""

TEST_PROPERTIES_SKOOL = """; @start
; @set-{0}={1}
; Data
b40000 DEFB 0 ; Comment
"""

TEST_WARNINGS_PROPERTY_SKOOL = """; This skool file generates warnings

; @start
; @set-warnings={0}
; Routine at 25000
;
; Used by the routine at 25000.
c25000 JP 25000
"""

TEST_LINE_WIDTH_SKOOL = """; @start
; @set-line-width={0}
; Routine
c49152 RET ; This is a fairly long instruction comment, which makes it suitable
           ; for testing various line widths
"""

TEST_LABEL_COLONS_SKOOL = """; @start
; @set-label-colons={0}
; Routine
; @label=DOSTUFF
c50000 RET
"""

TEST_COMMENT_WIDTH_MIN_SKOOL = """; @start
; @set-comment-width-min={0}
; Data
c35000 DEFB 255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255 ; {1}
"""

def mock_run(*args):
    global run_args
    run_args = args

class TestAsmWriter:
    def __init__(self, *args):
        pass

    def write(self):
        write_text('OK')

class Skool2AsmTest(SkoolKitTestCase):
    def test_default_option_values(self):
        self.mock(skool2asm, 'run', mock_run)
        skool2asm.main(('test.skool',))
        fname, be_quiet, properties, parser_mode, writer_mode = run_args
        self.assertEqual(fname, 'test.skool')
        case = base = None
        asm_mode = 1
        warn = True
        fix_mode = 0
        create_labels = False
        self.assertEqual(parser_mode, (case, base, asm_mode, warn, fix_mode, create_labels))
        self.assertTrue(len(properties) == 0)
        self.assertEqual(writer_mode, (False, warn))
        self.assertFalse(be_quiet)

    def test_no_arguments(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_skool2asm()
        self.assertEqual(cm.exception.args[0], 2)

    def test_invalid_option(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_skool2asm('-x')
        self.assertEqual(cm.exception.args[0], 2)

    def test_invalid_option_value(self):
        for args in ('-i ABC', '-f +'):
            with self.assertRaises(SystemExit) as cm:
                self.run_skool2asm(args)
            self.assertEqual(cm.exception.args[0], 2)

    def test_no_options(self):
        asm = self.get_asm(skool=TEST_NO_OPTIONS_SKOOL)
        self.assertEqual(asm[0], '  ORG 24593') # no crlf, tabs or lower case
        self.assertEqual(asm[4], '  LD A,B')    # No @ofix
        self.assertEqual(asm[5], '  LD B,A')    # @ofix-
        self.assertEqual(asm[9], '  LD C,A')    # No @bfix
        self.assertEqual(asm[10], '  LD D,A')   # @bfix-
        self.assertEqual(asm[14], '  LD E,A')   # @rfix-
        self.assertEqual(asm[17], '  RET')      # No @ssub
        self.assertEqual(asm[21], '  LD A,0')   # @rsub-

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2asm(option, err_lines=True, catch_exit=True)
            self.assertEqual(len(output), 0)
            self.assertEqual(len(error), 1)
            self.assertEqual(error[0], 'SkoolKit {}'.format(VERSION))

    def test_option_q(self):
        skoolfile = self.write_text_file(TEST_Q_SKOOL, suffix='.skool')
        for option in ('-q', '--quiet'):
            output, error = self.run_skool2asm('{0} {1}'.format(option, skoolfile))
            self.assertEqual(error, '')

    def test_option_w(self):
        skoolfile = self.write_text_file(TEST_W_SKOOL, suffix='.skool')
        for option in ('-w', '--no-warnings'):
            output, error = self.run_skool2asm('-q {0} {1}'.format(option, skoolfile))
            self.assertEqual(error, '')

    def test_option_d(self):
        for option in ('-d', '--crlf'):
            asm = self.get_asm(option, TEST_d_SKOOL, strip_cr=False)
            self.assertEqual(asm[0][-1], '\r')

    def test_option_t(self):
        for option in ('-t', '--tabs'):
            asm = self.get_asm(option, TEST_t_SKOOL)
            self.assertEqual(asm[0], '\tORG 24576')
            self.assertEqual(asm[3], '\tRET')

    def test_option_l(self):
        for option in ('-l', '--lower'):
            asm = self.get_asm(option, TEST_l_SKOOL)
            self.assertEqual(asm[0], '  org 24576')
            self.assertEqual(asm[3], 'DOSTUFF:') # Labels unaffected
            self.assertEqual(asm[4], '  nop')

    def test_option_u(self):
        for option in ('-u', '--upper'):
            asm = self.get_asm(option, TEST_U_SKOOL)
            self.assertEqual(asm[1], 'start:') # Labels unaffected
            self.assertEqual(asm[2], '  NOP')

    def test_option_D(self):
        for option in ('-D', '--decimal'):
            asm = self.get_asm(option, TEST_D_SKOOL)
            self.assertEqual(asm[1], '  JP 43981')

    def test_option_H(self):
        for option in ('-H', '--hex'):
            asm = self.get_asm(option, TEST_H_SKOOL)
            self.assertEqual(asm[1], '  JP $DCBA')

    def test_option_i(self):
        width = 30
        for option in ('-i', '--inst-width'):
            asm = self.get_asm('{0} {1}'.format(option, width), TEST_i_SKOOL)
            self.assertEqual(asm[1].find(';'), width + 3)

    def test_option_f0(self):
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 0'.format(option), TEST_f_SKOOL)
            self.assertEqual(asm[2], '  LD A,B')
            self.assertEqual(asm[3], '  LD B,A')
            self.assertEqual(asm[7], '  LD C,A')
            self.assertEqual(asm[8], '  LD D,A')
            self.assertEqual(asm[12], '  LD E,A')

    def test_option_f1(self):
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 1'.format(option), TEST_f_SKOOL)
            self.assertEqual(asm[2], '  LD A,C')
            self.assertEqual(asm[3], '  LD B,C')
            self.assertEqual(asm[7], '  LD C,A')
            self.assertEqual(asm[8], '  LD D,A')
            self.assertEqual(asm[12], '  LD E,A')

    def test_option_f2(self):
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 2'.format(option), TEST_f_SKOOL)
            self.assertEqual(asm[2], '  LD A,C')
            self.assertEqual(asm[3], '  LD B,C')
            self.assertEqual(asm[7], '  LD C,B')
            self.assertEqual(asm[8], '  LD D,B')
            self.assertEqual(asm[12], '  LD E,A')

    def test_option_f3(self):
        for option in ('-f', '--fixes'):
            asm = self.get_asm('{0} 3'.format(option), TEST_f_SKOOL)
            self.assertEqual(asm[2], '  LD A,C')
            self.assertEqual(asm[3], '  LD B,C')
            self.assertEqual(asm[7], '  LD C,B')
            self.assertEqual(asm[8], '  LD D,B')
            self.assertEqual(asm[12], '  LD E,B')

    def test_option_s(self):
        for option in ('-s', '--ssub'):
            asm = self.get_asm(option, TEST_s_SKOOL)
            self.assertEqual(asm[1], '  JP (HL)')

    def test_option_r(self):
        for option in ('-r', '--rsub'):
            asm = self.get_asm(option, TEST_r_SKOOL)
            self.assertEqual(asm[2], '  LD A,C')   # @ofix
            self.assertEqual(asm[3], '  LD B,C')   # @ofix+
            self.assertEqual(asm[7], '  LD C,A')   # No @bfix
            self.assertEqual(asm[8], '  LD D,A')   # @bfix-
            self.assertEqual(asm[12], '  LD E,A')  # @rfix-
            self.assertEqual(asm[15], '  JP (HL)') # @ssub
            self.assertEqual(asm[19], '  XOR A')   # @rsub+

    def test_option_c(self):
        for option in ('-c', '--labels'):
            asm = self.get_asm(option, TEST_C_SKOOL)
            self.assertEqual(asm[1], 'L32768:')
            self.assertEqual(asm[2], '  JR L32770')
            self.assertEqual(asm[5], 'L32770:')
            self.assertEqual(asm[6], '  JR L32768')

    def test_writer(self):
        # Test a writer with no module or package name
        writer = 'AbsoluteAsmWriter'
        skoolfile = self.write_text_file(TEST_WRITER_SKOOL.format(writer), suffix='.skool')
        try:
            self.run_skool2asm(skoolfile)
            self.fail()
        except SkoolKitError as e:
            self.assertEqual(e.args[0], "Invalid class name: '{0}'".format(writer))

        # Test a writer in a nonexistent module
        writer = 'nonexistentmodule.AsmWriter'
        skoolfile = self.write_text_file(TEST_WRITER_SKOOL.format(writer), suffix='.skool')
        try:
            self.run_skool2asm(skoolfile)
            self.fail()
        except SkoolKitError as e:
            err_t = "Failed to import class nonexistentmodule.AsmWriter: No module named {0}nonexistentmodule{0}"
            self.assertTrue(e.args[0] in (err_t.format(''), err_t.format("'")))

        # Test a writer that doesn't exist
        writer = 'test_skool2asm.NonexistentAsmWriter'
        skoolfile = self.write_text_file(TEST_WRITER_SKOOL.format(writer), suffix='.skool')
        try:
            self.run_skool2asm(skoolfile)
            self.fail()
        except SkoolKitError as e:
            self.assertEqual(e.args[0], "No class named 'NonexistentAsmWriter' in module 'test_skool2asm'")

        # Test a writer that exists
        asm = self.get_asm(skool=TEST_WRITER_SKOOL.format('test_skool2asm.TestAsmWriter'))
        self.assertEqual(asm[0], 'OK')

        # Test a writer in a module that is not in the search path
        message = 'Testing TestAsmWriter'
        module = self.write_text_file(TEST_ASM_WRITER_MODULE.format(message), suffix='.py')
        module_path = os.path.dirname(module)
        module_name = os.path.basename(module)[:-3]
        writer = '{0}:{1}.TestAsmWriter'.format(module_path, module_name)
        asm = self.get_asm(skool=TEST_WRITER_SKOOL.format(writer))
        self.assertEqual(asm[0], message)

    def test_tab_property(self):
        property_name = 'tab'

        # tab=0
        asm = self.get_asm(skool=TEST_PROPERTIES_SKOOL.format(property_name, '0'))
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment')

        # tab=1
        asm = self.get_asm(skool=TEST_PROPERTIES_SKOOL.format(property_name, '1'))
        self.assertEqual(asm[1], '\tDEFB 0                  ; Comment')

        # tab=0, overridden by '-t' option
        asm = self.get_asm('-t', skool=TEST_PROPERTIES_SKOOL.format(property_name, '0'))
        self.assertEqual(asm[1], '\tDEFB 0                  ; Comment')

    def test_crlf_property(self):
        property_name = 'crlf'

        # crlf=0
        asm = self.get_asm(skool=TEST_PROPERTIES_SKOOL.format(property_name, '0'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment')

        # crlf=1
        asm = self.get_asm(skool=TEST_PROPERTIES_SKOOL.format(property_name, '1'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment\r')

        # crlf=0, overridden by '-d' option
        asm = self.get_asm('-d', skool=TEST_PROPERTIES_SKOOL.format(property_name, '0'), strip_cr=False)
        self.assertEqual(asm[1], '  DEFB 0                  ; Comment\r')

    def test_indent_property(self):
        for indent in (1, 5, 'x'):
            asm = self.get_asm(skool=TEST_PROPERTIES_SKOOL.format('indent', indent))
            try:
                indent_size = int(indent)
            except ValueError:
                indent_size = 2
            self.assertEqual(asm[1], '{0}DEFB 0                  ; Comment'.format(' ' * indent_size))

    def test_warnings_property(self):
        # warnings=0 (SkoolParser warnings only)
        skoolfile = self.write_text_file(TEST_WARNINGS_PROPERTY_SKOOL.format(0), suffix='.skool')
        output, error = self.run_skool2asm('-q {0}'.format(skoolfile))
        self.assertEqual(error, 'WARNING: Found no label for operand: 25000 JP 25000\n')

        # warnings=1 (SkoolParser and AsmWriter warnings)
        skoolfile = self.write_text_file(TEST_WARNINGS_PROPERTY_SKOOL.format(1), suffix='.skool')
        output, error = self.run_skool2asm('-q {0}'.format(skoolfile), err_lines=True)
        self.assertEqual(len(error), 5)
        self.assertEqual(error[0], 'WARNING: Found no label for operand: 25000 JP 25000')
        self.assertEqual(error[1], 'WARNING: Comment contains address (25000) not converted to a label:')
        self.assertEqual(error[2], '; Routine at 25000')
        self.assertEqual(error[3], 'WARNING: Comment contains address (25000) not converted to a label:')
        self.assertEqual(error[4], '; Used by the routine at 25000.')

        # warnings=1, overridden by '-w' option (no warnings)
        skoolfile = self.write_text_file(TEST_WARNINGS_PROPERTY_SKOOL.format(1), suffix='.skool')
        output, error = self.run_skool2asm('-q -w {0}'.format(skoolfile))
        self.assertEqual(error, '')

    def test_instruction_width_property(self):
        property_name = 'instruction-width'

        for value in (20, 25, 30, 'z'):
            try:
                width = int(value)
            except ValueError:
                width = 23
            asm = self.get_asm(skool=TEST_PROPERTIES_SKOOL.format(property_name, value))
            self.assertEqual(asm[1], '  {0} ; Comment'.format('DEFB 0'.ljust(width)))

        # instruction-width=27, overridden by '-i'
        for width in (20, 25, 30):
            asm = self.get_asm('-i {0}'.format(width), skool=TEST_PROPERTIES_SKOOL.format(property_name, 27))
            self.assertEqual(asm[1], '  {0} ; Comment'.format('DEFB 0'.ljust(width)))

    def test_line_width_property(self):
        indent = ' ' * 25
        instruction = '  RET'.ljust(len(indent))
        comment = 'This is a fairly long instruction comment, which makes it suitable for testing various line widths'
        for width in (65, 80, 95, 'x'):
            asm = self.get_asm(skool=TEST_LINE_WIDTH_SKOOL.format(width))
            try:
                line_width = int(width)
            except ValueError:
                line_width = 79
            comment_lines = textwrap.wrap(comment, line_width - len(instruction) - 3)
            exp_lines = [instruction + ' ; ' + comment_lines[0]]
            for comment_line in comment_lines[1:]:
                exp_lines.append('{0} ; {1}'.format(indent, comment_line))
            for line_no, exp_line in enumerate(exp_lines, 1):
                self.assertEqual(asm[line_no], exp_line)

    def test_label_colons_property(self):
        for label_colons in ('0', '1', '2', 'x'):
            asm = self.get_asm(skool=TEST_LABEL_COLONS_SKOOL.format(label_colons))
            try:
                expect_colon = int(label_colons)
            except ValueError:
                expect_colon = True
            exp_label = 'DOSTUFF{0}'.format(':' if expect_colon else '')
            self.assertEqual(asm[1], exp_label)

    def test_comment_width_min_property(self):
        line_width = 79
        comment = 'This comment should have the designated minimum width'
        for width in (10, 15, 20, 'x'):
            asm = self.get_asm(skool=TEST_COMMENT_WIDTH_MIN_SKOOL.format(width, comment))
            try:
                comment_width_min = int(width)
            except ValueError:
                comment_width_min = 10
            instruction, sep, comment_line = asm[1].partition(';')
            instr_width = len(instruction)
            indent = ' ' * instr_width
            comment_width = line_width - 2 - instr_width
            comment_lines = textwrap.wrap(comment, max((comment_width, comment_width_min)))
            exp_lines = [instruction + '; ' + comment_lines[0]]
            for comment_line in comment_lines[1:]:
                exp_lines.append('{0}; {1}'.format(indent, comment_line))
            for line_no, exp_line in enumerate(exp_lines, 1):
                self.assertEqual(asm[line_no], exp_line)

    def test_no_html_escape(self):
        asm = self.get_asm(skool=TEST_NO_HTML_ESCAPE_SKOOL)
        self.assertEqual(asm[1], '  DEFM "&<>"              ; a <= b & b >= c')

    def test_macro_expansion(self):
        asm = self.get_asm(skool=TEST_MACRO_EXPANSION_SKOOL)
        self.assertEqual(asm[1], '  DEFB 123                ; A=0')
        self.assertEqual(asm[2], "  DEFB $23                ; '#'")

    def get_asm(self, args='', skool='', out_lines=True, err_lines=True, strip_cr=True):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        output, error = self.run_skool2asm('{0} {1}'.format(args, skoolfile), out_lines, err_lines, strip_cr)
        self.assertEqual('Wrote ASM to stdout', error[-1][:19], 'Error(s) while running skool2asm.main() with args "{0}"'.format(args))
        return output

if __name__ == '__main__':
    unittest.main()
