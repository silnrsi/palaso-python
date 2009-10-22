
import re

class lang :
    
    def test_expr(txt) :
        return txt.startswith("@")

    def __init__(self, exprstr, model) :
        self.model = model
        self.key = exprstr.split(" ")

    def calc(self) :
        self.model.get_key(self.key)


