import mock
import unittest

from git_replay import change


class TestChange(unittest.TestCase):
    def test_id(self):
        commit1 = mock.Mock(predecessors=[])
        commit2 = mock.Mock(predecessors=[commit1])

        c = change.Change(commit2)
        self.assertEqual(str(commit1), c.id)
        self.assertEqual(str(commit2), c.head)

    def test___contains__(self):
        commit1 = mock.Mock(predecessors=[])
        commit2 = mock.Mock(predecessors=[commit1])

        c1 = change.Change(commit1)
        c2 = change.Change(commit2)

        self.assertIn(c1, c2)
        self.assertNotIn(c2, c1)

        commit3 = mock.Mock(predecessors=[commit1])
        c3 = change.Change(commit3)

        self.assertIn(c1, c3)
        self.assertNotIn(c3, c1)
        self.assertNotIn(c3, c2)
        self.assertNotIn(c2, c3)

    def test___sub__(self):
        commit1 = mock.Mock(predecessors=[])
        commit2 = mock.Mock(predecessors=[commit1])
        commit3 = mock.Mock(predecessors=[commit2])

        commit4 = mock.Mock(predecessors=[commit2])
        commit5 = mock.Mock(predecessors=[commit4])

        c1 = change.Change(commit3)
        c2 = change.Change(commit5)

        self.assertEqual([commit3], c1 - c2)
        self.assertEqual([commit4, commit5], c2 - c1)

        c3 = change.Change(commit2)
        self.assertEqual([], c3 - c2)
        self.assertEqual([], c3 - c1)
        self.assertEqual([commit3], c1 - c3)
        self.assertEqual([commit4, commit5], c2 - c3)

    def test___iter__(self):
        commit1 = mock.Mock(predecessors=[])
        commit2 = mock.Mock(predecessors=[commit1])
        commit3 = mock.Mock(predecessors=[commit2])

        c1 = change.Change(commit3)

        self.assertEqual([commit1, commit2, commit3], list(c1))


class TestChanges(unittest.TestCase):
    def test_operators(self):
        # Change 1
        commit1 = mock.Mock(predecessors=[])
        commit2 = mock.Mock(predecessors=[commit1])
        commit3 = mock.Mock(predecessors=[commit1])

        # Change 2
        commit4 = mock.Mock(predecessors=[])

        changes1 = change.Changes([commit4, commit2])
        changes2 = change.Changes([commit3])

        self.assertEqual(1, len(changes1 & changes2))
        self.assertEqual(1, len(changes2 & changes1))

        self.assertEqual(1, len(changes1 - changes2))
        self.assertEqual(0, len(changes2 - changes1))
