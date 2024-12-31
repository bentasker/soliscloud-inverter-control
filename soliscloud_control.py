#!/usr/bin/env python3
#


# Copyright (c) 2024, B Tasker
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

import datetime
import base64
import hashlib
import hmac
import json
import os
import requests
import sys
import time


class SolisCloud:

    def __init__(self, config, session=False, debug=False):
        self.config = config
        self.debug = debug
        if session:
            self.session = session
        else:
            self.session = requests.session()

        # Tracking information for rate limit observance
        self.ratelimit = {
            "requests" : 0,
            "lastreset" : time.time()
            }

    def checkRateLimit(self):
        ''' Check how many requests we've made and when
        in order to assess whether we're at risk of hitting
        service rate limits.
        
        The API doc says:
        
            Note: The calling frequency of all interfaces is limited to three times every five seconds for the same IP
        
        It does not clarify whether we'll get a HTTP 429 or some other status
        '''
        
        # What we want to check is
        #
        # Was the last reset more than 5 seconds ago
        # Have there been >= 3 requests?
        #
        now = time.time()
        # When was the last quota reset?
        if (now - self.ratelimit['lastreset']) >= 5:
            self.printDebug(f'RATE_LIMIT_CHECK: Last reset was more than 5 seconds ago')
            # Should be fine, reset the limit
            self.ratelimit['lastreset'] = now
            self.ratelimit['requests'] = 1
            return True
        
        # If we reached this point, we're within the n second boundary
        # check how many requests have been placed
        if (self.ratelimit['requests'] + 1) > self.config['api_rate_limit']:
            self.printDebug(f'RATE_LIMIT_CHECK: Breach - too many requests')
            # We'd be breaching the rate limit
            #
            # We don't increment the counter because we're
            # preventing the request from being sent yet
            return False
        
        # So we're within the time bounds but haven't yet hit the maximum number of
        # requests. Increment the counter and approve the request
        self.printDebug(f'RATE_LIMIT_CHECK: Request approved')
        self.ratelimit['requests'] += 1
        return True

    def createHMAC(self, signstr, secret, algo):
        ''' Create a HMAC of signstr using secret and algo
        
        https://snippets.bentasker.co.uk/page-1910021144-Generate-HMACs-with-different-algorithms-Python3.html
        '''
        hashedver = hmac.new(secret.encode('utf-8'),signstr.encode('utf-8'),algo)
        return hashedver.digest()


    def doAuth(self, key_id, secret, req_path, req_body, method="POST", content_type="application/json", datestring=False):
        ''' Calculate an authorization header value to accompany the request
        
        Solis' API docs describe the method as:
        
            Authorization = "API " + KeyId + ":" + Sign
            Sign = base64(HmacSHA1(KeySecret,
            VERB + "\n"
            + Content-MD5 + "\n"
            + Content-Type + "\n"
            + Date + "\n"
            + CanonicalizedResource))
            
            
        Note: the API wants MD5s and SHA1s to be digests and not hexdigests
        '''
        
        # Calculate an MD5 of the request body
        # if there's no body, the hash should be empty
        if len(req_body) > 0:
            content_md5 = hashlib.md5(req_body.encode()).digest()
            md5_str = base64.b64encode(content_md5).decode()
            self.printDebug(f"Request body: {req_body}")
        else:
            md5_str = ''
            self.printDebug(f"Empty Request body")
        
        # If there's no override, generate the current UTC date
        # in HTTP header format
        if not datestring:
            self.printDebug(f"Calculating date")
            d = datetime.datetime.now(tz=datetime.timezone.utc)
            datestring = d.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Construct the string that we need to sign
        # The entries should be seperated by a newline
        signstr = '\n'.join([method,
                md5_str,
                content_type,
                datestring,
                req_path
                ])
        
        self.printDebug(f"Signstr: {signstr}")
        
        # HMAC and then base64 it
        hmacstr = self.createHMAC(signstr, secret, 'sha1')
        signature = base64.b64encode(hmacstr).decode()
        
        # Take the values and construct the header value
        auth_header = f"API {key_id}:{signature}"
        self.printDebug(f"Calculated Auth header: {auth_header}")
        
        
        # build headers
        headers = {
            "Content-Type" : content_type,
            "Content-MD5" : md5_str,
            "Date" : datestring,
            "Authorization" : auth_header
            }
        
        return headers

    def postRequest(self, url, headers, data):
        ''' Place a request to the API, taking into account
         internal rate-limit tracking
        '''
        
        # Check whether this request would hit the service's published rate-limit
        x = 0
        while True:
            if self.checkRateLimit():
                # We're below the rate limit, break out
                # so the request can be placed
                break
                
            # Otherwise, this request would hit the rate limit wait a bit and try again
            x += 1
            time.sleep(1)
            if x > self.config("max_ratelimit_wait"):
                self.printDebug("Max ratelimit wait exceeded - something's gone wrong, please report it")
                sys.exit(1)
            continue
        
        # Place the request
        return self.session.post(url=url, headers=headers, data=data)
        

    def printDebug(self, msg):
        if self.debug:
            print(msg)
        

    def readChargeDischargeSchedule(self, sn):
        ''' Place a request to the API to read the charge schedule settings
        '''
        
        # Construct the request body
        req_body_d = {
                "inverterSn": sn,
                "cid" : 103
            }
        req_body = json.dumps(req_body_d)
        req_path = "/v2/api/atRead"
        
        # Construct an auth header
        headers = self.doAuth(self.config['api_id'], self.config['api_secret'], req_path, req_body)
                
        self.printDebug(f'Built request - Headers {headers}, body: {req_body}, path: {req_path}')
               
        # Place the request
        r = self.postRequest(
            f"{self.config['api_url']}{req_path}",
            headers,
            req_body
            )
        
        resp = r.json()
        self.printDebug(f'Got response: {resp}')
        
        if not resp or "msg" not in resp or resp['msg'] != "success":
            return False
        
        return resp
        

# Utility functions to help with __main__ runs


def configFromEnv():
    ''' Build a dict of configuration settings based on environment variables
    '''
    return {
        "inverter" : os.getenv("INVERTER_SERIAL", "aaa-bbb-ccc"),
        "api_id" : int(os.getenv("API_ID", 1234)),
        "api_secret" : os.getenv("API_SECRET", "abcde"),
        "api_url" : os.getenv("API_URL", "https://tobeconfirmed").strip('/'),
        # Max number of requests per 5 seconds
        "api_rate_limit" : int(os.getenv("API_RATE_LIMIT", 2)),
        # This is a safety net - maximum seconds to wait if we believe we'll
        # hit the rate limit. As long as this is higher than api_rate_limit it
        # should never actually be hit unless there's a bug.
        "max_ratelimit_wait" : int(os.getenv("API_RATE_LIMIT_MAXWAIT", 8)),
        "measurement" : os.getenv("MEASUREMENT", "solar_inverter")
        }


if __name__ == "__main__":
    # Are we running in debug mode?
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    config = configFromEnv()    
    soliscloud = SolisCloud(config, debug=DEBUG)
    
    res = soliscloud.readChargeDischargeSchedule(config['inverter'])
    print(res)
    
