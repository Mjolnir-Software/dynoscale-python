# Dynoscale for workers

## Dev/Testing

- cd into `examples/flask_rq`
- start `redis-server` in one terminal window
- start `redis-cli monitor` in another terminal window
- install dependencies: `pip install -r requirements.txt`
- make sure to `source venv/bin/activate` before each of the following commands
- start `python3 -m worker` in yet another terminal
- start `python3 -m web` in yet another but finally last terminal
- now you can `open http://127.0.0.1:3000`