from hypothesis.utils.conventions import not_set

def accept(f):
    def decimals():
        return f()
    return decimals
