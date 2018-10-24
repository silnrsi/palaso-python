#!/usr/bin/python

import unittest
from palaso.unicode.reorder import ReOrder, CharCode

class TestLana(unittest.TestCase):

    def setUp(self):
        subj = ur"\u1A60[\u1A20-\u1A49]"
        self.reorder = ReOrder([
            (subj, CharCode(10, 0, 0, False), ur"\u1A49[\u1A62\u1A65-\u1A7C]*"),
            (ur"[\u1A55\u1A56]", CharCode(20, 0, 0, False)),
            (ur"[\u1A6E\u1A6F\u1A70\u1A71\u1A72]", CharCode(30, 0, 0, False)),
            (ur"[\u1A69\u1A6A\u1A6C]", CharCode(35, 0, 0, False)),
            (ur"[\u1A62\u1A65\u1A66\u1A67\u1A68\u1A6B\u1A73]", CharCode(40, 0, 0, False)),
            (ur"[\u1A75\u1A76\u1A77\u1A78\u1A79]", CharCode(50, 0, 0, False)),
            (subj, CharCode(80, 0, 0, False)),
            (ur"[\u1A5C\u1A5D\u1A5E]", CharCode(80, 0, 0, False)),
            (ur"[\u1A63\u1A64]\u1A74?", CharCode(60, 0, 0, False)),
            (ur"\u1A61", CharCode(65, 0, 0, False)),
            (ur"[\u1A6D\u1A57\u1A58]", CharCode(85, 0, 0, False)),
            (ur"[\u1A7A\u1A7C]", CharCode(90, 0, 0, False)),
            (ur"\u1A7F", CharCode(95, 0, 0, False)),
            (ur"\u1A7B", CharCode(100, 0, 0, False))])

def create_tests():
    fns = []
    for t in (
            ("kok", u"\u1A20\u1A6B\u1A60\u1A20", u"\u1A20\u1A6B\u1A60\u1A20"),
            ("kwang", u"\u1A20\u1A60\u1A45\u1A62\u1A29", u"\u1A20\u1A62\u1A60\u1A45\u1A29"),
            ("snabsnun", u"\u1A48\u1A7B\u1A60\u1A36\u1A62\u1A37\u1A48\u1A7B\u1A60\u1A36\u1A69\u1A41",
                         u"\u1A48\u1A62\u1A60\u1A36\u1A7B\u1A37\u1A48\u1A69\u1A60\u1A36\u1A7B\u1A41"),
            ("hngey", u"\u1A49\u1A60\u1A26\u1A6E\u1A6B\u1A60\u1A3F", u"\u1A49\u1A60\u1A26\u1A6E\u1A6B\u1A60\u1A3F"),
            ("hin",  u"\u1A49\u1A65\u1A60\u1A36",       u"\u1A49\u1A60\u1A36\u1A65"),
            ("hnim", u"\u1A49\u1A60\u1A36\u1A65\u1A3E", u"\u1A49\u1A60\u1A36\u1A65\u1A3E")):
        def makefn(tst):
            def testfn(self):
                res = self.reorder.reorder(tst[1])
                self.assertEqual(res, tst[2])
            return testfn
        setattr(TestLana, "test_{}".format(t[0]), makefn(t))

create_tests()

