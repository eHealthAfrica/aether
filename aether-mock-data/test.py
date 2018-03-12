from mocker import MockFn

m = MockFn(sum, [1,2])
print(m())

def weird(args=None):
    if args:
        return args[::-1]
    return "weird"

f = MockFn(weird, ["dook", "ip"])

p = MockFn(weird, {"args": "pie"})

print (f())

print(p())
