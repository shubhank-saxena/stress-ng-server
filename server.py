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

    #stress-ng --memrate 1  -t 20 --memrate-bytes 128M  --memrate-rd-mbs 256M --memrate-wr-mbs 512M.



    if sum(run_times) != total_time:
        return "Time slots does not match total time", 404
    else:
        for time_run, task in zip(run_times, tasks):
            cpu = tasks.get("cpu", 0)
            disk_rate = tasks["disk"].get("memrate", 0)
            disk_size = tasks["disk"].get("memrate-bytes", 0)
            read_size = task["disk"].get("mem-read-size", 0)
            write_size = task["disk"].get("mem-write-size", 0)
            tcp_workers = tasks["network"]["tcp"].get("tcp-workers", 0)
            tcp_destination = tasks["network"]["tcp"].get("tcp-domain","localhost")
            udp_workers = tasks["network"]["udp"].get("udp-workers",0)
            udp_destination = tasks["network"]["udp"].get("udp-domain","localhost")

            cmd = ["stress-ng", "--cpu", f"{cpu}", "--memrate", f"{disk_rate}", "--memrate-bytes", f"{disk_size}", "--memrate-rd-mbs", f"{read_size}", "--memrate-wr-mbs", f"{write_size}", "--sock", f"{tcp_workers}", "--sock-domain", f"{tcp_destination}", "--udp", f"{udp_workers}", "--udp-domain", f"{udp_destination}", "-t", f"{time_run}"]
            run_background_task(cmd, logging.getLogger(__name__), 'Starting Time Runner')

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
    disk_rate = tasks["disk"].get("memrate", 0)
    disk_size = tasks["disk"].get("memrate-bytes", 0)
    read_size = task["disk"].get("mem-read-size", 0)
    write_size = task["disk"].get("mem-write-size", 0)
    tcp_workers = start_load["network"]["tcp"].get("tcp-workers", 0)
    tcp_destination = start_load["network"]["tcp"].get("tcp-domain","localhost")
    udp_workers = start_load["network"]["udp"].get("udp-workers", 0)
    udp_destination = start_load["network"]["udp"].get("udp-domain","localhost")

    for time_run in range(0, end_time, time_step):
        cmd = ["stress-ng", "--cpu", f"{cpu}", "--memrate", f"{disk_rate}", "--memrate-bytes", f"{disk_size}", "--memrate-rd-mbs", f"{read_size}", "--memrate-wr-mbs", f"{write_size}", "--sock", f"{tcp_workers}", "--sock-domain", f"{tcp_destination}", "--udp", f"{udp_workers}", "--udp-domain", f"{udp_destination}", "-t", f"{time_run}"]
        run_background_task(cmd, logging.getLogger(__name__), 'Starting Step Runner')

        cpu = cpu + step_load.get("cpu", 0)
        disk_rate = disk_rate + step_load["disk"].get("memrate", 0)
        disk_size = disk_size + step_load["disk"].get("memrate-bytes", 0)
        read_size = read_size + step_load["disk"].get("mem-read-size", 0)
        write_size = write_size + step_load["disk"].get("mem-write-size", 0)
        tcp_workers = tcp_workers + step_load["network"]["tcp"].get("tcp-workers", 0)
        udp_workers = udp_workers + step_load["network"]["udp"].get("udp-workers",0)

    return "Tasks run successfully"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
