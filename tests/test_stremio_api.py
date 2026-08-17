import requests

url = "http://127.0.0.1:11470/"

response = requests.get(url)

print(response.text)