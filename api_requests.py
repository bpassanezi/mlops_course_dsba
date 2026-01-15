import requests

url = 'http://127.0.0.1:8000/scoring/'

input_request = {'address': 'my_address', 'surface': 10, 'num_rooms': 2}
x = requests.post(url, json = input_request)
print("Input : ", input_request, "Output: ", x.text)

input_request = {'address': 'my_address', 'surface': 100, 'num_rooms': 2}
x = requests.post(url, json = input_request)
print("Input : ", input_request, "Output: ", x.text)

input_request = {'address': 'my_address', 'surface': 100, 'num_rooms': 3}
x = requests.post(url, json = input_request)
print("Input : ", input_request, "Output: ", x.text)

input_request = {'address': 'my_address', 'surface': 100}
x = requests.post(url, json = input_request)
print("Input : ", input_request, "Output: ", x.text)

input_request = {'address': 10, 'surface': 100}
x = requests.post(url, json = input_request)
print("Input : ", input_request, "Output: ", x.text)
