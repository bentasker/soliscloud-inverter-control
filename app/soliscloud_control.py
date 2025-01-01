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

import datetime
import base64
import hashlib
import hmac
import json
import os
import re
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
        if (now - self.ratelimit['lastreset']) >= 1:
            self.printDebug(f'RATE_LIMIT_CHECK: Last reset was more than 1 seconds ago')
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
            if x > self.config["max_ratelimit_wait"]:
                self.printDebug("Max ratelimit wait exceeded - something's gone wrong, please report it")
                sys.exit(1)
            continue
        
        # Place the request
        return self.session.post(url=url, headers=headers, data=data)
        

    def printDebug(self, msg):
        if self.debug:
            print(msg)
        

    def calculateDynamicTimeRange(self, end_hours = 3, exact = False):
        ''' Calculate a time range to pass into the API
        '''
        
        now = datetime.datetime.now()
        
        hour_begin = now.replace(minute=0)
        if not exact:
            hour_end = hour_begin + datetime.timedelta(hours=end_hours)
        else:
            hour_end = hour_begin.replace(hour=exact['hour'], minute=exact['minute'])
        
        if int(hour_begin.strftime("%H")) > int(hour_end.strftime("%H")):
            # Time wrapped
            hour_end = hour_end.replace(hour=0, minute=0)
        
        # Turn into a textual range
        b = hour_begin.strftime("%H:%M")
        e = hour_end.strftime("%H:%M")
        
        return f"{b}-{e}"
        

    def immediateStart(self, action="charge", hours=3, exact=False):
        ''' Immediately start an action
        '''
               
        timerange = self.calculateDynamicTimeRange(hours, exact)
        self.printDebug(f'Generating a {action} timings payload for {timerange}')
        
        # Get existing schedule and settings
        timings = self.readChargeDischargeSchedule(self.config['inverter'])
        
        if not timings:
            self.printDebug(f'Failed to fetch timings object')
            if not self.config['do_retry']:
                # Retries are disabled
                return False
            
            self.printDebug(f'Will retry after {self.config["retry_delay_s"]}s')
            time.sleep(self.config['retry_delay_s'])
            timings = self.readChargeDischargeSchedule(self.config['inverter'])
            if not timings:
                # Out of luck
                return False

        
        # Set the charge timing for the relevant slot
        slot = f"slot{self.config['dynamic_slot']}"
        
        if action == "charge":
            timings['slots'][slot]['charge'] = timerange;
            timings['slots'][slot]['discharge'] = "00:00-00:00";
        else:
            timings['slots'][slot]['discharge'] = timerange;
            timings['slots'][slot]['charge'] = "00:00-00:00";
        
        # Set the schedule
        res2 = self.setChargeDischargeTimings(self.config['inverter'], timings)
        
        if not res2:
            self.printDebug(f'Failed to set timings')
            if not self.config['do_retry']:
                # Retries are disabled
                return False
            
            self.printDebug(f'Will retry after {self.config["retry_delay_s"]}s')
            time.sleep(self.config['retry_delay_s'])
            if not self.readChargeDischargeSchedule(self.config['inverter']):
                # Out of luck
                return False

        
        return True


    def immediateStop(self):
        ''' Immediately stop charging and discharging
        '''
        # Get existing schedule and settings
        timings = self.readChargeDischargeSchedule(self.config['inverter'])
        
        if not timings:
            self.printDebug(f'Failed to fetch timings object')
            if not self.config['do_retry']:
                # Retries are disabled
                return False
            
            self.printDebug(f'Will retry after {self.config["retry_delay_s"]}s')
            time.sleep(self.config['retry_delay_s'])
            timings = self.readChargeDischargeSchedule(self.config['inverter'])
            if not timings:
                # Out of luck
                return False
           
        # Set the charge timing for the relevant slot
        slot = f"slot{self.config['dynamic_slot']}"
        timings['slots'][slot]['charge'] = "00:00-00:00";
        timings['slots'][slot]['discharge'] = "00:00-00:00";
        
        # Set the schedule
        res2 = self.setChargeDischargeTimings(self.config['inverter'], timings)
        
        if not res2:
            self.printDebug(f'Failed to set timings')
            if not self.config['do_retry']:
                # Retries are disabled
                return False
            
            self.printDebug(f'Will retry after {self.config["retry_delay_s"]}s')
            time.sleep(self.config['retry_delay_s'])
            if not self.readChargeDischargeSchedule(self.config['inverter']):
                # Out of luck
                return False
        
        return True
    
    
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
        
        if not resp or "code" not in resp or resp["code"] != "0":
            return False
        
        
        # Process the response
        timings = {}
        
        '''
        The returned string looks like this
        20,55,00:00-06:00,00:00-00:00,0,0,12:00-16:00,00:00-00:00,0,0,00:00-00:00,00:00-00:00
        
        We need to take the first two values (charge and discharge current, respectively) and
        then iterate through the timeslots
        '''
        slots = resp['data']['msg'].split(',')
        timings['charge_current'] = slots[0]
        timings['discharge_current'] = slots[1]
        
        timings["slots"] = {
            "slot1": { "charge": slots[2], "discharge": slots[3]},
            "slot2": { "charge": slots[6], "discharge": slots[7]},
            "slot3": { "charge": slots[10], "discharge": slots[11]}
            }
        
        timings['raw'] = resp
        
        return timings


    def setChargeDischargeTimings(self, sn, timings):
        ''' Set charge and discharge rate and timings
        
        This expects a dict in the same format as that returned by 
        readChargeDischargeSchedule with the exception that it doesn't
        require the raw attribute (which will be ignored if present)
        '''
        
        if not self.validateTimingsObj(timings):
            # It _probably_ threw an exception so we'll never get here
            return False
        
        # Build the value        
        value_l = [
            str(timings['charge_current']),
            str(timings['discharge_current'])
            ]
        
        for l in timings['slots']:
            if len(value_l) > 2:
                value_l = value_l + ["0","0"]
            
            value_l.append(timings['slots'][l]["charge"])
            value_l.append(timings['slots'][l]["discharge"])
        
        value = ",".join(value_l)
        print(value)
        # Construct the request payload
        req_body_d = {
                "inverterSn": sn,
                "cid" : 103,
                "value" : value
            }
        req_body = json.dumps(req_body_d)
        req_path = "/v2/api/control"
        
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
        
        
        if not resp or "code" not in resp or resp["code"] != "0":
            return False
        
        return resp
        
    def startCharge(self, hours=3, exact=False):
        ''' Start a charge immediately
        
        If not stopped before then, it'll stop in hours **or** at midnight
        whichever comes first
        '''
        
        return self.immediateStart("charge", hours, exact)
        
    def stopCharge(self):
        ''' Stop a charge immediately
        
        '''
        return self.immediateStop()          


    def startDischarge(self, hours=3, exact=False):
        ''' Start a charge immediately
        
        If not stopped before then, it'll stop in hours **or** at midnight
        whichever comes first
        '''
        
        return self.immediateStart("discharge", hours, exact)
        
    def stopDischarge(self):
        ''' Stop a charge immediately
        
        '''
        return self.immediateStop()       
        
    def validateTimingsObj(self, timings):
        ''' Ensure that the timings dict meets the expectations of this class
        
            This doesn't promise to be perfect, but it'd be good not to
            go posting dodgy values into the API
        '''

        if "slots" not in timings:
            raise ValueError(f'timings validation failed: no slots attribute')
            return False

        if "charge_current" not in timings:
            raise ValueError(f'timings validation failed: no charge_current attribute')
            return False
        
        if "discharge_current" not in timings:            
            raise ValueError(f'timings validation failed: no discharge_current attribute')
            return False

        # There must always be 3 slots, whether or not they're all in use
        for slot in ["slot1", "slot2", "slot3"]:
            if slot not in timings["slots"]:
                raise ValueError(f'timings validation failed: slots lacks {slot}')
                return False
            
            # There must be charge and discharge, even if 00:00-00:00
            for t in ["charge", "discharge"]:
                if t not in timings["slots"][slot]:
                    raise ValueError(f'timings validation failed: {slot} lacking {t}')
                    return False
                
                if not re.match("[0-2][0-9]:[0-5][0-9]-[0-2][0-9]:[0-5][0-9]", timings["slots"][slot][t]):
                    raise ValueError(f'timings validation failed: {slot} {t} is not formatted as HH:MM-HH:MM')
                    return False
                    
        return True
            
            
            
            


