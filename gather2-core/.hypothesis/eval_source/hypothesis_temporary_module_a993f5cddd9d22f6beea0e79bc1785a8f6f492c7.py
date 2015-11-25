from hypothesis.utils.conventions import not_set

def accept(f):
    def booleans():
        return f()
    return booleans
