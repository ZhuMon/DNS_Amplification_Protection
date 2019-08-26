
# Make it easier to construct and assign objects

def assign(obj, **kwargs):
    obj.__dict__.update(kwargs)

class Object(object):
    def __init__(self, **kwargs):
        assign(self, **kwargs)
