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

def dump(filePath):
    printWidth = 16
    with open(filePath, 'rb') as file:
        ctr = 0
        txt = ' '
        for b in file.read():
            print(hex(b)[2:].zfill(2), end = ' ')
            ctr += 1
            try:
                txt += b.to_bytes(1, 'big').decode('utf-8')
            except:
                txt += '.'
            if ctr == printWidth:
                print(txt)
                ctr = 0
                txt = ' '
        if ctr != 0:
            for i in range(printWidth - ctr):
                print('  ', end = ' ')
            print(txt)

if __name__ == '__main__':
    main()
