import json
import logging
import os
import subprocess
import time
import yaml

from conf import settings
from flask import Flask, redirect, request, url_for
from nested_lookup import nested_lookup

from tools.tasks import run_background_task, terminate_all_tasks

_CURR_DIR = os.path.dirname(os.path.realpath(__file__))
settings.load_from_dir(os.path.join(_CURR_DIR, 'conf'))

app = Flask(__name__)

@app.route("/v1/runtask/fileupload/", methods=["GET", "POST"])
def postFile():
    if request.method == "POST":
        file = request.files["file"].read()
        if file:
            yaml_file = yaml.safe_load(file)
            if yaml_file["operationMode"] == "step":
                return redirect(url_for(".postJSON", content=yaml_file))
            elif yaml_file["operationMode"] == "time":
                return redirect(url_for(".postJson", content=yaml_file))
    return "File Uploaded"


def dict_formation(load):
    cmd_dict = {}
    #CPU Configurations
    cmd_dict["cpu"] = load.get("cpu", "NA")
    #Disk Configurations
    if "disk" in load.keys():
        cmd_dict["memrate"] = load["disk"].get("memrate", "NA")
        cmd_dict["memrate-bytes"] = load["disk"].get("memrate-bytes", "NA")
        cmd_dict["memrate-rd-mbs"] = load["disk"].get("mem-read-size", "NA")
        cmd_dict["memrate-wr-mbs"] = load["disk"].get("mem-write-size", "NA")
    #Network Configurations
    if "network" in load.keys():
        cmd_dict["sock"] =load["network"]["tcp"].get("tcp-workers", "NA")
        cmd_dict["sock-domain"] = load["network"]["tcp"].get("tcp-domain","NA")
        cmd_dict["udp"] = load["network"]["udp"].get("udp-workers", "NA")
        cmd_dict["udp-domain"] =load["network"]["udp"].get("udp-domain","NA")
    return cmd_dict


@app.route("/v1/runtask/time_vary", methods=["GET", "POST"])
def postJson():

    terminate_all_tasks(logging.getLogger(__name__))

    json_content = request.args["content"]
    content = json.loads(json_content.replace("'", '"'))

    total_time = content["total_time"]
    run_times = nested_lookup("time_slot", content)
    tasks = nested_lookup("resources", content)

    if sum(run_times) != total_time:
        return "Time slots does not match total time", 404
    else:
        for time_run, task in zip(run_times, tasks):
            load = dict_formation(task)
            
            cmd = ["stress-ng", "-t", f"{time_run}"]

            for key in load:
                if load[key] != "NA":
                    cmd.append(f"--{key}")
                    cmd.append(f"{load[key]}")
            
            run_background_task(cmd, logging.getLogger(__name__), 'Starting Time Runner')

            time.sleep(time_run)

    return "Tasks run successfully"


@app.route("/v1/runtask/step_vary", methods=["GET", "POST"])
def postJSON():

    terminate_all_tasks(logging.getLogger(__name__))

    json_content = request.args["content"]
    content = json.loads(json_content.replace("'", '"'))

    start_load = dict_formation(content["start_load"])
    step_load = dict_formation(content["step_load"])
    time_step = content["time_step"]
    end_time = content["end_time"]

    for time_run in range(0, end_time, time_step):

        cmd = ["stress-ng", "-t", f"{time_step}"]
        
        for key in start_load:
            if start_load[key] != "NA":
                cmd.append(f"--{key}")
                cmd.append(f"{start_load[key]}")
        
        run_background_task(cmd, logging.getLogger(__name__), 'Starting Step Runner')
        time.sleep(time_step)

        for key in start_load:
            if start_load[key] != "NA" and step_load[key] != "NA":
                if key == "memrate-bytes":
                    start_load[key] = str(int(start_load[key][:-1]) + int(step_load[key][:-1]))+start_load[key][-1]
                else:
                    start_load[key] = start_load[key] + step_load[key]

    return "Tasks run successfully"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8700, debug=True)