# Utility functions to help with __main__ runs


def configFromEnv():
    ''' Build a dict of configuration settings based on environment variables
    '''
    return {
        "inverter" : os.getenv("INVERTER_SERIAL", "aaa-bbb-ccc"),
        
        # Which time slot to use when dynamically generating times
        "dynamic_slot" : os.getenv("DYNAMIC_SLOT", "3"),
        
        "api_id" : int(os.getenv("API_ID", 1234)),
        "api_secret" : os.getenv("API_SECRET", "abcde"),
        "api_url" : os.getenv("API_URL", "https://tobeconfirmed").strip('/'),
        # Max number of requests per second
        "api_rate_limit" : int(os.getenv("API_RATE_LIMIT", 2)),
        
        # Should we retry, and if so, what's the delay?
        "do_retry" : os.getenv("RETRIES_ENABLED", "true").lower() == "true",
        "retry_delay_s" : int(os.getenv("RETRY_DELAY", 3)),
        
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
    '''
    if not res:
        print("Request failed")
        sys.exit(1)
    
    # Testing
    # res['slots'][2][0] = "00:00-00:00"
    res['slots']['slot1']['charge'] = "00:00-06:30"
    res['slots']['slot1']['discharge'] = "00:00-00:00"
    res['slots']['slot2']['charge'] = "12:00-16:00"
    res['slots']['slot2']['discharge'] = "00:00-00:00"
    res['slots']['slot3']['charge'] = "00:00-00:00"
    res['slots']['slot3']['discharge'] = "00:00-00:00"
    print(res)
    
    print(soliscloud.validateTimingsObj(res))
    
    
    res2 = soliscloud.setChargeDischargeTimings(config['inverter'], res)
    '''
    
    soliscloud.startCharge()
    soliscloud.stopDischarge()
