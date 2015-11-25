from hypothesis.utils.conventions import not_set

def accept(f):
    def none():
        return f()
    return none
