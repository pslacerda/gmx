# gmxscript
_Simple checkpointed Python scripting framework for Gromacs_


There are some libraries around there wrapping gromacs commands (e.g.
[GromacsWrapper](http://gromacswrapper.readthedocs.io/)). This one isn't a
library, it's a framework. **`gmxscript`** was designed to help programmers and
non-programmers to do reproducible science with Gromacs.

## Instalation and Usage

Enter `pip3 gmxscript` at your command line, but first you may need to install
Python 3.4 or higher. You also must have installed an working copy of Gromacs 5
or higher. **`gmxscript`** tries to detect the Gromacs installation automatically
, but if it fails you need to `source GMXRC` as usual. Supposing that you have
the following sample in a file called `protocol.py`, run the script with
`python3 protocol.py`.

```python
    from gmxscript import *
    
    # Enters in the checkpointed lysozyme/ directory, any command you run inside
    # it is checkpointed. If you rerun this script, previously launched commands
    # aren't started again
    with system('1AKI'):
    
        # Generate topology. The PDB file is downloaded automatically if not
        # found in parent directories
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
        
        # Minimize energy using the steep descent algorithm. The .mdp file is
        # looked up in parent directories and has these parameters added or 
        # modified
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
        
        # If there is a checkpoint file (.cpt) and the simulation wasn't 
        # finished (i.e. there isn't a .gro file), then the simulation is 
        # restarted. But it works only if you provides the -deffnm option here.
        mdrun(deffnm = 'sd')
```
