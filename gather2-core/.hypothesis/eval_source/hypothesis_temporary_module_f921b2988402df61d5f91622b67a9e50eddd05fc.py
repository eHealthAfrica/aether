from hypothesis.utils.conventions import not_set

def accept(f):
    def complex_numbers():
        return f()
    return complex_numbers
