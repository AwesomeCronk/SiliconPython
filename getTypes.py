for attr in dir(__builtins__):
    print('{}: '.format(attr).ljust(32) + repr(getattr(__builtins__, attr)))