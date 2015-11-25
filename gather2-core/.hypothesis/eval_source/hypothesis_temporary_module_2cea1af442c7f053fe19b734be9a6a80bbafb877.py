from hypothesis.utils.conventions import not_set

def accept(f):
    def randoms():
        return f()
    return randoms
