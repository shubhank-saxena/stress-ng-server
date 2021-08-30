import json
import logging
import os
import subprocess

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


@app.route("/v1/runtask/time_vary", methods=["GET", "POST"])
def postJson():

    terminate_all_tasks(logging.getLogger(__name__))

    json_content = request.args["content"]
    content = json.loads(json_content.replace("'", '"'))

    content = request.get_json()
    total_time = content["total_time"]
    run_times = nested_lookup("time_slot", content)
    tasks = nested_lookup("resources", content)

    if sum(run_times) != total_time:
        return "Time slots does not match total time", 404
    else:
        for time_run, task in zip(run_times, tasks):
            cpu = task.get("cpu", 0)
            disk = task.get("disk", 0)
            io = task.get("io", 0)

            cmd = ["stress-ng", "--cpu", f"{cpu}", "--hdd", f"{disk}", "--io", f"{io}", "-t", f"{time_run}"]

    return "Tasks run successfully"


@app.route("/v1/runtask/step_vary", methods=["GET", "POST"])
def postJSON():

    terminate_all_tasks(logging.getLogger(__name__))

    json_content = request.args["content"]
    content = json.loads(json_content.replace("'", '"'))

    start_load = content["start_load"]
    time_step = content["time_step"]
    step_load = content["step_load"]
    end_time = content["end_time"]

    cpu = start_load.get("cpu", 0)
    disk = start_load.get("disk", 0)
    io = start_load.get("io", 0)

    for time_run in range(1, end_time, time_step):

        cmd = ["stress-ng", "--cpu", f"{cpu}", "--hdd", f"{disk}", "--io", f"{io}", "-t", f"{time_run}"]
        run_background_task(cmd, logging.getLogger(__name__), 'Starting Step Runner')

        cpu = cpu + step_load.get("cpu", 0)
        disk = cpu + step_load.get("disk", 0)
        io = cpu + step_load.get("io", 0)

    return "Tasks run successfully"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
