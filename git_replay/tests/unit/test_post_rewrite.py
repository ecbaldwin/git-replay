import unittest

from git_replay import post_rewrite


class TestPostRewrite(unittest.TestCase):
    def test_convert_date(self):
        self.assertEqual("1515642254 -0700", post_rewrite.convert_date(1515642254, 25200))

    def test_make_rebase_map(self):
        pairs = [("0dead4f466", "9b4d826656"),
                 ("b94128d659", "9b4d826656"),
                 ("5d21e6c4c0", "67c7bb1364")]
        rebase_map = post_rewrite.make_rebase_map(pairs)
        self.assertEqual({'67c7bb1364': ['5d21e6c4c0'],
                          '9b4d826656': ['0dead4f466', 'b94128d659']},
                         rebase_map)
