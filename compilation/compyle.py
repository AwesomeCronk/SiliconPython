import argparse, logging, sys
from types import CodeType
from dis import dis


version = '0.1.0'

NoneType = type(None)

# Logging setup
serializeLogger = logging.getLogger('serialize')
serializeLogger.setLevel(logging.DEBUG)
serializeHandler = logging.StreamHandler()
serializeHandler.setLevel(logging.DEBUG)
serializeFormatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
serializeHandler.setFormatter(serializeFormatter)
serializeLogger.addHandler(serializeHandler)


def getArgs(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='Python source file to disassemble'
    )
    parser.add_argument(
        '-o',
        '--out-file',
        action='store',
        default='<default>',
        help='file to output the compiled program to'
    )
    parser.add_argument(
        '-a',
        '--attributes',
        action='store_true',
        help='list attributes of the compiled program'
    )
    parser.add_argument(
        '-d',
        '--disassemble',
        action='store_true',
        help='disassemble the compiled program'
    )
    parser.add_argument(
        '-x',
        '--hexdump',
        action='store_true',
        help='hexdump the compiled program'
    )
    # parser.add_argument(
    #     '-c',
    #     '--color',
    #     action='store_true',
    #     help='color in different components in the hexdump (will be skipped if -x is not specified)'
    # )
    return parser.parse_args(argv)

def serialize(object):
    logger = logging.getLogger('serialize')
    typeIDs = [
        # Pointers have no type because they are not Python objects
        # They only exist when explicitly needed to facilitate more complex objects
        # pointer,
        CodeType,
        int,
        float,
        str,
        bytes,
        bool,
        tuple,
        list,
        dict,
        NoneType
    ]
    binary = b''

    class pointer():
        def __init__(self, value): assert value < 256 ** 4; self.value = value

    def editPointer(address, target):
        nonlocal binary
        binary = binary[0:address] + int.to_bytes(target, 4, 'big') + binary[address + 4:]

    def addObject(object):
        # nonlocal objects
        nonlocal binary

        if isinstance(object, pointer):     # Complete
            pointerBinary = int.to_bytes(object.value, 4, 'big')

            address = len(binary)
            binary += pointerBinary
            logger.info('Serialized {} at address 0x{:02X}'.format(pointer, address))

        elif isinstance(object, CodeType):
            # Generate a byte string to represent the object, appending any references to other objects to `objects`
            address = len(binary)
            codeBinaryHeader = int.to_bytes(typeIDs.index(CodeType), 1, 'big') + b'spy'
            binary += codeBinaryHeader

            codePointer = addObject(pointer(0))
            namesPointer = addObject(pointer(0))
            constantsPointer = addObject(pointer(0))
            namePointer = addObject(pointer(0))
            filenamePointer = addObject(pointer(0))
            
            editPointer(codePointer, len(binary))
            binary += object.co_code
            editPointer(namesPointer, addObject(object.co_names))
            editPointer(constantsPointer, addObject(object.co_consts))
            editPointer(namePointer, addObject(object.co_name))
            editPointer(filenamePointer, addObject(object.co_filename))

            logger.info('Serialized {} at address 0x{:02X}'.format(CodeType, address))

        elif isinstance(object, int):
            address = len(binary)

            logger.debug('int: {}'.format(object))

            # Calculate size of int (increases in 32B increments as blocks are added)
            size = 32
            while 256 ** size <= abs(object) * 2: size += 32
            numBlocks = size // 32
            # logger.debug('int has size {}B ({} blocks)'.format(size, numBlocks))
            # Max size is 256^3 blocks
            if size >= 32 * (256 ** 3): raise ValueError('Object of type \'int\' is too big')

            # Calculate 2's compliment of integer
            cap = 256 ** size
            compliment = (cap + object) % cap
            complimentBinary = int.to_bytes(compliment, size, 'big')
            # logger.debug('compliment: {}, binary: {}'.format(compliment, complimentBinary))

            # Create binary
            binary += int.to_bytes(typeIDs.index(int), 1, 'big') + int.to_bytes(numBlocks, 3, 'big')
            for i in range(numBlocks):
                complimentBlock = complimentBinary[32 * i: 32 * (i + 1)]
                # logger.debug('iterating block {}: {}'.format(i, complimentBlock))
                binary += complimentBlock
                
                # Pointer to next block (comes right after this one)
                if i + 1 < numBlocks: binary += int.to_bytes(len(binary), 4, 'big')
                # Zero, since there's no next block to point to
                else: binary += b'\x00\x00\x00\x00'

            logger.info('Serialized {} at address 0x{:02X}'.format(int, address))

        elif isinstance(object, str):
            strBinary = object.encode('utf-8')
            length = len(strBinary)
            if length >= 256 ** 4: raise ValueError('Object of type \'str\' is too big')
            strBinary += b'\x00' * (4 - (length % 4))
            strBinary = int.to_bytes(length, 4, 'big') + strBinary

            address = len(binary)
            binary += strBinary
            logger.info('Serialized {} at address 0x{:02X}'.format(str, address))
        
        elif isinstance(object, tuple):
            if len(object) >= 256 ** 4: raise ValueError('Object of type {} is too big'.format(tuple))
            tupleBinary = int.to_bytes(len(object), 4, 'big')
            for item in object:
                itemAddress = addObject(item)
                tupleBinary += int.to_bytes(itemAddress, 4, 'big')

            address = len(binary)
            binary += tupleBinary
            logger.info('Serialized {} at address 0x{:02X}'.format(tuple, address))

        elif isinstance(object, NoneType):
            noneBinary = b'None'

            address = len(binary)
            binary += noneBinary
            logger.info('Serialized {} at address 0x{:02X}'.format(NoneType, address))

        else:
            raise TypeError('Unsupported type: {}'.format(type(object)))

        return address

    addObject(object) # Begin the recursive serialization process
    return binary

def main():
    args = getArgs()
    if args.file.split('.')[-1] != 'py': raise ValueError('<file> should end in ".py".')
    if args.out_file == '<default>': args.out_file = '.'.join(args.file.split('.')[0:-1] + ['spy'])
    elif args.out_file.split('.')[-1] != 'spy': raise ValueError('<out-file> should end in ".spy".')
    
    print('Compyle {} on Python {}'.format(version, sys.version))
    
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


    binary = serialize(code)

    with open(args.out_file, 'wb') as outFile:
        outFile.write(binary)

    if args.hexdump:
        chars = "................................ !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~................................................................................................................................."
        disp = 'Hexdump of .pyc:\n'
        addr = 0
        while True:
            line = binary[addr:addr + 16]
            text = ''
            disp += hex(addr)[2:].zfill(8) + '  '
            if line == b'': break

            for b, byte in enumerate(line):   # Note that byte is an int when you iterate bytes
                disp += hex(byte)[2:].zfill(2) + ' '
                text += chars[byte]
                if b == 7: disp += ' '

            if b < 8: disp += ' '
            for i in range(15 - b): disp += '   '
            disp += ' |' + text + '|\n'
            addr += 16
        disp += '\n'
        print(disp)

    units = ('B', 'kB', 'MB', 'GB', 'TB', 'PB')
    selectedUnit = 0
    count = len(binary)
    while count >= 1024:
        count /= 1024
        selectedUnit += 1
        if selectedUnit == len(units) - 1: break
    else: print('Program size: {}{}'.format(round(count, 2), units[selectedUnit]))


if __name__ == '__main__':
    main()
