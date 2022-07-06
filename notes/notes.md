# Custom serialization
Will support the same types as marshal
Supported types (italics indicate not implimented):
* compyle.serialize.pointer
* *code object*
* int
* *float*
* str
* *bytes*
* *bool*
* tuple
* *list*
* *dict*

# Memory allocation
To allocate memory, enable `Ctrl_Alloc` and output the desired size onto the bus. The allocator will walk from the first known available memory block and read the size from that address (4B to store size). For each block it walks to, it jumps to then next if the available sie is too little, reading the address for the next block directly after the size (4B to store address). It then tweaks these blocks to point around the allocated block, storing the address of the allocated block in the allocated register. During this time, the rest of the CPU is halted (clock still goes, but microcode is not executing). When it unhalts, `Ctrl_AllocOut` is enabled and the allocated register is output.

## MMU states
Notes
* `available` and `desired` always have greater/equal available as `sufficient`
* `available` and `desired` always have difference available as `remaining`
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
* write memory address `testing` + `desired` as `remaining`
* read memory address `testing` + 4 into `next`
* write memory address `testing` + `desired` + 4 as `next`
* if `previous` equals `first` then go to state 6, else go to state 5
### State 5 (redirect previous block)
* write memory address `previous` + 4 as `next`     // Make the last block point to the block after this one, instead of pointing to this one
* go to state 0
### State 6 (relocate first block)
* read memory address `testing` + 4 into `first`
* go to state 0
