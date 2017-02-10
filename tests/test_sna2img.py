import unittest
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, sna2img, VERSION
from skoolkit.graphics import Udg

def mock_run(*args):
    global run_args
    run_args = args

class MockImageWriter:
    def __init__(self, options):
        global image_writer
        image_writer = self
        self.options = options

    def write_image(self, frames, img_file, img_format):
        self.frames = frames
        self.img_format = img_format

class Sna2ImgTest(SkoolKitTestCase):
    def _test_sna2img(self, mock_open, options, data, udgs, scale=1, mask=0, x=0, y=0,
                      width=None, height=None, address=16384, outfile=None, iw_options=None, ftype='scr'):
        if ftype == 'scr':
            infile = self.write_bin_file(data, suffix='.scr')
        else:
            ram = [0] * (address - 16384) + data
            ram.extend((0,) * (49152 - len(ram)))
            if ftype == 'sna':
                infile = self.write_bin_file([0] * 27 + ram, suffix='.sna')
            elif ftype == 'szx':
                infile = self.write_szx(ram)
            elif ftype == 'z80':
                infile = self.write_z80(ram)[1]
        args = '{} {}'.format(options, infile)
        if outfile:
            exp_outfile = outfile
            img_format = outfile[-3:]
            args += ' {}'.format(outfile)
        else:
            img_format = 'png'
            exp_outfile = infile[:-3] + img_format
        output, error = self.run_sna2img(args)
        self.assertEqual([], output)
        self.assertEqual(error, '')
        self.assertEqual(iw_options or {}, image_writer.options)
        self.assertEqual(image_writer.img_format, img_format)
        mock_open.assert_called_with(exp_outfile, 'wb')
        self.assertEqual(len(image_writer.frames), 1)
        frame = image_writer.frames[0]
        self.assertEqual(len(udgs), len(frame.udgs))
        for i, row in enumerate(udgs):
            self.assertEqual(udgs[i], frame.udgs[i], "Row {}/{} differs from expected value".format(i + 1, len(udgs)))
        self.assertEqual(frame.scale, scale)
        self.assertEqual(frame.mask, mask)
        self.assertEqual(frame.x, x)
        self.assertEqual(frame.y, y)
        if width is None:
            width = 8 * len(frame.udgs[0]) * scale
        if height is None:
            height = 8 * len(frame.udgs) * scale
        self.assertEqual(frame.width, width)
        self.assertEqual(frame.height, height)

    def _test_bad_spec(self, option, exp_error):
        scrfile = self.write_bin_file(suffix='.scr')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_sna2img('{} {}'.format(option, scrfile))
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_no_arguments(self):
        output, error = self.run_sna2img(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))

    def test_invalid_option(self):
        output, error = self.run_sna2img('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input file type$'):
            self.run_sna2img('unknown.snap')

    def test_nonexistent_input_file(self):
        infile = 'non-existent.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_sna2img(infile)
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(infile))

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_no_options(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [4] * 768
        exp_udgs = [[Udg(4, [170, 0] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_gif_output(self, mock_open):
        scr = ([85] * 256 + [0] * 256) * 12 + [5] * 768
        exp_udgs = [[Udg(5, [85, 0] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '', scr, exp_udgs, outfile='scr.gif')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_sna_input(self, mock_open):
        scr = ([84] * 256 + [0] * 256) * 12 + [6] * 768
        exp_udgs = [[Udg(6, [84, 0] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '', scr, exp_udgs, ftype='sna')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_szx_input(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [7] * 768
        exp_udgs = [[Udg(7, [170, 0] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '', scr, exp_udgs, ftype='szx')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_z80_input(self, mock_open):
        scr = ([42] * 256 + [0] * 256) * 12 + [8] * 768
        exp_udgs = [[Udg(8, [42, 0] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '', scr, exp_udgs, ftype='z80')

    @patch.object(sna2img, 'run', mock_run)
    def test_options_e_expand(self):
        for option, value in (('-e', 'UDG32768'), ('--expand', 'FONT49152')):
            output, error = self.run_sna2img('{} {} test.scr'.format(option, value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.macro, value)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_e_font(self, mock_open):
        addr = 30000
        attr = 5
        char1 = Udg(attr, [170] * 8)
        char2 = Udg(attr, [129] * 8)
        exp_udgs = [[char1, char2]]
        chars = len(exp_udgs[0])
        scale = 3
        x, y = 1, 2
        width, height = 40, 19
        data = char1.data + char2.data
        macro = 'FONT{},{},{},{}{{{},{},{},{}}}(ignored.gif)'.format(addr, chars, attr, scale, x, y, width, height)
        self._test_sna2img(mock_open, '-e {}'.format(macro), data, exp_udgs, scale, 0, x, y, width, height, addr, ftype='sna')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_e_font_with_text(self, mock_open):
        font_addr = 25000
        text = 'ab'
        addr = font_addr + 8 * (ord(text[0]) - 32)
        char1 = Udg(56, [85] * 8)
        char2 = Udg(56, [240] * 8)
        exp_udgs = [[char1, char2]]
        scale = 2
        data = char1.data + char2.data
        macro = '#FONT:({}){}'.format(text, font_addr)
        self._test_sna2img(mock_open, '--expand {}'.format(macro), data, exp_udgs, scale, address=addr, ftype='sna')

    def test_option_e_font_invalid_parameters(self):
        scrfile = self.write_bin_file(suffix='.scr')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_sna2img('-e FONTx {}'.format(scrfile))
        self.assertEqual(cm.exception.args[0], 'Invalid #FONT macro: No parameters (expected 1)')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_e_scr(self, mock_open):
        df_addr = 24576
        af_addr = 30720
        udg = Udg(2, [170] * 8)
        exp_udgs = [[udg]]
        scale = 2
        scr_x, scr_y = 31, 23
        scr_w, scr_h = 1, 1
        tile_addr = df_addr + 2048 * (scr_y // 8) + 32 * (scr_y % 8) + scr_x
        tile_attr_addr = af_addr + 32 * scr_y + scr_x
        data = [0] * (tile_attr_addr - tile_addr + 1)
        data[0:2048:256] = udg.data
        data[-1] = udg.attr
        macro = 'SCR{},{},{},{},{},{},{}(ignored)'.format(scale, scr_x, scr_y, scr_w, scr_h, df_addr, af_addr)
        self._test_sna2img(mock_open, '-e {}'.format(macro), data, exp_udgs, scale, address=tile_addr, ftype='sna')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_e_scr_cropped(self, mock_open):
        udg = Udg(2, [129] * 8)
        exp_udgs = [[udg]]
        scale = 3
        scr_x, scr_y = 30, 23
        scr_w, scr_h = 1, 1
        x, y = 2, 1
        width, height = 14, 13
        tile_addr = 16384 + 2048 * (scr_y // 8) + 32 * (scr_y % 8) + scr_x
        tile_attr_addr = 22528 + 32 * scr_y + scr_x
        data = [0] * (tile_attr_addr - tile_addr + 1)
        data[0:2048:256] = udg.data
        data[-1] = udg.attr
        crop = '{{{},{},{},{}}}'.format(x, y, width, height)
        macro = '#SCR{},{},{},{},{}{}'.format(scale, scr_x, scr_y, scr_w, scr_h, crop)
        self._test_sna2img(mock_open, '--expand {}'.format(macro), data, exp_udgs, scale, 0, x, y, width, height, tile_addr, ftype='sna')

    def test_option_e_scr_invalid_parameters(self):
        scrfile = self.write_bin_file(suffix='.scr')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_sna2img('-e SCR{{x}} {}'.format(scrfile))
        self.assertEqual(cm.exception.args[0], "Invalid #SCR macro: Cannot parse integer 'x' in parameter string: 'x'")

    @patch.object(sna2img, 'run', mock_run)
    def test_options_f_flip(self):
        for option, value in (('-f', 1), ('--flip', 2)):
            output, error = self.run_sna2img('{} {} test.scr'.format(option, value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.flip, value)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_f_1(self, mock_open):
        scr = [170] * 6144 + [56] * 768
        exp_udgs = [[Udg(56, [85] * 8)] * 32] * 24
        self._test_sna2img(mock_open, '-f 1', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_f_2(self, mock_open):
        scr = ([255] * 256 + [0] * 256) * 12 + [1] * 768
        exp_udgs = [[Udg(1, [0, 255] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '-f 2', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_f_3(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [2] * 768
        exp_udgs = [[Udg(2, [0, 85] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '--flip 3', scr, exp_udgs)

    def test_option_f_invalid_value(self):
        scrfile = self.write_bin_file(suffix='.scr')
        output, error = self.run_sna2img('-f ? {}'.format(scrfile), catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))
        self.assertTrue(error.endswith("error: argument -f/--flip: invalid int value: '?'\n"))

    @patch.object(sna2img, 'run', mock_run)
    def test_options_i_invert(self):
        for option in ('-i', '--invert'):
            output, error = self.run_sna2img('{} test.scr'.format(option))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertTrue(options.invert)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_i(self, mock_open):
        scr = [85] * 6144 + [135, 7] * 384
        udg1 = Udg(7, [170] * 8) # Inverted
        udg2 = Udg(7, [85] * 8)  # Unchanged
        exp_udgs = [[udg1, udg2] * 16] * 24
        self._test_sna2img(mock_open, '-i', scr, exp_udgs)

    @patch.object(sna2img, 'run', mock_run)
    def test_options_n_no_animation(self):
        for option in ('-n', '--no-animation'):
            output, error = self.run_sna2img('{} test.scr'.format(option))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertFalse(options.animated)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_n(self, mock_open):
        scr = [0] * 6144 + [248] * 768
        exp_udgs = [[Udg(248, [0, 0, 0, 0, 0, 0, 0, 0])] * 32] * 24
        exp_iw_options = {'GIFEnableAnimation': 0, 'PNGEnableAnimation': 0}
        self._test_sna2img(mock_open, '-n', scr, exp_udgs, iw_options=exp_iw_options)

    @patch.object(sna2img, 'run', mock_run)
    def test_options_o_origin(self):
        for option, value in (('-o', (3, 4)), ('--origin', (5, 6))):
            output, error = self.run_sna2img('{} {},{} test.scr'.format(option, *value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.origin, value)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_o(self, mock_open):
        scr = [240] * 6144 + [7] * 736 + [4] * 32
        exp_udgs = [[Udg(7, [240] * 8)] * 5] * 5 + [[Udg(4, [240] * 8)] * 5]
        self._test_sna2img(mock_open, '-o 27,18', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_options_o_and_S_together(self, mock_open):
        scr = [7] * 6144
        for n in range(24):
            scr.extend(list(range(n, n + 32)))
        x, y = 4, 5
        w, h = 6, 7
        udg_data = [7] * 8
        exp_udgs = [[Udg(i + j, udg_data) for i in range(x, x + w)] for j in range(y, y + h)]
        options = '-o {},{} -S {}x{}'.format(x, y, w, h)
        self._test_sna2img(mock_open, options, scr, exp_udgs)

    def test_option_o_invalid_values(self):
        scrfile = self.write_bin_file(suffix='.scr')
        for coords in ('x,1', '1,y', 'p,q', '1', '1,2,3'):
            output, error = self.run_sna2img('-o {} {}'.format(coords, scrfile), catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: sna2img.py'))
            self.assertTrue(error.endswith("error: argument -o/--origin: invalid coordinates: '{}'\n".format(coords)))

    @patch.object(sna2img, 'run', mock_run)
    def test_options_p_poke(self):
        for option, value in (('-p', '32768,0'), ('--poke', '30000-30009,5')):
            output, error = self.run_sna2img('{} {} test.scr'.format(option, value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.pokes, [value])

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [255, 0, 0, 0, 0, 0, 0, 0])
        self._test_sna2img(mock_open, '-p 16384,255', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_address_range(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0].data[0] = 255
        self._test_sna2img(mock_open, '-p 16384-16415,255', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_address_range_with_step(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [15] * 8)
        self._test_sna2img(mock_open, '-p 16384-18176-256,15', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_hexadecimal_values(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [15] * 8)
        self._test_sna2img(mock_open, '-p $4000-$4700-$100,$0f', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_with_add_operation(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0].data[0] = 5
        self._test_sna2img(mock_open, '-p 16384-16415,+5', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_with_xor_operation(self, mock_open):
        scr = [255] * 6912
        exp_udgs = [[Udg(255, [255] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0].data[0] = 240
        self._test_sna2img(mock_open, '-p 16384-16415,^15', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_multiple(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [255, 0, 0, 0, 0, 0, 0, 0])
        exp_udgs[0][1] = Udg(0, [170, 0, 0, 0, 0, 0, 0, 0])
        self._test_sna2img(mock_open, '-p 16384,255 --poke 16385,170', scr, exp_udgs)

    def test_option_p_invalid_values(self):
        self._test_bad_spec('-p 1', 'Value missing in poke spec: 1')
        self._test_bad_spec('-p q', 'Value missing in poke spec: q')
        self._test_bad_spec('-p 1,x', 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('-p x,1', 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('-p 1-y,1', 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('-p 1-3-z,1', 'Invalid address range in poke spec: 1-3-z,1')

    @patch.object(sna2img, 'run', mock_run)
    def test_options_r_rotate(self):
        for option, value in (('-r', 1), ('--rotate', 3)):
            output, error = self.run_sna2img('{} {} test.scr'.format(option, value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.rotate, value)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_r_1(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [56] * 768
        exp_udgs = [[Udg(56, [85, 0] * 4)] * 24] * 32
        self._test_sna2img(mock_open, '-r 1', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_r_2(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [1] * 768
        exp_udgs = [[Udg(1, [0, 85] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '-r 2', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_r_3(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [2] * 768
        exp_udgs = [[Udg(2, [0, 170] * 4)] * 24] * 32
        self._test_sna2img(mock_open, '--rotate 3', scr, exp_udgs)

    def test_option_r_invalid_value(self):
        scrfile = self.write_bin_file(suffix='.scr')
        output, error = self.run_sna2img('-r X {}'.format(scrfile), catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))
        self.assertTrue(error.endswith("error: argument -r/--rotate: invalid int value: 'X'\n"))

    @patch.object(sna2img, 'run', mock_run)
    def test_options_s_scale(self):
        for option, value in (('-s ', 2), ('--scale', 3)):
            output, error = self.run_sna2img('{} {} test.scr'.format(option, value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.scale, value)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_s(self, mock_open):
        scr = [0] * 6144 + [1] * 768
        exp_udgs = [[Udg(1, [0] * 8)] * 32] * 24
        self._test_sna2img(mock_open, '-s 2', scr, exp_udgs, 2)

    def test_option_s_invalid_value(self):
        scrfile = self.write_bin_file(suffix='.scr')
        output, error = self.run_sna2img('-s Q {}'.format(scrfile), catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))
        self.assertTrue(error.endswith("error: argument -s/--scale: invalid int value: 'Q'\n"))

    @patch.object(sna2img, 'run', mock_run)
    def test_options_S_size(self):
        for option, value in (('-S ', (5, 6)), ('--size', (7, 8))):
            output, error = self.run_sna2img('{} {}x{} test.scr'.format(option, *value))
            self.assertEqual([], output)
            self.assertEqual(error, '')
            infile, outfile, options = run_args
            self.assertEqual(options.size, value)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_S(self, mock_open):
        scr = [15] * 6144 + [4] * 32 + [7] * 736
        exp_udgs =  [[Udg(4, [15] * 8)] * 5] + [[Udg(7, [15] * 8)] * 5] * 5
        self._test_sna2img(mock_open, '-S 5x6', scr, exp_udgs)

    def test_option_S_invalid_values(self):
        scrfile = self.write_bin_file(suffix='.scr')
        for dimensions in ('Xx1', '1xY', 'pxq', '1', '1x2x3'):
            output, error = self.run_sna2img('-S {} {}'.format(dimensions, scrfile), catch_exit=2)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: sna2img.py'))
            self.assertTrue(error.endswith("error: argument -S/--size: invalid dimensions: '{}'\n".format(dimensions)))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_sna2img(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
