# Stress-ng REST server
This is a very basic Flask based REST server which takes in the stress-ng factors like compute,storage and netwok along with time and allows to run time varying stress tests. There are three modes available -

## 1. Step Varying Mode
This mode allows to increase the loads by some fixed unit and at some fixed step time. A sample json would be as follows - 
```python
step_time = {
    "start_load" : {
        'cpu': 10,
        'disk': 12,
        'network': 10,
    }
    "time_step": 10
    "step_load" : {
        'cpu': 10,
        'disk': 12,
        'network': 10, 
    }
    "end_time": 10
} 
```
This is available on the route - `http://localhost/v1/runtask/step_vary`

## 2. Time Varying Mode
This mode allows to set stres loads for a particular time span. A sample json would be as follows -
```python
task_runner = {
    'total_time' : 20,
    'task_run' : {
        'task1': {
            'time_slot' : 10,
            'resources' : {
                'cpu': 10,
                'disk': 12,
                'network': 10,
            }
        },
        'task2': {
            'time_slot' : 10,
            'resources' : {
                'cpu': 10,
                'disk': 12,
                'network': 10,
            }
        },
    },
}
```
This is available on the route - `http://localhost/v1/runtask/time_vary`

## 3. File Upload Mode
To make sure to pass the configurations as a configuration file, we can post a `yaml` file with a similar json configration with starting field as `operationMode` in the file.

- If the `operationMode == step`, this will run the application in step varying mode.

- If the `operationMode == time`, this will run the application in time varying mode.

This is available on the route - `http://localhost/v1/runtask/fileupload`

### For all the use cases, you can find samples in the samples folder.
## How to run the tool
## 1. Docker
- Run `docker-compse build` to build the image.
- Run `docker-compose run` to spawn up the image. This will run a server at `localhost:8000`
## 2. Pipenv
- Install pipenv on your system using `pip3 install pipenv`
- Then run `pipenv shell` inside this repo. This will create virtualenv for the project.
- Then run `pipenv install` so that it installs all the dependencies required for the project.
- Run `python main.py`. This will fire up the flask server and then you can run the stress-ng via REST!
**If you face any issue with python version, change the python version in the pipfile to the one that is there on your system**
