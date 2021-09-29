import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from cpymad.madx import Madx
from matplotlib import cm, gridspec, patches
import os

import xobjects as xo
import xline as xl
import xtrack as xt

import elettra_toolbox

############################################################################################################

k_var = 0.001

k1_qd1_0          =       -3.420000
k1_qf1_0          =       5.735000

n_points = 10
k1_qd1_scan = np.linspace(k1_qd1_0 - k_var, k1_qd1_0 + k_var, n_points)
k1_qf1_scan = np.linspace(k1_qf1_0 - k_var, k1_qf1_0 + k_var, n_points)

emit_df = pd.DataFrame(index=k1_qd1_scan, columns=k1_qf1_scan, dtype=float)

iteration = 0


############################################################################################################

for kd1 in k1_qd1_scan:
    for kf1 in k1_qf1_scan:
    
        print(iteration)

        if os.path.exists("stdout.out"):
            os.remove("stdout.out")

        # Launch MAD-X Session
        with open('stdout.out', 'w') as f:
            madx = Madx(stdout=f)


        # Read parameters

        from config import parameters
        from config import settings

        for i in parameters.keys():
            madx.globals[i] = parameters[i]


        # Call sequence and optics 

        madx.call('elettra2_v15_VADER_2.3T.madx');
        madx.call('optics_elettra2_v15_VADER_2.3T.madx');

        # Set the k_value of VADER dipole
        madx.globals.k1_qd1 = kd1
        madx.globals.k1_qf1 = kf1


        # Initial twiss

        madx.use(sequence='ring')
        madx.twiss(sequence='ring', table='init_twiss');

        # Compute Emittance 

        madx.input(f'''
        emit, deltap={madx.globals.deltap};
        ''')

        # Stop MAD-X instance

        madx.quit()

        # Get the emittance from the standard output

        try:
            ex, ey, ez = elettra_toolbox.get_emittances_from_madx_output("stdout.out", to_meters=True)
            emit_df.loc[kd1,kf1] = ex
            
        except:
            emit_df.loc[kd1,kf1] = np.nan
            print('Warning: an emittance value was not properly computed')

        iteration = iteration + 1
    

emit_df.to_pickle('emit_df_quad.pkl')


