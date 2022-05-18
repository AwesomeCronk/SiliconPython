from dis import dis
from py_compile import compile
import argparse, os, sys

def getArgs(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='file to disassemble'
    )
    return parser.parse_args(argv)

def main():
    args = getArgs()
    print('Python {}'.format(sys.version))
    with open(args.file, 'r') as file:
        dis(file.read())
    compile(args.file, args.file + 'c')
    os.system('hexdump -C {}'.format(args.file + 'c'))

if __name__ == '__main__':
    main()
