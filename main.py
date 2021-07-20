import subprocess
import yaml

from flask import Flask, request, redirect, url_for
from nested_lookup import nested_lookup

app = Flask(__name__)

# task_runner = {
#     'total_time' : 'time',
#     'task_run' : {
#         'task1': {
#             'time_slot' : 'time',
#             'resources' : {
#                 'cpu': "10",
#                 'disk': "12",
#                 'network': "10",
#             }
#         },
#         'task2': {
#             'time_slot' : 'time',
#             'resources' : {
#                 'cpu': "10",
#                 'disk': "12",
#                 'network': "10",
#             }
#         },
#     },
# }

# step_time = {
#     "start_load" : {
#         'cpu': 10,
#         'disk': 12,
#         'network': 10,
#     }
#     "time_step": 10
#     "step_load" : {
#         'cpu': 10,
#         'disk': 12,
#         'network': 10, 
#     }
#     "end_time": 10
# }

@app.route('/v1/runtask/fileupload/', methods = ['GET','POST'])
def postFile():
    if request.method =='POST':
        file = request.files['file'].read()
        print(type(file))
        if file:
            yaml_file = yaml.safe_load(file)
            if yaml_file['operationMode'] == 'step':
                return redirect(url_for('postJSON'))
            elif yaml_file['operationMode'] == 'time':
                return redirect(url_for('postJson'))
    return "Hi"

@app.route('/v1/runtask/time_vary', methods = ['GET','POST'])
def postJson():
    content = request.get_json()
    total_time = content['total_time']
    run_times = nested_lookup('time_slot',content)
    tasks = nested_lookup('resources', content)
    
    if sum(run_times) != total_time:
        return "Time slots does not match total time", 404
    else:
        for time,task in zip(run_times,tasks):
            cpu = task.get('cpu', 0)
            disk = task.get('disk', 0)

            subprocess.Popen(f'stress-ng --cpu {cpu} -t {time}', shell=True, stdout=subprocess.PIPE).stdout.read()
        
        return "Tasks run successfully"

@app.route('/v1/runtask/step_vary', methods = ['GET','POST'])
def postJSON():
    content = request.get_json()
    start_load = content['start_load']
    time_step = content['time_step']
    step_load = content['step_load']
    end_time = content['end_time']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000 ,debug=True)