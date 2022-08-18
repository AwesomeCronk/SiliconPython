import argparse, json5

def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'jsonfile',
        help='JSON5 file to read ucode structure from'
    )
    parser.add_argument(
        '-o',
        '--outfile',
        help='File to write ucode binary to',
        default='ucode.bin'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='Enable verbose output',
        action='store_true'
    )

    return parser.parse_args()

if __name__ == '__main__':
    args = getArgs()
    with open(args.jsonfile, 'r') as jsonfile: ucodeJSON = json5.load(jsonfile)
    lines = ucodeJSON['lines']
    states = ucodeJSON['states']
    numLines = ucodeJSON['numLines']
    numStates = ucodeJSON['numStates']
    numConditions = ucodeJSON['numConditions']

    if len(lines) != numLines: print('Line count {} is incorrect'.format(len(lines))); exit()
    if len(states) != numStates: print('State count {} is incorrect'.format(len(states))); exit()
    for s, state in enumerate(states):
        if len(ucodeJSON[state]) != 2 ** 3: print('Step count {} for state {} is incorrect'.format(len(ucodeJSON[state]), s)); exit()

    def encodeStep(step):
        bits = [0] * len(lines)
        for line in step: bits[len(lines) - lines.index(line) - 1] = 1
        intValue = 0
        for bit in bits: intValue *= 2; intValue += bit
        return int.to_bytes(intValue, len(lines) // 8, 'big')

    binary = b''
    for i, state in enumerate(states):
        if args.verbose: print('Processing state', i)
        for j, step in enumerate(ucodeJSON[state]):
            if args.verbose: print('Processing step {}: '.format(j), end='')

            # Steps can be a list of lines and be constant
            # or can be a list of lists of lines and be conditional
            if len(step) == 0:
                if args.verbose: print('blank')
                binary = binary + b'\x00' * ((len(lines) // 8) * numConditions)
            elif isinstance(step[0], list):
                if args.verbose: print('conditional')
                assert len(step) == numConditions
                for k, conditional in enumerate(step):
                    binary = binary + encodeStep(conditional)
            else:
                if args.verbose: print('constant')
                for k in range(numConditions):
                    binary = binary + encodeStep(step)

    with open(args.outfile, 'wb') as file: file.write(binary)
    if args.verbose: print('Wrote binary')
