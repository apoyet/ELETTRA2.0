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

k_vader_0 = -1.962662
k_var = 0.02

n_points = 100
k_scan = np.linspace(k_vader_0 - k_var, k_vader_0 + 2*k_var, n_points)
ex_lst = []
iteration = 0


############################################################################################################

for k in k_scan:
    
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
    madx.globals.k1_vader = k


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
        ex_lst.append(ex)
    except:
        ex_lst.append(np.nan)
        print('Warning: an emittance value was not properly computed')
    
    iteration = iteration + 1
    
emit_df = pd.DataFrame(index=[k_scan], columns=['ex'])
emit_df['ex'] = np.array(ex_lst)
emit_df.to_parquet('emit_df.parquet')


