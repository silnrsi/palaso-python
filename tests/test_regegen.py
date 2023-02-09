from palaso.reggen import expand_sub

class TestReggen:
    tests=[
        ('([ab])([cd])', r'\2\1'),
        (u'([\u1000-\u1003])([\u103C-\u103D]?)(\u102F?|\u1030)([\u1000-\u1003]\u103A)', r'\1\2\4\3'),
        ('(x([ab]|[cd]?))', r'\1')
    ]

    def test_expand_sub(self):
        for t in self.tests:
            print("-" * 50)
            print(t[0] + "\t" + t[1])
            for s in expand_sub(t[0], t[1]):
                print(s[0] + "\t" + s[1])
