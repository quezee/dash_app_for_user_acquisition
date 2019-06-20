import json

class Config:

    def __init__(self, env_path='environments.json'):

        with open(env_path, 'r') as f:
            data = json.load(f)

        for key, value in data.items():
            setattr(self, key, value)