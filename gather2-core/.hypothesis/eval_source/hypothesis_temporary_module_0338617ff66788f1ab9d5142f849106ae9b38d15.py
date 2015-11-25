from hypothesis.utils.conventions import not_set

def accept(f):
    def fractions():
        return f()
    return fractions
