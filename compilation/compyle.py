import argparse, logging, sys, struct
from types import CodeType
from dis import dis


version = '0.4.0'

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
        bool,
        int,
        float,
        str,
        bytes,
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
        # `address * 4` is because SiliconPython uses 32 bit words, so incrementing the address by one increments by 4 bytes
        binary = binary[0:address * 4] + int.to_bytes(target, 4, 'big') + binary[(address + 1) * 4:]

    def addObject(object):
        # nonlocal objects
        nonlocal binary

        if isinstance(object, pointer):     # Complete
            pointerBinary = int.to_bytes(object.value, 4, 'big')

            address = len(binary) // 4
            binary += pointerBinary
            logger.info('Serialized <pointer> at 0x{:08X}'.format(address))

        elif isinstance(object, CodeType):
            # Generate a byte string to represent the object, appending any references to other objects to `objects`
            address = len(binary) // 4
            codeBinaryHeader = int.to_bytes(typeIDs.index(CodeType), 1, 'big') + b'spy'
            binary += codeBinaryHeader

            codePointer = addObject(pointer(0))
            namesPointer = addObject(pointer(0))
            constantsPointer = addObject(pointer(0))
            namePointer = addObject(pointer(0))
            filenamePointer = addObject(pointer(0))
            
            editPointer(codePointer, len(binary) // 4)
            binary += object.co_code
            editPointer(namesPointer, addObject(object.co_names))
            editPointer(constantsPointer, addObject(object.co_consts))
            editPointer(namePointer, addObject(object.co_name))
            editPointer(filenamePointer, addObject(object.co_filename))

            logger.info('Serialized <CodeType> at 0x{:08X}'.format(address))

        elif isinstance(object, bool):      # Complete
            address = len(binary) // 4
            header = int.to_bytes(typeIDs.index(bool), 1, 'big') + (b'\xff\xff\xff' if object else b'\x00\x00\x00')
            binary += header
            logger.info('Serialized <bool> at 0x{:08X}'.format(address))

        elif isinstance(object, int):       # Complete
            address = len(binary) // 4

            # logger.debug('int: {}'.format(object))

            # Calculate size of int (increases in 32B increments as blocks are added)
            blockSize = 16
            size = blockSize
            while 256 ** size <= abs(object) * 2: size += blockSize
            numBlocks = size // blockSize
            # logger.debug('int has size {}B ({} blocks)'.format(size, numBlocks))
            # Max size is 256^3 blocks
            if size >= blockSize * (256 ** 3): raise ValueError('Object of type \'int\' is too big')

            # Calculate 2's compliment of integer
            cap = 256 ** size
            compliment = (cap + object) % cap
            complimentBinary = int.to_bytes(compliment, size, 'big')
            # logger.debug('compliment: {}, binary: {}'.format(compliment, complimentBinary))

            # Create binary
            binary += int.to_bytes(typeIDs.index(int), 1, 'big') + int.to_bytes(numBlocks, 3, 'big')
            for i in range(numBlocks):
                complimentBlock = complimentBinary[blockSize * i: blockSize * (i + 1)]
                # logger.debug('iterating block {}: {}'.format(i, complimentBlock))
                binary += complimentBlock
                
                # Pointer to next block (comes right after this one because Compyle assumes clean memory)
                if i + 1 < numBlocks: binary += int.to_bytes(len(binary) // 4, 4, 'big')
                # Zero, since there's no next block to point to
                else: binary += b'\x00\x00\x00\x00'

            logger.info('Serialized <int> at 0x{:08X}'.format(address))

        elif isinstance(object, float):     # Complete
            address = len(binary) // 4

            header = int.to_bytes(typeIDs.index(float), 1, 'big') + b'\x00\x00\x00'

            binary += header
            binary += struct.pack('!d', object)
            logger.info('Serialized <float> at 0x{:08X}'.format(address))

        elif isinstance(object, str):       # Complete
            address = len(binary) // 4

            strBinary = object.encode('utf-8')
            blockSize = 32
            length = len(strBinary)
            if length >= 256 ** 3: raise ValueError('Object of type \'str\' is too big')
            
            # Pad data so it lines up later
            pad = length % blockSize
            # If/else prevents adding a full empty block at the end
            strBinary += b'\x00' * ((blockSize - pad) if pad != 0 else 0)
            
            header = int.to_bytes(typeIDs.index(str), 1, 'big') + int.to_bytes(length, 3, 'big')
            binary += header

            numBlocks = len(strBinary) // blockSize
            for i in range(numBlocks):
                strBlock = strBinary[blockSize * i:blockSize * (i + 1)]
                binary += strBlock

                # Pointer to next block (comes right after this one)
                if i + 1 < numBlocks: binary += int.to_bytes(len(binary) // 4, 4, 'big')
                # Zero, since there's no next block to point to
                else: binary += b'\x00\x00\x00\x00'


            logger.info('Serialized <str> at 0x{:08X}'.format(address))

        elif isinstance(object, bytes):     # Complete
            address = len(binary) // 4

            bytesBinary = object
            blockSize = 32
            length = len(bytesBinary)
            if length >= 256 ** 3: raise ValueError('Object of type \'bytes\' is too big')
            
            # Pad data so it lines up later
            pad = length % blockSize
            # If/else prevents adding a full empty block at the end
            bytesBinary += b'\x00' * ((blockSize - pad) if pad != 0 else 0)
            
            header = int.to_bytes(typeIDs.index(bytes), 1, 'big') + int.to_bytes(length, 3, 'big')
            binary += header

            numBlocks = len(bytesBinary) // blockSize
            for i in range(numBlocks):
                bytesBlock = bytesBinary[blockSize * i:blockSize * (i + 1)]
                binary += bytesBlock

                # Pointer to next block (comes right after this one)
                if i + 1 < numBlocks: binary += int.to_bytes(len(binary) // 4, 4, 'big')
                # Zero, since there's no next block to point to
                else: binary += b'\x00\x00\x00\x00'


            logger.info('Serialized <bytes> at 0x{:08X}'.format(address))
        
        elif isinstance(object, tuple):     # Complete
            address = len(binary) // 4
            header = int.to_bytes(typeIDs.index(tuple), 1, 'big') + int.to_bytes(len(object), 3, 'big')
            binary += header

            if len(object) >= 256 ** 3: raise ValueError('Object of type {} is too big'.format(tuple))
            
            pointers = []
            
            # Allocate pointers
            for i in range(len(object)):
                pointers.append(addObject(pointer(0)))

            # Add each item and edit the pointer to it
            for i, o in enumerate(object):
                editPointer(pointers[i], addObject(o))
            
            logger.info('Serialized <tuple> at 0x{:08X}'.format(address))

        elif isinstance(object, list):
            address = len(binary) // 4
            header = int.to_bytes(typeIDs.index(list), 1, 'big') + int.to_bytes(len(object), 3, 'big')
            binary += header

            if len(object) >= 256 ** 3: raise ValueError('Object of type {} is too big'.format(tuple))
            blockSize = 8  # Not bytes in this case, but items
            pointers = []
            
            # Fill blocks
            for i in range(len(object)):
                if i and (i % blockSize == 0):
                    binary += int.to_bytes(len(binary) // 4, 4, 'big')   # Pointer to next block
                pointers.append(addObject(pointer(0)))

            # Pad last block
            pad = (blockSize - (len(object) % blockSize)) % blockSize
            # logger.debug('pad {} pointers ({})'.format(pad, b'\x00\x00\x00\x00' * pad))
            binary += b'\x00\x00\x00\x00' * pad
            if pad: binary += b'\x00\x00\x00\x00'   # Next block pointer, for consistency's sake

            # Add each item and edit the pointer to it
            for i in range(len(object)):
                editPointer(pointers[i], addObject(object[i]))
            
            logger.info('Serialized <list> at 0x{:08X}'.format(address))

        elif isinstance(object, NoneType):  # Complete
            address = len(binary) // 4
            binary += int.to_bytes(typeIDs.index(NoneType), 1, 'big') + b'\x00\x00\x00'
            logger.info('Serialized <NoneType> at 0x{:08X}'.format(address))

        else:
            raise TypeError('Unsupported type: {}'.format(type(object)))

        return address

    addObject(object) # Begin the recursive serialization process
    return binary

def hexdump(binary):
    chars = "................................ !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~................................................................................................................................."
    disp = ''
    addr = 0
    while True:
        line = binary[addr:addr + 16]
        text = ''
        if line == b'': break
        if disp != '': disp += '\n'
        disp += '{:08X}  '.format(addr // 4)  # addr // 4 gives word addresses

        for b, byte in enumerate(line):   # Note that byte is an int when you iterate bytes
            disp += '{:02X} '.format(byte)
            text += chars[byte]
            if b % 4 == 3: disp += ' '

        disp += ' ' * (4 - (b // 4))
        for i in range(15 - b): disp += '   '
        disp += '|{}|'.format(text)
        addr += 16
    print(disp)

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
        hexdump(binary)

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
