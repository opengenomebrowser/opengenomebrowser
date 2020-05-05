class Counter():
    def __init__(self, count: int = -1):
        self.count = count

    def s(self):
        # self / state
        return self.count

    def ss(self):
        # self / state
        return str(self.count)

    def p(self):
        # plus
        self.count += 1
        return self.count

    def pp(self):
        # plus
        self.count += 1
        return str(self.count)

    def m(self):
        # minus
        self.count -= 1
        return self.count

    def mm(self):
        # minus
        self.count -= 1
        return str(self.count)

    def d(self):
        # double
        self.count *= 2
        return self.count

    def dd(self):
        # double
        self.count *= 2
        return str(self.count)
