import yaml


def load_config(path: str = "configs/default.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
