import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from cpymad.madx import Madx
from matplotlib import cm, gridspec, patches

import xobjects as xo
import xline as xl
import xtrack as xt


# Launch MAD-X Session
with open('stdout.out', 'w') as f:
    madx = Madx(stdout=f)
    

