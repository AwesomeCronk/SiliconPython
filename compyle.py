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

    colors = {
        'co_argcount':      (0, 0, 100),
        'co_posonlyargcount': (0, 50, 75),
        'co_kwonlyargcount': (0, 75, 50),
        'co_nlocals':       (0, 75, 0),
        'co_codelen':       (128, 0, 0),
        'co_code':          (200, 20, 20),
        'co_consts':        (20, 100, 0),
        'co_filename':      (0, 0, 0),
        'co_firstlineno':   (0, 0, 0),
        'co_flags':         (0, 0, 0),
        'co_name':          (150, 75, 0),
        'co_names':         (0, 0, 0),
        'co_stacksize':     (0, 0, 0),
        'co_varnames':      (0, 0, 0)
    }

    addrs = {}
    addrs['co_argcount']        = 0x11
    addrs['co_posonlyargcount'] = 0x15
    addrs['co_kwonlyargcount']  = 0x19
    addrs['co_nlocals']         = 0x1d
    addrs['co_stacksize']       = 0x21
    addrs['co_flags']           = 0x25
    addrs['co_codelen']         = 0x2a
    addrs['co_code']            = 0x2e
    # addrs['co_consts']          = addrs['co_code'] + int.from_bytes(pycBinary[addrs['co_codelen']:addrs['co_codelen'] + 4], 'little')
    
    ## Serialize things (this is where it gets complicated)

    objects = []
    def addObject(object):
        nonlocal objects
        if isinstance(object, types.CodeType):
            # Generate a byte string to represent the object, appending any references to other objects to `objects`
            codeAttrs = []
            
            codeAttrs.append(object.co_name.encode())
            codeAttrs.append(object.co_filename.encode())

            codeAttrAddrs = [b'\x00\x00\x00\x00'] * len(codeAttrs)
            # binary needs to be the address block followed by the content

        elif isinstance(object, int):
            pass

    addObject(code) # Begin the recursive serialization process

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
