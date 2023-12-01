import os
import yaml

file_to_create = os.path.join(f"{os.path.expanduser('~')}/Documents/ERPNotifier", "config.yaml")

if not os.path.exists(f"{os.path.expanduser('~')}/Documents/ERPNotifier"):
    os.mkdir(f"{os.path.expanduser('~')}/Documents/ERPNotifier")
    
with open(file_to_create, 'w') as cred:
    username = input("Enter Username/LoginID: ")
    password = input("Enter Password: ")
    data = {'username': username, 'password': password, 'total_assignments': 0, 'total_attendance':0}
    yaml.dump(data, cred)
