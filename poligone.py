

class Poligone(object):
    status = 9


attr_name = getattr(Poligone(), "status")
print(attr_name)