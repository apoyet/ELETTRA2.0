import shlex
from pathlib import Path
from typing import Tuple, Union


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

