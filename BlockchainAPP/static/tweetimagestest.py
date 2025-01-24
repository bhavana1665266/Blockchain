import ipfsApi
import base64
import pickle
api = ipfsApi.Client(host='http://127.0.0.1', port=5001)

file = open("112.jpg","rb")
data = file.read()
file.close()

data = pickle.dumps(data)

new_file = api.add_pyobj(data)
print(new_file)

content = api.get_pyobj(new_file)
#print(content)
content = pickle.loads(content)
with open("temp.png", "wb") as file:
    file.write(content)
file.close()
