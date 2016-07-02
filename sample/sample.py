#!/usr/bin/python3

from gmxscript import *

with system('1AKI'):

    # System preparation
    pdb2gmx(
        ff    = 'gromos54a7',
        water = 'spce',
        f     = PDB['1AKI'],
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

    # Steep descent energy minimization
    grompp(
        f = MDP['em.mdp', {
            'integrator': 'steep',
            'emtol'     : 10.0,
            'nsteps'    : 500,
        }],
        c = 'ions.gro',
        o = 'sd.tpr',
        p = 'topol.top'
    )
    mdrun(deffnm = 'sd')

    # Conjugate gradient energy minimization
    grompp(
        f = MDP['em.mdp', {
            'integrator': 'cg',
            'emtol'     : 1.0,
            'nsteps'    : 500,
        }],
        c = 'sd.gro',
        o = 'cg.tpr',
        p = 'topol.top'
    )
    mdrun(deffnm = 'cg')

    # Position restrained molecular dynamics
    grompp(
        f = MDP['md.mdp', {
            'steps'       : 250000,
            'define'      : '-DPOSRES',
            'continuation': False,
            'gen_vel'     : True
        }],
        c = 'cg.gro',
        o = 'mdposres.tpr',
        p = 'topol.top'
    )
    mdrun(deffnm = 'mdposres')

    # Molecular dynamics
    grompp(
        f = MDP['md.mdp', {
            'steps'       : 250000,
            'continuation': True,
            'gen_vel'     : False,
            'tcoupl'      : 'V-rescale',
            'tc_grps'     : ['Protein', 'Non-protein'],
            'tau_t'       : [0.1, 0.1],
            'ref_t'       : [298, 298]
        }],
        c = 'mdposres.gro',
        o = 'md.tpr',
        p = 'topol.top'
    )
    mdrun(deffnm = 'md')
