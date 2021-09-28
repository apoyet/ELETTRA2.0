import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from cpymad.madx import Madx
from matplotlib import cm, gridspec, patches

import xobjects as xo
import xline as xl
import xtrack as xt

import elettra_toolbox


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


# Initial twiss

madx.use(sequence='ring')
madx.twiss(sequence='ring', table='init_twiss');
init_twiss = madx.table.init_twiss.dframe()

if settings['SAVE_TWISS']:
    init_twiss.to_parquet('init_twiss.parquet')
    
    
# Some plots
s = init_twiss['s'].to_numpy()
betx = init_twiss['betx'].to_numpy()
bety = init_twiss['bety'].to_numpy()

plt.figure(figsize=(10,5))
plt.plot(s, betx, 'r-', lw=2, label='$\\beta_{x}$')
plt.plot(s, bety, 'b-', lw=2, label='$\\beta_{y}$')

plt.xlabel('s [m]', fontsize=16)
plt.ylabel('$\\beta_{x,y}$ [m]', fontsize=16)
plt.tick_params(labelsize=14)
plt.legend(loc='best', fontsize=14);

if settings['SAVE_FIGS']:
    plt.savefig('elettra_beta_ring.pdf', bbox_inches='tight')
    
x0 = init_twiss[init_twiss.name=='ss:1']['s'].iloc[0]
x1 = init_twiss[init_twiss.name=='ss:2']['s'].iloc[0]

aux = init_twiss[(init_twiss.s>x0) & (init_twiss.s<x1)]
s = aux['s'].to_numpy()
betx = aux['betx'].to_numpy()
bety = aux['bety'].to_numpy()

plt.figure(figsize=(10,5))
plt.plot(s, betx, 'r-', lw=2, label='$\\beta_{x}$')
plt.plot(s, bety, 'b-', lw=2, label='$\\beta_{y}$')

plt.xlabel('s [m]', fontsize=16)
plt.ylabel('$\\beta_{x,y}$ [m]', fontsize=16)
plt.tick_params(labelsize=14)
plt.legend(loc='best', fontsize=14);

if settings['SAVE_FIGS']:
    plt.savefig('elettra_beta_achromat.pdf', bbox_inches='tight')
    
# Compute Emittance 

madx.input(f'''
emit, deltap={madx.globals.deltap};
''')

# Stop MAD-X instance

madx.quit()

# Get the emittance from the standard output

ex, ey, ez = elettra_toolbox.get_emittances_from_madx_output("stdout.out", to_meters=True)

print(f'ex = {ex*1e12} pm')
print(f'ey = {ey*1e12} pm')
print(f'ez = {ex*1e6} um')


