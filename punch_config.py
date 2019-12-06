__config_version__ = 1

default = (
    "{{major}}.{{minor}}.{{patch}}{{status if status}}{{count if status}}"
)

GLOBALS = {
    "serializer": default,
}

FILES = ["setup.py", "feedinlib/__init__.py"]

VERSION = [
    "major",
    "minor",
    "patch",
    {"name": "status", "type": "value_list", "allowed_values": ["", "rc"]},
    {"name": "count", "type": "integer", "start_value": 1},
]
