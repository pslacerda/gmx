# from gmx import system, MDP, PDB
# from os import mkdir, chdir, path
#
# if not path.exists('test'):
#     mkdir('test')
# chdir('test')
#
# import ipdb; ipdb.set_trace()
# MDP.get_mdp_name('asd')

with system('2goj-apo'):
    pdb2gmx(
        ff    = 'amber99',
        water = 'spce',
        f     = PDB['prot'],
        o     = 'prot.gro',
        p     = 'topol.top'
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
        o  = 'sol.gro',
        p  = 'topol.top'
    )

    grompp(
        f = MDP['ions.mdp'],
        c = 'sol.gro',
        o = 'ions.tpr',
        p = 'topol.top'
    )

    genion(
        s       = 'ions.tpr',
        o       = 'ions.gro',
        neutral = 1,
        p       = "topol.top",
        stdin   = """
            SOL
        """
    )

    grompp(
        f = MDP['sd.mdp'],
        c = 'ions.gro',
        o = 'sd.tpr',
        p = 'topol.top'
    )

    mdrun(
        deffnm = 'sd',
        v      = True
    )