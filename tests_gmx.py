import gmx
import os
import subprocess
import unittest
from unittest import mock


class DirectoryTest(unittest.TestCase):

    def setUp(self):
        self.chdir = os.chdir
        self.mkdir = os.mkdir
        self.check_call = os.mkdir
        subprocess.check_call = mock.MagicMock()
        os.mkdir = mock.MagicMock()
        os.chdir = mock.MagicMock()

    def tearDown(self):
        os.chdir = self.chdir
        os.mkdir = self.mkdir
        subprocess.check_call = self.check_call


class CommandTest(unittest.TestCase):

    def setUp(self):
        self.check_call = subprocess.check_call

    def tearDown(self):
        subprocess.check_call = self.check_call


class TestGromacsCommand(CommandTest):

    def test_build_option(self):
        cmd = gmx.GromacsCommand('cmd1')
        self.assertEqual(
            cmd.build_option('a', 'a'),
            ['-a', 'a']
        )
        self.assertEqual(
            cmd.build_option('b', 1),
            ['-b', '1']
        )
        self.assertEqual(
            cmd.build_option('c', 2.2),
            ['-c', '2.2']
        )
        self.assertEqual(
            cmd.build_option('d', True),
            ['-d', '1']
        )

    def test_run(self):
        cmd = gmx.GromacsCommand('cmd1', f=1, b=2.2)
        cmd.run()

        args = subprocess.check_call.call_args[0][0]
        self.assertEqual(args[:2], ['gmx', 'cmd1'])
        self.assertEqual(
            set(args[2:]),
            set([cmd.build_option(k, v) for k, v in {'f':1, 'b':2.2}.items()])
        )

    def test_str(self):
        cmd = gmx.GromacsCommand('cmd1', f=1, b=2.2)
        self.assertEqual(cmd, gmx.GromacsCommand.from_str(str(cmd)))
        self.assertEqual(str(cmd), '1\tgmx\tcmd1\t-f 1\t-b 2.2')

    def test_eq(self):
        self.assertEqual(
            gmx.GromacsCommand('cmd1', f=1, b=2.2),
            gmx.GromacsCommand('cmd1', f=1, b=2.2)
        )


class TestCommandSequence(self)
class TestGromacsCheckPointed(unittest.TestCase):

    def setUp(self):
        self.check_all = subprocess.check_call
        subprocess.check_call = mock.MagicMock()
        try:
            os.remove(gmx.CHECKPOINT_FNAME)
        except FileNotFoundError:
            pass

    def tearDown(self):
        subprocess.check_call = self.check_all
        os.remove(gmx.CHECKPOINT_FNAME)

    def test_call(self):
        cpe = gmx.CheckpointedEnvironment()
        cmd1 = gmx.GromacsCommand('cmd1')
        cmd2 = gmx.GromacsCommand('cmd2')

        cpe.run_command(cmd1)
        cpe.run_command(cmd2)

        cmds = (open(gmx.CHECKPOINT_FNAME).readlines())
        cmds = [c.strip().split('\t') for c in cmds]
        self.assertListEqual(cmds, [['gmx', 'cmd1'], ['gmx', 'cmd2']])


class TestFieldFinder(DirectoryTest):

    def test_find(self):
        finder = gmx.ForceFieldFinder()
        self.assertRaises(FileNotFoundError, finder.__getitem__, 'test')

        isdir = os.path.isdir
        ffdirs = ['test', 'test.ff', '../test', '../test.ff']
        for ffdir in ffdirs:
            os.path.isdir = lambda d: d == ffdir
            self.assertEqual(ffdir, finder[ffdir])


if __name__ == '__main__':
    unittest.main()