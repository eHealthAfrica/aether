from hypothesis.utils.conventions import not_set

def accept(f):
    def permutations(values):
        return f(values)
    return permutations
