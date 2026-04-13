import yaml

def load_servers():
    with open("config/servers_testing.yaml") as f:
        return yaml.safe_load(f)["servers"]
