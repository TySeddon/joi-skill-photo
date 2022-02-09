
class Base():
    def __hello(self):
        print("base")

    def say_hello(self):
        self.__hello()

class Concrete(Base):
    def _Base__hello(self):
        print("concrete")


c = Concrete()
c.say_hello()