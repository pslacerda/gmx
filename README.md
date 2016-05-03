# gmxscript
_Simple checkpointed Gromacs scripting framework for Python_


There are some libraries around there that wraps gromacs commands to easy its usage
(e.g. [GromacsWrapper](http://gromacswrapper.readthedocs.io/)). This one isn't a library, it's a framework. `gmxscript`was
designed to allow non-programmers and entry level programmers to do reproducible science with Gromacs scripts.


```python
    from gmxscript import *
    
    # Enters in the checkpointed lysozyme/ directory, any command you run inside it is checkpointed
    # If you rerun this script, previously launched commands isn't started again
    with system('1AKI'):
    
        # Generate topology
        # the PDB file is downloaded automatically if not found in parent directories
        pdb2gmx(
            ff    = 'gromos54a7',
            water = 'spce',
            f     = PDB['1AKI'],
            o     = 'prot.gro',
            p     = 'topol.top'
        )
        
        # Apply periodic boundary condition
        editconf(
            f  = 'prot.gro',
            o  = 'pbc.gro',
            bt = 'dodecahedron',
            d  = 1.4
        )
        
        # Minimize energy using the steep descent algorithm
        # The .mdp file is looked up in parent directories and has these parameters added or modified
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
```
