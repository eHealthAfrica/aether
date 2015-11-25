from hypothesis.utils.conventions import not_set

def accept(f):
    def test_map_function_smoke_test(self, map_function_data=not_set):
        return f(self, map_function_data)
    return test_map_function_smoke_test
