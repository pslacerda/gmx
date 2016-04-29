import unittest
import gmx
import subprocess
from unittest import mock
import os


class TestGromacsCommand(unittest.TestCase):

    def setUp(self):
        self.check_all = subprocess.check_call
        subprocess.check_call = mock.MagicMock()

    def tearDown(self):
        subprocess.check_call = self.check_all

    def test_build_option(self):
        cmd = gmx.GromacsCommand('cmd1')
        self.assertEqual(
            cmd.build_option('a', 'a'),
            '-a=a'
        )
        self.assertEqual(
            cmd.build_option('b', 1),
            '-b=1'
        )
        self.assertEqual(
            cmd.build_option('c', 2.2),
            '-c=2.2'
        )
        self.assertEqual(
            cmd.build_option('d', True),
            '-d=1'
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

    def test_eq(self):
        self.assertEqual(
            gmx.GromacsCommand('cmd1', f=1, b=2.2),
            gmx.GromacsCommand('cmd1', f=1, b=2.2)
        )

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


if __name__ == '__main__':
    unittest.main()