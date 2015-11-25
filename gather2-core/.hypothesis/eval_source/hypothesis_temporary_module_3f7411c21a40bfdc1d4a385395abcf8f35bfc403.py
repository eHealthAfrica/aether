from hypothesis.utils.conventions import not_set

def accept(f):
    def fixed_dictionaries(mapping):
        return f(mapping)
    return fixed_dictionaries
