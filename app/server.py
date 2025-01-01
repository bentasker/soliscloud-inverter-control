#!/usr/bin/env python3
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

app = Flask(__name__)

@app.route('/')
def version():
    
    if not checkAuth(request.authorization):
        return Response(status=403)

    return "Soliscloud Control - no auth headers\n"    

    

@app.route('/api/v1/startCharge', methods=['POST'])
def startCharge():
    ''' Trigger charging 
    '''
    
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # TODO check if hours are specified
    if soliscloud.startCharge():
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/startDischarge', methods=['POST'])
def startDischarge():
    ''' Trigger charging 
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # TODO check if hours are specified
    if soliscloud.startDischarge():
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/stopCharge', methods=['POST'])
def stopCharge():
    ''' Trigger charging 
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # TODO check if hours are specified
    if soliscloud.stopCharge():
        return Response(status=200)
    else:
        return Response(status=502)

@app.route('/api/v1/stopDischarge', methods=['POST'])
def stopDischarge():
    ''' Trigger charging 
    '''
    if not checkAuth(request.authorization):
        return Response(status=403)    
    
    # TODO check if hours are specified
    if soliscloud.stopDischarge():
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
