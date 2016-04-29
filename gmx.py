#!/usr/bin/env python3

import os
import tempfile
import subprocess
from os import path
from glob import glob


CHECKPOINT_FNAME = '.checkpoint'

class GromacsCommand:

    def __init__(self, name, **kwargs):
        options = [self.build_option(k, v) for k, v in kwargs.items()]
        self.args = ['gmx', name] + options

    @classmethod
    def build_option(cls, key, value):
        if type(value) is bool:
            value = int(value)
        return '-%s=%s' % (key, value)

    def run(self):
        subprocess.check_call(self.args)

    @classmethod
    def from_str(cls, str):
        cmd = str.strip().split('\t')
        name = cmd[1]
        opts = (c.partition('=') for c in cmd[2:])
        opts = {k[1:]:d for k,_,d in opts}
        return GromacsCommand(name, **opts)

    def __eq__(self, other):
        return self.args == other.args

    def __str__(self):
        return '\t'.join(self.args)


class CheckpointedEnvironment:

    def __init__(self):
        self.previous_cmds = []
        self.checkpoint_cmds = []
        try:
            with open(CHECKPOINT_FNAME, 'r') as fp:
                for line in fp:
                    cmd = GromacsCommand.from_str(line)
                    self.checkpoint_cmds.append(cmd)
        except FileNotFoundError:
            pass
        self.checkpoint_fp = open(CHECKPOINT_FNAME, 'a')

    def run_command(self, cmd):
        self.previous_cmds.append(cmd)

        if len(self.checkpoint_cmds) > 0:
            if self.checkpoint_cmds[0] == self.previous_cmds[0]:
                self.checkpoint_cmds.pop(0)
                self.previous_cmds.pop(0)
        cmd.run()
        self.checkpoint_fp.write('%s\n' % cmd)
        self.checkpoint_fp.flush()

    def __del__(self):
        self.checkpoint_fp.close()


class ForceFieldFinder:

    def __getitem__(self, item):
        ffdirs =  [
            item,
            '%sff' % item,
            path.join('..', item),
            path.join('..', '%sff' % item)
        ]
        for ffdir in ffdirs:
            if path.isdir(ffdir):
                return ffdir
        for ffdir in glob(path.join(os.environ['GMXDATA'], 'top', '*.ff')):
            if item in [path.basename(ffdir), path.basename(ffdir)[:-3]]:
                return ffdir
        raise KeyError("Force field '%s' not found" % item)


class SystemContext:
    def __init__(self, dir):
        self.dir = dir

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self):
        pass
system = SystemContext

FORCE_FIELDS = ForceFieldFinder()
"""
with system('2goj-apo'):
    pdb2gmx(
        ff    = FORCE_FIELD['amber99sb-ildn'],
        water = 'spce',
        f     = 'prot.pdb',
        o     = 'prot.gro'
    )

    editconf(
        f  = 'prot.gro',
        o  = 'pbc.gro',
        bt = 'dodecahedron',
        d  = 1.4
    )

    solvate(
        cp = 'pbc.gro',
        cs = 'spc216.gro',
        o  = 'sol.gro'
    )

    grompp(
        f = MDP['ions.mdp'],
        c = 'sol.gro',
        o = 'ions.tpr'
    )

    genion(
        s = 'ions.tpr',
        o = 'ions.gro',
        neutral = True,
    )
"""