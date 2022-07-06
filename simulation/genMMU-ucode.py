lines = [
    'Available_In',
    'Available_Out',
    'Desired_In',
    'Desired_Out',
    'Remaining_Out',
    'First_In',
    'First_Out',
    'Previous_In',
    'Previous_Out',
    'Testing_In',
    'Testing_Out',
    'TestingPointer_Out',
    'Next_In',
    'Next_Out',
    'Memory_Address',
    'Memory_Read',
    'Memory_Write',
    'CPU_Hold',
    'CPU_Unhold',
    'Step_Reset',
    'State_Set',
    'State_0',
    'State_1',
    'State_2'
]

numConditions = 4

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

state_idle = [
    ['CPU_Unhold'],
    [
        ['State_Set', 'Step_Reset'],
        ['State_Set', 'State_0', 'Step_Reset'],
        ['State_Set', 'Step_Reset'],
        ['State_Set', 'State_0', 'Step_Reset']
    ],
    [],
    [],
    [],
    [],
    [],
    []
]

state_init = [
    ['CPU_Hold'],
    ['Desired_In'],
    ['First_Out', 'Next_In'],
    ['Testing_In'],     # Latches 0 since nothing is outputting
    ['State_Set', 'State_1', 'Step_Reset'],
    [],
    [],
    []
]

state_compare = [
    ['Testing_Out', 'Previous_In'],
    ['Next_Out', 'Testing_In'],
    ['Testing_Out', 'Memory_Address'],
    ['Memory_Read', 'Available_In'],
    [
        ['State_Set', 'State_0', 'State_1', 'Step_Reset'],
        ['State_Set', 'State_0', 'State_1', 'Step_Reset'],
        ['State_Set', 'State_2', 'Step_Reset'],
        ['State_Set', 'State_2', 'Step_Reset']
    ],
    [],
    [],
    []
]

state_walk = [
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    []
]


states = [
    state_idle,
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

def encodeStep(step):
    bits = [0] * len(lines)
    for line in step: bits[len(lines) - lines.index(line) - 1] = 1
    intValue = 0
    for bit in bits: intValue *= 2; intValue += bit
    return int.to_bytes(intValue, len(lines) // 8, 'big')

binary = b''
for i, state in enumerate(states):
    print('Processing state', i)
    for j, step in enumerate(state):
        print('Processing step {}: '.format(j), end='')

        # Steps can be a list of lines and be constant
        # or can be a list of lists of lines and be conditional
        if len(step) == 0:
            print('blank')
            binary = binary + b'\x00' * ((len(lines) // 8) * numConditions)
        elif isinstance(step[0], list):
            print('conditional')
            assert len(step) == numConditions
            for k, conditional in enumerate(step):
                binary = binary + encodeStep(conditional)
        else:
            print('constant')
            for k in range(numConditions):
                binary = binary + encodeStep(step)

with open('MMU-ucode.bin', 'wb') as file: file.write(binary)
print('Wrote binary')
