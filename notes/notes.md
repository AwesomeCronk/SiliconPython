# Custom serialization
All objects except `compyle.serialize.pointer`s (used internally by compyle) have a 4 byte header. The first byte is the object type index and the other three bytes are metadata for the object.

Supported types are listed below. Italics indicate not implemented or incomplete.

### compyle.serialize.pointer
* ID: None

This object is simply a placeholder object within compyle, used to keep track of where to write memory addresses.

### *code object*
* ID: 0 | Metadata: 0x000000
* Structure:
    * Pointer to bytecode
    * Pointer to names
    * Pointer to constants
    * Pointer to name
    * Pointer to filename

All referenced objects are inserted in the binary elsewhere

### *int*
* ID: 1 | Metadata: number of blocks
* Structure (per block):
    * 32B of the raw, big endian two's compliment of the int value
    * 4B pointer to next block, 0 if current block is last

### *float*
* ID: 2 | Metadata: 0x000000
* Structure:
    * 8B IEEE-754 double-precison float

### *str*
* ID: 3 | Metadata: number of blocks
* Structure: (per block):
    * 32B of the str object, UTF-8 encoded
    * 4B pointer to next block, 0 if current block is last

### *bytes*
* ID: 4 | Metadata: number of blocks
* Structure: (per block):
    * 32B of the bytes object
    * 4B pointer to next block, 0 if current block is last

### *bool*
* ID: 5 | Metadata: 0x000000 if False, else 0xFFFFFF
* Structure: N/A - value is stored in header metadata

### *tuple*
* ID: 6 | Metadata:

### *list*
* ID: 7 | Metadata:

### *dict*
* ID: 8 | Metadata:


# Boot sequence
1. Copy `boot.spy` to memory and execute it
// 2. Import (ER) `__main__` from program ROM   // Maybe just call an `import __main__` at the end of `boot.spy`?

Maybe what should be done here is run `boot.py`, then run `__main__`. I don't want stack traces to be `boot/__main__/whatever`, but just `__main__/whatever`. We'll see what happens, because before any of this can exist, it needs to be able to execute and import code.

# Imports and builtins
Code can be imported in many ways:
* Raw (R) import                - Copies the code object to memory, adjusting pointers
* Executing raw (ER) import     - Performs a raw import, then executes the code object
* Code (C) import               - Compiles the code to a code object, assuming a beginning address of 0, then adjusts pointers
* Executing code (EC) import    - Performs a code import, then executes the code object

A code import can performed with code from any source, so long as it's presented as a Python string. The `compile` function is used just like CPython's `compile` and is defined in `boot.py`. The `import <thing>` statement performs an ER import if `<thing>` is a corelib and and EC import if `<thing>` is not.

**Use `__import__()` to implement the import mechanism**

### Builtin implementation
There are two types of builtins: Hardware builtins and Software builtins. `boot.py` defines software builtins, while the microcode for the bytecode executor defines hardware builtins.

### Import mechanism
Standard packages, etc, are bundled in `corelibs.bin`. At the beginning is a header containing addresses of packages. At each of these addresses is the contents of the related .spy file. Each of these .spy files is compiled assuming an initial address of 0. Import mechanism needs to find all address pointers within the imported code and offset them to fit where objects can be allocated in memory.

# Name lookup
Check locals, then globals, then builtins

# Memory allocation
To allocate memory, enable `Ctrl_Alloc` and output the desired size onto the bus. The allocator will walk from the first known available memory block and read the size from that address (4B to store size). For each block it walks to, it jumps to then next if the available sie is too little, reading the address for the next block directly after the size (4B to store address). It then tweaks these blocks to point around the allocated block, storing the address of the allocated block in the allocated register. During this time, the rest of the CPU is halted (clock still goes, but microcode is not executing). When it unhalts, `Ctrl_AllocOut` is enabled and the allocated register is output.

## MMU states
Notes
* `available` and `desired` always have greater/equal available as `sufficient`
* `available` and `desired` always have difference available as `remaining`
* `testing` and `desired` always have sum available as `split`

### State 0 (idle)
* unhold the CPU
* if `Ctrl_Alloc` active then go to state 1 else go to state 0

### State 1 (init)
* hold CPU
* latch desired block size into `desired`
* copy `first` to `next`
* latch 0 into `testing`    // Used when marking blocks after one is found
* go to state 2

### State 2 (compare)
* copy `testing` to `previous`
* copy `next` to `testing`
* read memory address `testing` into `available`
* if `sufficient` then go to state 4, else go to state 3

### State 3 (walk)
* read memory address `testing` + 4 into `next`
* go to state 2

### State 4 (split block)
* write memory address `split` as `remaining`
* read memory address `testing` + 4 into `next`
* write memory address `split` + 4 as `next`
* if `previous` equals `first` then go to state 6, else go to state 5

### State 5 (redirect previous block)
* write memory address `previous` + 4 as `next`     // Make the last block point to the block after this one, instead of pointing to this one
* go to state 0

### State 6 (relocate first block)
* read memory address `testing` + 4 into `first`
* go to state 0
