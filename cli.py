import os
import requests

print("Welcome to the stress-ng-cli tool!")

input_file = input("Enter the location of the configuration file for stress-ng-cli : \n")
server_lists = [int(x) for x in input("Enter the IP address of various servers").split()]

files = {}
files['file'] = open(f'{os.path.abspath(input_file)}', 'rb')

for ip in server_list:
    BASE_URL = f'http://{ip}:8700'
    response = requests.post(url=f'{BASE_URL}/v1/runtask/fileupload/', files=files)
    if response.status_code == 201:
        print(f"Configuration file uploaded to {ip} server")
    else:
        print(f'Error: {response.text}')