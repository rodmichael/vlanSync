## Work with virtual environment

Create venv
```
python3 -m venv vlanSyncVenv
```

Activate venv
```
source vlanSyncVenv/bin/activate
```

Install pre-required packages
```
pip3 install -r requirements
```

## Configuration
Modify config.json accordingly Example:
```
{
    "databaseDetails": {
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "dbName": "VLANS"
    },
    "switchDetails": {
        "switch": "192.168.0.10",
        "username": "cisco",
        "privateKeyPath": "/path/to/private/key.pem"
    }
}
```

## Run
```
python3 main.py -p <DATABASE_PASSWORD>
```
