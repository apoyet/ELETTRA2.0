import logging
import shlex
from pathlib import Path
from typing import Tuple, Union, Dict
import sys

from cpymad.madx import Madx, TwissFailed

LOGGER = logging.getLogger(name=__name__)
LOGGER.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

import os
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from matplotlib import cm, gridspec, patches
from pyhdtoolkit import cpymadtools

plt.rcParams.update({"text.usetex": False})



def get_emittances_from_madx_output(madx_output_file: Union[str, Path], to_meters: bool = False) -> Tuple[float, float, float]:
    """
    Parse MAD-X output file and return the X, Y and Z emittances from the output of the last called EMIT command.
    
    Args:
        madx_output_file (Union[str, Path]): Path to the MAD-X output file. Can be a string, in which case it will be 
            converted to a Path object first.
        to_meters (bool): if True, convert the emittances to meters before returning. Defaults to False in order to
            give back the exact output from MAD-X.
    """
    scaling_factor = 1e6 if to_meters is True else 1
    output_file_path = Path(madx_output_file)
    output_lines = output_file_path.read_text().split("\n")
    last_emit_call_output = [line for line in output_lines if line.startswith(" Emittances [pi micro m]")][-1]  # take the last one

    parsed_emit_output = shlex.split(last_emit_call_output)

    emittance_x = float(parsed_emit_output[4]) / scaling_factor
    emittance_y = float(parsed_emit_output[5]) / scaling_factor
    emittance_z = float(parsed_emit_output[6]) / scaling_factor
    return emittance_x, emittance_y, emittance_z


def check_closed_machine(madx: Madx, tol: float = 1e-3) -> Tuple[float, float]:
    """
    This method checks if the machine is properly closed after running the SURVEY command of MAD-X. From the survey, it computes
    the difference in x and z between the start and the end of the ring. If one of these differences is larger that the set 
    tolerance (default at 1 mm), it raises an error. If the test is passed then the function returns the afordmentioned differences.
    
    Args: 
        madx (Madx): Madx instance currently running 
        tol (float): tolerance for the machine to be considered closed in meters (default: 1e-3 [m])
        
    Returns:
        (x_diff, z_diff) (tuple): computed differences for x and z, from the survey, between the start and the end of the ring
    
    Raises: 
        If x_diff or z_diff is larger than the set tolerance, raises an error. 
    """
    LOGGER.debug("Running survey on the machine")
    madx.command.survey()
    survey = madx.table.survey.dframe().copy()
    x_diff = abs(survey.x["#s"] - survey.x["#e"])
    z_diff = abs(survey.z["#s"] - survey.z["#e"])
    assert x_diff < tol, "Machine is not closed, tolerance in x not met"
    assert z_diff < tol, "Machine is not closed, tolerance in z not met"
    LOGGER.info(f"Machine seems closed with respect to the provided tolerance ({tol*1e3} [mm])")
    return x_diff, z_diff


######################################################################################################

from dataclasses import dataclass, field


@dataclass
class ScanConfig:
    variable_name: str
    initial_value: float
    scan_start: float
    scan_end: float
    n_points: int
    scan_space: np.ndarray = field(init=False)

    def __post_init__(self):
        self.scan_space = np.linspace(self.scan_start, self.scan_end, self.n_points)
        
        
def scan_param_for_emittance(madx: Madx, parameter_space: ScanConfig, madx_output_file: Union[str, Path], tol_closed_machine: float = 1e-3) -> pd.DataFrame:
    """
    Scans a parameter among the MADX instance globals, and returns the computed emittances in a pandas DataFrame. 
    
    Args:
        madx (Madx): running cpymad MAD-X instance (the one that you are using)
        parameter_space (ScanConfig): ScanConfig containing the information regarding the scan you are performing. This ScanConfig should have
                                the form {'variable': str, 'init_value': float, 'scan_to_perform': np.array}, as defined in the Data Class above. 
        madx_output_file (Union[str, Path]): Path to the MAD-X output file. Can be a string, in which case it will be converted to a Path 
                                                object first.
        tol_closed_machine (float): tolerance to be used when checking if the machine is closed (default to 1e-3 [m]) 
        
    
    Returns: 
        emit_results (pd.DataFrame): pandas DataFrame containing the results of the parameter scan in terms of emittances 
    """
    LOGGER.info(f"Scanning parameter {parameter_space.variable_name} for emittance results.")
    emit_results = pd.DataFrame(index=parameter_space.scan_space)
    emit_results.index.name = parameter_space.variable_name
    ex_res, ey_res, ez_res = [], [], []

    for param_value in parameter_space.scan_space:
        LOGGER.debug(f"Attempting emittance calculation for value of {param_value:.5f}")
        madx.globals[parameter_space.variable_name] = param_value
        try:
            madx.twiss()
            check_closed_machine(madx, tol=tol_closed_machine)
            madx.command.emit(deltap=madx.globals.deltap)
            madx.command.emit(deltap=madx.globals.deltap)
            ex, ey, ez = get_emittances_from_madx_output(madx_output_file, to_meters=True)
            ex_res.append(ex)
            ey_res.append(ey)
            ez_res.append(ez)
        except TwissFailed:
            LOGGER.debug("Twiss failed for this configuration, defaulting to NaN and skipping ahead.")
            ex_res.append(np.nan)
            ey_res.append(np.nan)
            ez_res.append(np.nan)
        except AssertionError:
            LOGGER.debug("Machine not closed for this configuration, defaulting to NaN and skipping ahead.")
            ex_res.append(np.nan)
            ey_res.append(np.nan)
            ez_res.append(np.nan)

    emit_results["ex"] = ex_res
    emit_results["ey"] = ey_res
    emit_results["ez"] = ez_res
    return emit_results







