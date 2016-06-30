#!/usr/bin/env python3

# Copyright 2016 Pedro Sousa Lacerda
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import builtins
import itertools
import hashlib
import json
import os
import subprocess
import tempfile
import textwrap

from contextlib import contextmanager
from os import path
from urllib.request import urlretrieve


if 'GMXPREFIX' not in os.environ:
    vars = ['GMXPREFIX', 'GMXBIN', 'GMXLDLIB', 'GMXMAN', 'GMXDATA',
           'GROMACS_DIR', 'LD_LIBRARY_PATH', 'MANPATH', 'PKG_CONFIG_PATH',
            'GROMACS_DIR', 'PATH']
    args = ['bash', '-c', ". /usr/local/gromacs/bin/GMXRC && echo %s" %
            '\t'.join(['$%s' % v for v in vars])]

    out = subprocess.check_output(args)
    out = str(out, encoding='ascii').strip().split()

    for key, value in zip(vars, out):
        os.environ[key] = value


def load(fp):
    return [Command(cmd) for cmd in json.load(fp)]


def dump(sequence, fp):
    json.dump(sequence, fp)


def open_resource(name, mode='r'):
    if not path.isdir('.gmx'):
        os.mkdir('.gmx')
    return open(path.join('.gmx', name), mode)


class Command(dict):

    def __init__(self, obj):
        super().__init__(obj)
        self['stdin'] = textwrap.dedent(self['stdin']).strip()

    def run(self):
        if self['stdin']:
            stdin = tempfile.mkstemp(dir='.')[1]
            with open(stdin, 'w') as stdin:
                stdin.write(self['stdin'])
            stdin = open(stdin.name)
        else:
            stdin = subprocess.PIPE
        subprocess.check_call(self['args'], stdin=stdin)

    def __eq__(self, other):
        return self['stdin'] == other['stdin'] and self['args'] == other['args']


class GromacsCommand(Command):

    def __init__(self, name, _params):
        stdin = _params.pop('stdin') if 'stdin' in _params else ''
        params = []
        for key in sorted(_params):
            params.append('-%s' % key)
            params.extend(self.convert_param(_params[key]))

        super().__init__({
            'stdin': stdin,
            'args': ['gmx', '-quiet', name] + params
        })

    def convert_param(self, param):
        if type(param) is bool:
            return [str(param).lower()]
        elif type(param) in [list, tuple]:
            params = (self.convert_param(p) for p in param)
            return itertools.chain.from_iterable(params)
        else:
            return [str(param)]

    def run(self):
        if self['args'][2] == 'mdrun' and '-deffnm' in self['args']:
            deffnm = self['args'][self['args'].index('-deffnm') + 1]
            cpi = '%s.cpt' % deffnm
            gro = '%s.gro' % deffnm

            if path.isfile(cpi) and not path.isfile(gro):
                self['args'].extend(['-cpi', cpi])
        super().run()


class CheckpointedEnvironment:

    def __init__(self):
        self.prev_cmds = []
        self.step = 0
        try:
            self.cp_cmds = load(open_resource('checkpoint'))
        except FileNotFoundError:
            self.cp_cmds = []

    def run_command(self, cmd):
        self.prev_cmds.append(cmd)

        if self.step < len(self.cp_cmds) > 0:
            if self.cp_cmds[self.step] != self.prev_cmds[self.step]:
                raise Exception("Checkpoint and script differ")
        else:
            cmd.run()
            dump(self.prev_cmds, open_resource('checkpoint', 'w'))
        self.step += 1


class PrettyCheckpointedEnvironment(CheckpointedEnvironment):

    def __init__(self):
        super().__init__()

        self.color1 = ''
        self.color2 = ''
        self.reset = ''
        try:
            def tput(s):
                out = subprocess.check_output(['tput'] + s.split())
                return out.decode('ascii')

            if int(tput('colors')) >= 8:
                self.color1 = (tput('bold') + tput('setaf 3'))
                self.color2 = (tput('bold') + tput('setaf 4'))
                self.color3 = tput('setab 5')
                self.reset = tput('sgr0')
        except FileNotFoundError:
            pass

        dir = path.abspath('.')
        print("%sCheckpointed environment: %s%s" % (self.color1, self.reset, dir))

    def run_command(self, cmd):
        print("%sCommand:%s %s" % (self.color2, self.reset, ' '.join(cmd['args'])))
        if cmd['stdin']:
            print("%sInput  :%s %s" % (self.color2, self.reset, cmd['stdin']))
        super().run_command(cmd)


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

    def __getitem__(self, item):
        if type(item) is not tuple:
            return super().__getitem__(item)

        name = item[0]
        params = item[1]
        mdp = super().__getitem__(name)

        if params == {}:
            return mdp

        for key, value in params.items():
            if type(value) in [list, tuple]:
                params[key] = ' '.join(map(str, value))
            if type(value) is bool:
                params[key] = str(int(value))
            if type(value) in [int, float]:
                params[key] = str(value)

        new_mdp = [(k, params[k]) for k in sorted(params)]
        new_mdp = bytes(mdp+str(new_mdp), encoding='ascii')
        new_mdp = hashlib.md5(new_mdp).hexdigest()
        new_mdp = '%s.mdp' % new_mdp

        try:
            with open_resource(new_mdp) as res:
                return path.abspath(res.name)
        except FileNotFoundError:
            pass

        with open_resource(new_mdp, 'w') as fout:
            with open(mdp) as fin:
                for line in fin:
                    line = line[:line.index(';')] if ';' in line else line
                    line = line.strip()
                    if not line:
                        continue
                    key, _, value = line.partition('=')
                    key = key.strip()

                    if key in params:
                        line = "%s = %s\n" % (key, params[key])
                    else:
                        line = "%s = %s\n" % (key, value.strip())
                    fout.write(line)
        return path.abspath(fout.name)


def gromacs_command_factory():
    factories = []
    out = subprocess.check_output(['gmx', '-quiet', 'help', 'commands'])
    for line in str(out, 'ascii').splitlines()[5:-1]:
        if line[4] != ' ':
            name = line[4:line.index(' ', 4)]
            fancy, name  = name.replace('-', '_'), name
            def command_factory(name=name, **kwargs):
                return GromacsCommand(name, kwargs)
            factories.append((fancy, name, command_factory))
    return factories


@contextmanager
def system(dir):
    prevdir = path.abspath('.')
    try:
        os.mkdir(dir)
    except FileExistsError:
        pass
    os.chdir(dir)

    env = PrettyCheckpointedEnvironment()
    factories = gromacs_command_factory()
    for fancy, name, factory in factories:
        def runner(name=name, factory=factory, **kwargs):
            cmd = factory(name, **kwargs)
            env.run_command(cmd)
        builtins.__dict__[fancy] = runner

    yield

    os.chdir(prevdir)
    for fancy, _, _ in factories:
        del builtins.__dict__[fancy]



__all__ = ["PDB", "MDP", "system"]

PDB = PDBFinder()
MDP = MDPResource()


for fancy, name, factory in gromacs_command_factory():
    def runner(name=name, **kwargs):
        cmd = GromacsCommand(name, kwargs)
        cmd.run()
    globals()[fancy] = runner
    __all__.append(fancy)


if __name__ == '__main__':
    import sys

    script = open(tempfile.mkstemp()[0], 'w')
    for line in open(__file__).readlines():
        if line == "if __name__ == '__main__':\n":
            break
        script.write(line)
    script.write("from gmx import *\n")
    for line in open(sys.argv[1]):
        script.write(line)
    script.close()
    subprocess.call(['python3', script])
