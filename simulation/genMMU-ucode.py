lines = [
    '0',
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7'
]

state_blank = [
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    []
]

state_test = [
    ['0'],
    ['1'],
    ['2'],
    ['3'],
    ['4'],
    ['5'],
    ['6'],
    ['7']
]

states = [
    state_test,
    state_blank,
    state_blank,
    state_blank,
    state_blank,
    state_blank,
    state_blank,
    state_blank
]

assert len(lines) == 8
assert len(states) == 2 ** 3
for s, state in enumerate(states): print('Checking step count for state', s); assert len(state) == 2 ** 3

binary = b''
for i, state in enumerate(states):
    print('Processing state', i)
    for j, step in enumerate(state):
        print('Processing step', j, step)
        bits = [0] * 8
        for line in step: bits[lines.index(line)] = 1
        intValue = 0
        for bit in bits: intValue *= 2; intValue += bit
        binary = binary + int.to_bytes(intValue, 1, 'big')

with open('MMU-ucode.bin', 'wb') as file: file.write(binary)
print('Wrote binary')
