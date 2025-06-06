#!/usr/bin/env python3
#
# Example Control Server
#
# This is a small flask app to expose an API
# allowing remote clients to pass calls by us
#
# Copyright (c) 2025, B Tasker
# Released under BSD 3-Clause License
#

'''
Copyright (c) 2023, B Tasker

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of
conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of
conditions and the following disclaimer in the documentation and/or other materials
provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used
to endorse or promote products derived from this software without specific prior written
permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import os
import soliscloud_control

from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route('/')
def version():
    
    if not checkAuth(request.authorization):
        return Response(status=403)

    return "Soliscloud Control - no auth headers\n"    

@app.route('/api/v1/setCurrent', methods=['POST'])
def setCurrent():
    ''' Change the configured current but don't change schedules
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    

    rates = getCurrents(request.get_json(silent=True))
    
    if not rates:
        return Response(status=400)
    
    if soliscloud.setCurrents(rates):
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/startCharge', methods=['POST'])
def startCharge():
    ''' Trigger charging 
    '''
    
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    hours = 3
    exact = False
    
    # Read the request body if present
    req = request.get_json(silent=True)
    
    # Get desired charge/discharge rates if provided
    rates = getCurrents(req)
    
    # Was there valid json in the request
    if req: 
        if "end" in req:
            # Split out the hours and minutes
            t1 = req["end"].split(" ")[1]
            t2 = t1.split(":")
            exact = {
                "hour" : int(t2[0]),
                "minute" : int(t2[1])
                }
    
    # TODO check if hours are specified
    if soliscloud.startCharge(hours, exact, rates):
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/startDischarge', methods=['POST'])
def startDischarge():
    ''' Trigger charging 
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # Read the request body if present
    req = request.get_json(silent=True)
    
    # Get desired charge/discharge rates if provided
    rates = getCurrents(req)
    
    # TODO check if hours are specified
    if soliscloud.startDischarge(rates):
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/stopCharge', methods=['POST'])
def stopCharge():
    ''' Trigger charging 
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # Read the request body if present
    req = request.get_json(silent=True)
    
    # Get desired charge/discharge rates if provided
    rates = getCurrents(req)
    
    # TODO check if hours are specified
    if soliscloud.stopCharge(rates):
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/stopDischarge', methods=['POST'])
def stopDischarge():
    ''' Trigger charging 
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # Read the request body if present
    req = request.get_json(silent=True)
    
    # Get desired charge/discharge rates if provided
    rates = getCurrents(req)
    
    # TODO check if hours are specified
    if soliscloud.stopDischarge(rates):
        return Response(status=200)
    else:
        return Response(status=502)


def checkAuth(auth):
    ''' If auth is enabled, check authentication
    '''
    
    if not DO_AUTH:
        # No auth needed
        return True
    
    if not auth:
        # No creds in request
        return False
    
    if auth["username"] == USER and auth["password"] == PASS:
        return True
    
    return False


def getCurrents(req):
    ''' Check if the request provides currents
    '''
    rates = False
    
    if not req or ("charge_current" not in req and "discharge_current" not in req):
        return False

    rates = {}
    if "charge_current" in req:
        rates["charge_current"] =  req['charge_current']
        
    if "discharge_current" in req:
        rates["discharge_current"] = req['discharge_current']
    
    return rates


if __name__ == "__main__":

    # Are we running in debug mode?
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    DO_AUTH = os.getenv("DO_AUTH", "false").lower() == "true"
    
    if DO_AUTH:
        USER = os.getenv("USER", "solisuser")
        PASS = os.getenv("PASS", False)
        if not PASS:
            import random, string
            PASS = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
            print(f"Generated random password: {USER} / {PASS}")
    
    config = soliscloud_control.configFromEnv()    
    soliscloud = soliscloud_control.SolisCloud(config, debug=DEBUG)
    
    app.run(host="0.0.0.0", port=8080, debug=DEBUG)
