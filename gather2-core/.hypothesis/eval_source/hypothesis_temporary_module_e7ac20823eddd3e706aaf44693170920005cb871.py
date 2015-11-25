from hypothesis.utils.conventions import not_set

def accept(f):
    def basic(basic=not_set, generate_parameter=not_set, generate=not_set, simplify=not_set, copy=not_set):
        return f(basic, generate_parameter, generate, simplify, copy)
    return basic
