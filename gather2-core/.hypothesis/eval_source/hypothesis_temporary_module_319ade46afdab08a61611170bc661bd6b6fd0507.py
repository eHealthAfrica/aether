from hypothesis.utils.conventions import not_set

def accept(f):
    def tuples(*args):
        return f(*args)
    return tuples
