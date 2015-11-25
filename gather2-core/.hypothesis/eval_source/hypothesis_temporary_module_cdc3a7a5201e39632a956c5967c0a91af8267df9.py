from hypothesis.utils.conventions import not_set

def accept(f):
    def binary(min_size=not_set, average_size=not_set, max_size=not_set):
        return f(min_size, average_size, max_size)
    return binary
