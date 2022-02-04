import yaml

def get_value(key):
    path = "development.yaml"
    with open(path, 'rt') as stream:
        config = yaml.safe_load(stream.read())
        return config[key]
