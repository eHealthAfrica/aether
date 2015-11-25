from hypothesis.utils.conventions import not_set

def accept(f):
    def streaming(elements):
        return f(elements)
    return streaming
