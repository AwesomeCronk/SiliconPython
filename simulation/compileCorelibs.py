import argparse, pathlib, subprocess, sys


### REQUIRES THAT `compyle` BE BUILT AND AVAILABLE ON PATH
### I prefer to build it with `python3 -m nuitka compyle.py --onefile -o compyle` and copy it to /usr/local/bin/.


def getArgs(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        '--directory',
        help='Directory to find corelibs in',
        type=str,
        default='corelibs'
    )
    parser.add_argument(
        '-o',
        '--outfile',
        help='File to output corelibs to',
        type=str,
        default='corelibs.bin'
    )

    return parser.parse_args(argv)

def main():
    args = getArgs()
    directory = pathlib.Path(args.directory)
    headerSize = 0
    for file in [item for item in directory.glob('*.py') if item.is_file()]:
        headerSize += 1
        print('Compiling {}'.format(file))
        compyle = subprocess.run(['compyle', str(file)])
        if compyle.returncode != 0:
            print('Compyle failed (code {}), stopping'.format(compyle.returncode))
            break
    if compyle.returncode != 0:
        return

    print('Generating {}'.format(args.outfile))
    header = b''
    fileSection = b''
    for file in [item for item in directory.glob('*.spy') if item.is_file()]:
        with open(file, 'rb') as fileHandle:
            data = fileHandle.read()
            data = data + b'\x00' * (4 - (len(data) % 4))
            fileSection += data
        
        header = header + int.to_bytes(headerSize + (len(fileSection) // 4), 4, 'big')

    if len(header) != headerSize * 4: raise Exception('Header length mismatch (expected {} entries in {} bytes, got {} bytes)'.format(headerSize, headerSize * 4, len(header)))
    binary = header + fileSection

    with open(args.outfile, 'wb') as outfile: outfile.write(binary)
    print('Wrote output')


if __name__ == '__main__':
    main()
