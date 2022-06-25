from dis import dis
import argparse, sys, types
import simpleANSI as ansi

def getArgs(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='Python source file to disassemble'
    )
    parser.add_argument(
        '--out-file',
        '-o',
        action='store',
        default='<default>',
        help='file to output the compiled program to'
    )
    parser.add_argument(
        '--attributes',
        '-a',
        action='store_true',
        help='list attributes of the compiled program'
    )
    parser.add_argument(
        '--disassemble',
        '-d',
        action='store_true',
        help='disassemble the compiled program'
    )
    parser.add_argument(
        '--hexdump',
        '-x',
        action='store_true',
        help='hexdump the compiled program'
    )
    parser.add_argument(
        '--color',
        '-c',
        action='store_true',
        help='color in different components in the hexdump (will be skipped if -x is not specified)'
    )
    return parser.parse_args(argv)

def serialize(object):
    objects = []
    binary = b''

    class pointer():
        def __init__(self, value): assert value < 256 ** 4; self.value = value

    def addObject(object):
        nonlocal objects
        nonlocal binary
        address = len(objects)

        if isinstance(object, pointer):
            pointerBinary = int.to_bytes(object.value, 4, 'big')
            binary += pointerBinary

        elif isinstance(object, types.CodeType):
            # Generate a byte string to represent the object, appending any references to other objects to `objects`
            codeAttrs = []
            
            codeAttrs.append(object.co_name.encode())
            codeAttrs.append(object.co_filename.encode())

            codeAttrAddrs = [b'\x00\x00\x00\x00'] * len(codeAttrs)
            # binary needs to be the address block followed by the content

        elif isinstance(object, int):
            size = 4
            while 256 ** size <= abs(object) * 2: size += 4
            if size >= 256 ** 4: raise ValueError('Object of type \'int\' is too big')

        elif isinstance(object, str):
            strBinary = object.encode('utf-8')
            strBinary = b'\x00' * (4 - (len(strBinary) % 4)) + strBinary
            strBinary = int.to_bytes(len(strBinary), 4, 'big') + strBinary

            binary += strBinary
        
        else:
            raise TypeError('Unsupported type {}'.format(type(object)))

        return address

    addObject(object) # Begin the recursive serialization process
    return binary

def main():
    args = getArgs()
    if args.file.split('.')[-1] != 'py': raise ValueError('<file> should end in ".py".')
    if args.out_file == '<default>': args.out_file = '.'.join(args.file.split('.')[0:-1] + ['spy'])
    elif args.out_file.split('.') != 'spy': raise ValueError('<out-file> should end in ".spy".')
    
    print('Python {}'.format(sys.version))
    
    with open(args.file, 'r') as file:
        source = file.read()

    code = compile(source, args.file, 'exec')

    if args.disassemble:
        dis(code)

    attributes = {
        'co_name': code.co_name,
        'co_filename': code.co_filename,
        'co_firstlineno': code.co_firstlineno,
        'co_flags': code.co_flags,
        'co_argcount': code.co_argcount,
        'co_posonlyargcount': code.co_posonlyargcount,
        'co_kwonlyargcount': code.co_kwonlyargcount,
        'co_code': code.co_code,
        'co_names': code.co_names,
        'co_consts': code.co_consts,
        'co_varnames': code.co_varnames,
        'co_freevars': code.co_freevars,
        'co_cellvars': code.co_cellvars,
        'co_nlocals': code.co_nlocals,
        'co_stacksize': code.co_stacksize,
        'co_lnotab': code.co_lnotab
    }

    if args.attributes:
        print('Program attributes:\n' + '\n'.join(['{}: {}'.format(key, attributes[key]) for key in attributes.keys()]))    


    serialize(code)

    if args.hexdump:
        # print(subprocess.run(['hexdump', '-C', args.file + 'c'], capture_output=True).stdout.decode(), end='')

        chars = "................................ !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~................................................................................................................................."
        disp = 'Hexdump of .pyc:\n'
        if args.color:
            disp += ansi.graphics.setGraphicsMode(ansi.graphics.bgColor, ansi.graphics.mode16Bit, 0, 0, 0)
            currentColor = (0, 0, 0)
        addr = 0
        while True:
            line = pycBinary[addr:addr + 16]
            text = ''
            disp += hex(addr)[2:].zfill(8) + '  '
            if line == b'':
                break

            if args.color:
                disp += ansi.graphics.setGraphicsMode(ansi.graphics.bgColor, ansi.graphics.mode16Bit, *currentColor)
                
            for b, byte in enumerate(line):   # Note that byte is an int when you do this
                if args.color:
                    if addr + b in addrs.values():
                        for key in addrs.keys():
                            if addrs[key] == addr + b: break
                        currentColor = colors[key]
                        disp += ansi.graphics.setGraphicsMode(ansi.graphics.bgColor, ansi.graphics.mode16Bit, *currentColor)

                disp += hex(byte)[2:].zfill(2) + ' '
                text += chars[byte]
                if b == 7:
                    disp += ' '

            if b < 8:
                disp += ' '

            for i in range(15 - b):
                disp += '   '

            if args.color:
                disp += ansi.graphics.setGraphicsMode(ansi.graphics.bgColor, ansi.graphics.mode16Bit, 0, 0, 0)
            disp += ' |' + text + '|\n'
            addr += 16
        disp += '\n'
        print(disp)


if __name__ == '__main__':
    main()
