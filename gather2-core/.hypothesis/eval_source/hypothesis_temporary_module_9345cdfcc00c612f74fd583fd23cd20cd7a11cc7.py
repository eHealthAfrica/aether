from hypothesis.utils.conventions import not_set

def accept(f):
    def recursive(base, extend, max_leaves=not_set):
        return f(base, extend, max_leaves)
    return recursive
