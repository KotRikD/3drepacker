from subprocess import STDOUT, CalledProcessError, check_output
from typing import Union

TIME_ORDER_SUFFIXES = ["nsec", "μsec", "msec", "sec", "min", "hours"]

def magnitude_fmt_time(t: Union[int, float]) -> str:  # in nanosec
    for suffix in TIME_ORDER_SUFFIXES:
        if t < 1000:
            break
        t /= 1000
    return f"{t:.2f} {suffix}"

def system_call(command):
    """ 
    params:
        command: list of strings, ex. `["ls", "-l"]`
    returns: output, success
    """
    try:
        output = check_output(command, stderr=STDOUT).decode()
        success = True 
    except CalledProcessError as e:
        output = e.output.decode()
        success = False
    return output, success