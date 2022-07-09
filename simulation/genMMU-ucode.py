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
    'Split_Out',
    'Next_In',
    'Next_Out',
    'Memory_Address',
    'Memory_AddressOffset',
    'Memory_Read',
    'Memory_Write',
    'CPU_Enable',
    '',
    'State_Set',
    'State_0',
    'State_1',
    'State_2'
]

numConditions = 8

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
    [
        ['CPU_Enable', 'State_Set'],
        ['State_Set', 'State_0'],
        ['CPU_Enable', 'State_Set'],
        ['State_Set', 'State_0'],
        ['CPU_Enable', 'State_Set'],
        ['State_Set', 'State_0'],
        ['CPU_Enable', 'State_Set'],
        ['State_Set', 'State_0']
    ],
    [],
    [],
    [],
    [],
    [],
    [],
    []
]

state_init = [
    ['Desired_In'],
    ['First_Out', 'Next_In'],
    ['Testing_In'],     # Latches 0 since nothing is outputting
    ['State_Set', 'State_1'],
    [],
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
        ['State_Set', 'State_0', 'State_1'],
        ['State_Set', 'State_0', 'State_1'],
        ['State_Set', 'State_0', 'State_1'],
        ['State_Set', 'State_0', 'State_1'],
        ['State_Set', 'State_2'],
        ['State_Set', 'State_2'],
        ['State_Set', 'State_2'],
        ['State_Set', 'State_2']
    ],
    [],
    [],
    []
]

state_walk = [
    ['Testing_Out', 'Memory_AddressOffset'],
    ['Memory_Read', 'Next_In'],
    ['State_Set', 'State_1'],
    [],
    [],
    [],
    [],
    []
]

state_splitBlock = [
    ['Split_Out', 'Memory_Address'],
    ['Memory_Write', 'Remaining_Out'],
    ['Testing_Out', 'Memory_AddressOffset'],
    ['Memory_Read', 'Next_In'],
    ['Split_Out', 'Memory_AddressOffset'],
    ['Memory_Write', 'Next_Out'],
    [
        ['State_Set', 'State_0', 'State_2'],
        ['State_Set', 'State_0', 'State_2'],
        ['State_Set', 'State_1', 'State_2'],
        ['State_Set', 'State_1', 'State_2'],
        ['State_Set', 'State_0', 'State_2'],
        ['State_Set', 'State_0', 'State_2'],
        ['State_Set', 'State_1', 'State_2'],
        ['State_Set', 'State_1', 'State_2']
    ],
    []
]

state_redirectPreviousBlock = [
    ['Previous_Out', 'Memory_AddressOffset'],
    ['Memory_Read', 'Next_In'],
    ['State_Set'],
    [],
    [],
    [],
    [],
    []
]

state_relocateFirstBlock = [
    ['Testing_Out', 'Memory_AddressOffset'],
    ['Memory_Read', 'First_In'],
    ['State_Set'],
    [],
    [],
    [],
    [],
    []
]


states = [
    state_idle,
    state_init,
    state_compare,
    state_walk,
    state_splitBlock,
    state_redirectPreviousBlock,
    state_relocateFirstBlock,
    state_blank
]

if len(lines) != 24: print('Line count {} is incorrect'.format(len(lines))); exit()
if len(states) != 2 ** 3: print('State count {} is incorrect'.format(len(states))); exit()
for s, state in enumerate(states):
    if len(state) != 2 ** 3: print('Step count {} for state {} is incorrect'.format(len(state), s)); exit()

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
