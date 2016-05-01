#!/usr/bin/env python3

import builtins
import collections
import os
import io
import tempfile
import json
import shutil
import subprocess
import textwrap

from os import path
from glob import glob
from contextlib import contextmanager
from urllib.request import urlretrieve

CHECKPOINT_FNAME = '.checkpoint'
MDP_PATH = None


def load(fp):
    seq = []
    for cmd in json.load(fp):
        if cmd[2] == 'mdrun':
            deffnm = cmd[list.index('-deffnm') + 1]
            cpi = '%s.cpt' % deffnm
            gro = '%s.gro' % deffnm

            if path.isfile(cpi) and not path.isfile(gro):
                cmd.extend(['-cpi', cpi])

            break
        seq.append(cmd)
    return seq


def dump(sequence, fp):
    json.dump(sequence, fp)


class Command(list):
    def run(self):
        text = textwrap.dedent(self[-1].strip())
        stdin = tempfile.mkstemp(dir='.')[1]
        stdin = open(stdin, 'w')
        stdin.write(text)
        stdin.close()
        subprocess.check_call(self[:-1], stdin=open(stdin.name))


class GromacsCommand(Command):
    def __init__(self, name, iterable):
        super(['gmx' '-quiet'] + iterable)





class CheckpointedEnvironment:

    def __init__(self):
        self.prev_seqs = []
        self.curr_step = 0
        try:
            self.cp_seqs = load(open(CHECKPOINT_FNAME))
        except FileNotFoundError:
            self.cp_seqs = []

    def run_sequence(self, seq):
        self.prev_seqs.append(seq)

        if self.curr_step <= len(self.cp_seqs) > 0:
            if self.cp_seqs[self.curr_step] != self.prev_seqs[self.curr_step]:
                raise Exception("Checkpoint and script differs")
            self.curr_step += 1
            return

        seq.run()
        dump(self.prev_seqs, open(CHECKPOINT_FNAME, 'w'))


class FileFinder:

    def __init__(self, extradirs=None):
        self.dirs = ['.', '..', path.join('..', '..')]
        if extradirs is not None:
            self.dirs.extend(extradirs)

    def __getitem__(self, item):
        for dir in self.dirs:
            fname = path.join(path.abspath(dir), item)
            if path.isfile(fname):
                return fname

        raise FileNotFoundError("Force field '%s' not found" % item)


class PDBFinder(FileFinder):
    def __getitem__(self, item):
        pdb = '%s.pdb' % item
        try:
            return super().__getitem__(pdb)
        except FileNotFoundError:
            url = 'http://files.rcsb.org/download/%s' % pdb
            urlretrieve(url, pdb)
            return pdb


class MDPResource(FileFinder):

    def get_mdp_name(self, name):
        if name[-4:] == '.mdp':
            return name
        else:
            return '%s.mdp' % name

    def __getitem__(self, item):
        if type(item) is not tuple:
            return super().__getitem__(self.get_mdp_name(item))

        name = item[0]
        params = item[1]

        for dir in self.dirs:
            mdp = path.join(dir, self.get_mdp_name(name))
            if path.isfile(mdp):
                break
        else:
            raise FileNotFoundError(name)

        if params == {}:
            return mdp

        # TODO: try to implement a top section in configparser
        mdp = shutil.copy(mdp, '.')
        with open(mdp, 'a') as fp:
            for key, value in params.items():
                if isinstance(value, collections.Iterable):
                    value = ' '.join(map(str, value))
                if isinstance(value, bool):
                    value = int(bool)
                fp.write('%s = %s' % (key, value))
        return mdp


def find_avaliable_commands():
    cmd_names = {}
    out = subprocess.check_output(['gmx', 'help', 'commands'],
                                  stderr=subprocess.DEVNULL)
    for line in str(out, 'ascii').splitlines()[5:-2]:
        if line[4] != ' ':
            name = line[4:line.index(' ', 4)]
            cmd_names[name.replace('-', '_')] = name
    return cmd_names


@contextmanager
def system(dir):
    prevdir = path.abspath('.')
    try:
        os.mkdir(dir)
    except (FileExistsError, PermissionError):
        pass
    os.chdir(dir)

    builtins.__dict__['MDP'] = MDPResource(MDP_PATH)
    cpenv = CheckpointedEnvironment()

    cmd_names = find_avaliable_commands()
    for name in cmd_names:
        def runner(name=name, **kwargs):
            cmd = ['gmx', '-quiet', name]
            for key in sorted(kwargs):
                if key == 'stdin':
                    continue
                cmd.extend(['-%s' % key, '%s' % kwargs[key]])
            cmd.append(kwargs.pop('stdin', ''))
            cmd = Command(cmd)
            cpenv.run_sequence(cmd)
        builtins.__dict__[name] = runner

    yield

    os.chdir(prevdir)
    del builtins.__dict__['MDP']
    for name in cmd_names:
        del builtins.__dict__[name]


PDB = PDBFinder()
MDP = MDPResource(MDP_PATH)

if __name__ == '__main__':
    import sys
    # lines = []
    #
    # with open(__file__) as fp:
    #     for line in fp:
    #         if line == "if __name__ == '__main__':\n":
    #             break
    #         lines.append(line)
    #
    # with open(sys.argv[1]) as fp:
    #     lines.extend(fp.readlines())
    #
    # script = open(tempfile.mkstemp()[1])
    # script.writelines(lines)
    #
    # subprocess.call(["python3", script.name])