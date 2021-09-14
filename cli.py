import click
import os
import requests


BASE_URL = 'http://localhost:8000'
print("Welcome to the stress-ng-cli tool!")

@click.group()
def apis():
    """A CLI tool for stress-ng-server."""

@apis.command()
def configure():
    input_file = input("Enter the location of the configuration file for stress-ng-cli")

    files = {}
    files['file'] = open(f'{os.path.abspath(input_file)}', 'rb')
    response = requests.post(url=f'{BASE_URL}/v1/runtask/fileupload/', files=files)
    if response.status_code == 201:
        print("Configuration file uploaded")
    else:
        print(f'Error: {response.text}')