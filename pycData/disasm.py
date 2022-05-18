from dis import dis
from py_compile import compile
import argparse, marshal, subprocess, sys

def getArgs(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='Python source file to disassemble'
    )
    parser.add_argument(
        '--marshal',
        '-m',
        action='store_true',
        help='use marshal to get attributes of the file'
    )
    parser.add_argument(
        '--hexdump',
        '-x',
        action='store_true',
        help='`hexdump -C` the compiled file'
    )
    parser.add_argument(
        '--color',
        '-c',
        action='store_true',
        help='color in different components in the marshal output and hexdump (will be skipped if -h is not specified)'
    )
    return parser.parse_args(argv)

def main():
    args = getArgs()
    print('Python {}'.format(sys.version))
    
    with open(args.file, 'r') as file:
        dis(file.read())

    compile(args.file, args.file + 'c')
    
    if args.marshal:
        with open(args.file + 'c', 'rb') as pycFile:
            pycFile.seek(16)
            code = marshal.loads(pycFile.read())
        attributesMarshal = {
            'co_argcount': code.co_argcount,
            'co_code': code.co_code,
            'co_consts': code.co_consts,
            'co_filename': code.co_filename,
            'co_firstlineno': code.co_firstlineno,
            'co_flags': code.co_flags,
            'co_name': code.co_name,
            'co_names': code.co_names,
            'co_nlocals': code.co_nlocals,
            'co_stacksize': code.co_stacksize,
            'co_varnames': code.co_varnames
        }
        print('marshal finds:\n{}'.format('\n'.join(['{}: {}'.format(key, attributesMarshal[key]) for key in attributesMarshal.keys()])))
    
    if args.hexdump:
        # print(subprocess.run(['hexdump', '-C', args.file + 'c'], capture_output=True).stdout.decode(), end='')
        print(dump(args.file + 'c'))

def dump(path):
    chars = "................................ !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~................................................................................................................................."
    disp = ''
    addr = 0
    with open(path, 'rb') as file:
        while True:
            line = file.read(16)
            text = ''
            disp += hex(addr)[2:].zfill(8) + '  '
            if line == b'':
                break

            for b, byte in enumerate(line):   # Note that byte is an int when you do this
                disp += hex(byte)[2:].zfill(2) + ' '
                text += chars[byte]
                if b == 7:
                    disp += ' '

            if b < 8:
                disp += ' '

            for i in range(15 - b):
                disp += '   '

            disp += ' |' + text + '|\n'
            addr += 16
    disp += '\n'
    return disp


if __name__ == '__main__':
    main()
