lines = [
    'Available_In',
    'Available_Out',
    'Desired_In',
    'Desired_Out',
    'First_In',
    'First_Out',
    'Previous_In',
    'Previous_Out',
    'Testing_In',
    'Testing_Out',
    'Next_In',
    'Next_Out',
    'Memory_Address',
    'Memory_Read',
    'Memory_Write',
    '',
    '',
    '',
    '',
    '',
    'State_Set',
    'State_0',
    'State_1',
    'State_2'
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
    [''],
    [''],
    [''],
    [''],
    ['State_Set'],
    ['State_0'],
    ['State_1'],
    ['State_2']
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

assert len(lines) == 24
assert len(states) == 2 ** 3
for s, state in enumerate(states): print('Checking step count for state', s); assert len(state) == 2 ** 3

binary = b''
for i, state in enumerate(states):
    print('Processing state', i)
    for j, step in enumerate(state):
        print('Processing step', j, step)
        bits = [0] * len(lines)
        for line in step: bits[len(lines) - lines.index(line) - 1] = 1
        intValue = 0
        for bit in bits: intValue *= 2; intValue += bit
        binary = binary + int.to_bytes(intValue, len(lines) // 8, 'big')

with open('MMU-ucode.bin', 'wb') as file: file.write(binary)
print('Wrote binary')
