import json
import locale
import os
import subprocess

import yaml
from flask import Flask, redirect, request, url_for
from nested_lookup import nested_lookup

app = Flask(__name__)

CMD_PREFIX = 'cmd : '
list_pids = []

def update_pids(pid):
    """update list of running pids, so they can be terminated at the end
    """
    global update_pids
    update_pids.append(pid)

def run_task (cpu,disk,io, time):
    """run the main task
    """
    cmd = f"stress-ng --cpu {cpu} --hdd {disk} --io {io} -t {time}"

    def handle_error(exception):
        """Handle errors by logging and optionally raising an exception.
        """
        print(
            'Unable to execute %(cmd)s. Exception: %(exception)s',
            {'cmd': ' '.join(cmd), 'exception': exception})
    
    try:
        proc = subprocess.Popen(map(os.path.expanduser, cmd), stdout=None, bufsize=0)
        while True:
            update_pids(proc.pid)

    except OSError as ex:
        handle_error(ex)

    else:
        if proc.returncode:
            ex = subprocess.CalledProcessError(proc.returncode, cmd, stderr)
            handle_error(ex)


def terminate_task_subtree(pid, signal='-15', sleep=10, logger=None):
    """Terminate given process and all its children
    Function will sent given signal to the process. In case
    that process will not terminate within given sleep interval
    and signal was not SIGKILL, then process will be killed by SIGKILL.
    After that function will check if all children of the process
    are terminated and if not the same terminating procedure is applied
    on any living child (only one level of children is considered).
    :param pid: Process ID to terminate
    :param signal: Signal to be sent to the process
    :param sleep: Maximum delay in seconds after signal is sent
    """
    try:
        children = subprocess.check_output("pgrep -P " + str(pid), shell=True).decode().rstrip('\n').split()
    except subprocess.CalledProcessError:
        children = []

    terminate_task(pid, signal, sleep)

    # just for case children were kept alive
    for child in children:
        terminate_task(child, signal, sleep)

def terminate_task(pid, signal='-15', sleep=10):
    """Terminate process with given pid
    Function will sent given signal to the process. In case
    that process will not terminate within given sleep interval
    and signal was not SIGKILL, then process will be killed by SIGKILL.
    :param pid: Process ID to terminate
    :param signal: Signal to be sent to the process
    :param sleep: Maximum delay in seconds after signal is sent
    """
    global list_pids
    
    if systeminfo.pid_isalive(pid):
        run_task(['sudo', 'kill', signal, str(pid)])
        for dummy in range(sleep):
            time.sleep(1)
            if not systeminfo.pid_isalive(pid):
                break

        if signal.lstrip('-').upper() not in ('9', 'KILL', 'SIGKILL') and systeminfo.pid_isalive(pid):
            terminate_task(pid, '-9', sleep)

    if pid in list_pids:
        pids.remove(pid)


def terminate_all_tasks():
    """Terminate all processes executed by vsperf, just for case they were not
    terminated by standard means.
    """
    global list_pids
    if update_pids:
        for pid in update_pids:
            terminate_task_subtree(pid)
        list_pids = []

@app.route("/v1/runtask/fileupload/", methods=["GET", "POST"])
def postFile():
    if request.method == "POST":
        file = request.files["file"].read()
        if file:
            yaml_file = yaml.safe_load(file)
            if yaml_file["operationMode"] == "step":
                return redirect(url_for(".postJSON", content=yaml_file))
            elif yaml_file["operationMode"] == "time":
                return redirect(url_for(".postJson", content=ymal_file))
    return "File Uploaded"

@app.route("/v1/runtask/time_vary", methods=["GET", "POST"])
def postJson():
    global list_pids
    if list_pids:
        terminate_all_tasks()

    json_content = request.args["content"]
    content = json.loads(json_content.replace("'", '"'))

    content = request.get_json()
    total_time = content["total_time"]
    run_times = nested_lookup("time_slot", content)
    tasks = nested_lookup("resources", content)
    

    if sum(run_times) != total_time:
        return "Time slots does not match total time", 404
    else:
        for time, task in zip(run_times, tasks):
            cpu = task.get("cpu", 0)
            disk = task.get("disk", 0)
            io = task.get("io", 0)

            run_task(cpu,disk,io,time)
        
    return "Tasks run successfully"


@app.route("/v1/runtask/step_vary", methods=["GET", "POST"])
def postJSON():
    global list_pids
    if list_pids:
        terminate_all_tasks()

    json_content = request.args["content"]
    content = json.loads(json_content.replace("'", '"'))

    start_load = content["start_load"]
    time_step = content["time_step"]
    step_load = content["step_load"]
    end_time = content["end_time"]

    cpu = start_load.get("cpu", 0)
    disk = start_load.get("disk", 0)
    io = start_load.get("io", 0)


    for time in range(1, end_time, time_step):

        run_task(cpu,disk,io,time)
        
        cpu = cpu + step_load.get("cpu", 0)
        disk = cpu + step_load.get("disk", 0)
        io = cpu + step_load.get("io", 0)

    return "Tasks run successfully"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)