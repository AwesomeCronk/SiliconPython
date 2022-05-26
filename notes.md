# .pyc structure
* "Magic" number (`0x550d0d0a` for 3.8) (4B)
* Bit field (All zeros)                 (4B)
* Unix timestamp of modification time   (4B)
* File size                             (4B)
* A marshalled code object
    * `co_argcount`
    * `co_code`
    * `co_consts`
    * `co_filename`
    * `co_firstlineno`
    * `co_flags`
    * `co_name`
    * `co_names`
    * `co_nlocals`
    * `co_stacksize`
    * `co_varnames`

# Custom serialization
Will support the same types as marshal
Supported types:
* code object
* int
* str
* float
* 