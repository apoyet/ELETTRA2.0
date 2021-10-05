import elettra_toolbox
import matplotlib.pyplot as plt
import seaborn as sns
from config import parameters, settings
from cpymad.madx import Madx
from matplotlib import cm, gridspec, patches
from pyhdtoolkit.cpymadtools.plotters import LatticePlotter
from pyhdtoolkit.utils import defaults

defaults.config_logger()
plt.rcParams.update({"text.usetex": False}) # Until LateX is back 
sns.set_palette("pastel")


# Launch MAD-X Session
with open("stdout.out", "w") as f:
    madx = Madx(stdout=f)
    
    
# Read parameters
for i in parameters.keys():
    madx.globals[i] = parameters[i]
    

# Call sequence and optics
madx.call("elettra2_v15_VADER_2.3T.madx")
madx.call("optics_elettra2_v15_VADER_2.3T.madx");


# Initial twiss
madx.use(sequence="ring")
madx.twiss(sequence="ring")
init_twiss = madx.table.twiss.dframe().copy()

if settings["SAVE_TWISS"]:
    init_twiss.to_parquet("init_twiss.parquet")
    
# PLOTS

if settings["MAKE_PLOTS"]:
    
    if settings["SAVE_FIGS"]:
        fig_machine_save = 'full_machine.pdf'
    else:
        fig_machine_save = None

    fig_machine = LatticePlotter.plot_latwiss(madx, "Elettra Ring", figsize=(22, 12), 
                                              k0l_lim=(-7e-2, 7e-2), k1l_lim=(-1.5, 1.5),
                                              disp_ylim=(-madx.table.twiss.dx.max()*2, madx.table.twiss.dx.max()*2),
                                              plot_dipole_k1=True, lw=2, savefig=fig_machine_save)



    x0 = init_twiss.s[init_twiss.name == "ll:1"][0]
    x1 = init_twiss.s[init_twiss.name == "ll:3"][0]

    if settings["SAVE_FIGS"]:
        fig_cell_save = 'achromat.pdf'
    else:
        fig_cell_save = None

    fig_cell = LatticePlotter.plot_latwiss(madx, "Elettra Cell", figsize=(22, 12), xlimits=(x0, x1), 
                                              k0l_lim=(-7e-2, 7e-2), k1l_lim=(-1.5, 1.5),
                                              disp_ylim=(-madx.table.twiss.dx.max()*2, madx.table.twiss.dx.max()*2),
                                              plot_dipole_k1=True, lw=2, savefig=fig_cell_save)


    x0 = init_twiss.s[init_twiss.name == "ss:1"][0]
    x1 = init_twiss.s[init_twiss.name == "ss:2"][0]

    if settings["SAVE_FIGS"]:
        fig_cell_save = 'achromat_match.pdf'
    else:
        fig_cell_save = None

    fig_cell = LatticePlotter.plot_latwiss(madx, "Elettra Cells Long Straight", figsize=(22, 12), xlimits=(x0, x1), 
                                              k0l_lim=(-7e-2, 7e-2), k1l_lim=(-1.5, 1.5),
                                              disp_ylim=(-madx.table.twiss.dx.max()*2, madx.table.twiss.dx.max()*2),
                                              plot_dipole_k1=True, lw=2, savefig=fig_cell_save)



# Compute Emittance
madx.command.emit(deltap=madx.globals.deltap)


madx.quit()

# Get the emittance from the standard output
ex, ey, ez = elettra_toolbox.get_emittances_from_madx_output("stdout.out", to_meters=True)

print(f"ex = {ex*1e12} pm")
print(f"ey = {ey*1e12} pm")
print(f"ez = {ex*1e6} um")
