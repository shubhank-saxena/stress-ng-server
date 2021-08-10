import os
import subprocess


def get_pids(proc_names_list):
    """Get pid(s) of process(es) with given name(s)
    :returns: list with pid(s) of given processes or None if processes
        with given names are not running
    """

    try:
        pids = subprocess.check_output(['sudo', 'LC_ALL=', 'pidof'] + proc_names_list)
    except subprocess.CalledProcessError:
        # such process isn't running
        return None

    return list(map(str, map(int, pids.split())))


def get_pid(proc_name_str):
    """Get pid(s) of process with given name
    :returns: list with pid(s) of given process or None if process
        with given name is not running
    """
    return get_pids([proc_name_str])


def pid_isalive(pid):
    """Checks if given PID is alive
    :param pid: PID of the process
    :returns: True if given process is running, False otherwise
    """
    return os.path.isdir('/proc/' + str(pid))
