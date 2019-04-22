from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import requests

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()
OW_APIHOST = os.getenv('OW_APIHOST')
OW_NAMESPACE = os.getenv('OW_NAMESPACE')
OW_AUTH = os.getenv('OW_AUTH')
print(OW_APIHOST, OW_NAMESPACE, OW_AUTH)
app = Flask(__name__)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="localhost", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]
    trigger_name = "vote_created"
    vote = None
    openwhisk_url = OW_APIHOST + '/api/v1/namespaces/' + OW_NAMESPACE + '/triggers/' + trigger_name
    ow_auth = OW_AUTH.split(':')

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)
        headers = {'Content-Type': 'application/json'}        
        # Trigger Openwhisk Action to read from redis
        response = requests.post(openwhisk_url, data=data, auth=(ow_auth[0], ow_auth[1]), headers=headers)
        print(response.text)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
