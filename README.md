# Soliscloud Inverter Control Script

A simple python class to interace with a Solis inverter via the [Soliscloud Control API](https://oss.soliscloud.com/doc/SolisCloud%20Device%20Control%20API%20V2.0.pdf).

[Issue tracking](https://projects.bentasker.co.uk/gils_projects/project/misc/soliscloud-inverter-control.html).

---

## Warning: Use At Your Own Risk

As the license text makes clear, this code is provided "as is", with no warranty and no claim for fitness to purpose:

> THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

It bears repeating, because this script calls the Soliscloud Control API in order to write values into your inverter's registers.

Although the script does some validation (and the API hopefully does), it _may_ be possible to write incorrect values which could damage your inverter (or even burn down your house).

Use of this software is entirely at your own risk and the author accepts no liability for the results of that use.


---

### Config

The script takes configuration via environment variable:

Mandatory:

* `API_ID`: Your soliscloud API key ID
* `API_SECRET`: The secret for your API key
* `INVERTER_SERIAL`: The serial number of your inverter (you can get this from the Soliscloud interface)

Optional:

* `DYNAMIC_SLOT`: Which timing slot to use. Valid values are 1,2 or 3 (default `3`)
* `RETRIES_ENABLED`: Should the script retry (once) if Soliscloud returns a failure (default `true`)
* `RETRY_DELAY`: Delay in seconds before retrying (default `3`)
* `DEBUG`: When `true`, prints additional information to stdout

---

## Inverter Time Slots

Solis inverters have 6 timing slots within their registers, 3 each for charge and discharge.

The Soliscloud web interface won't allow you to configure overlapping/conflicting timeranges across slots. Their API, however, offers no such protection and it's not clear whether the inverter will hande this safely.


To be safe, before using this script you should remove any timeslots that you have configured (by setting them all to 00:00).

The script itself only uses a single timeslot.

---

## Control Server

This repo also contains a Dockerfile for an example control server, allowing HTTP API calls to be made in order to trigger functions without the client having to implement Solis's authentication mechanism.

The server uses HTTP Basic Authentication [by default](https://projects.bentasker.co.uk/gils_projects/issue/misc/soliscloud-inverter-control/3.html), so you should set a password in environment variable `PASS` (if you don't, it'll generate a random password for you):

```sh
docker run \
-d \
--restart=always \
--name soliscloudcontrol \
-e API_ID=$SOLIS_API_KEY_ID \
-e API_SECRET=$SOLIS_API_KEY_SECRET \
-e INVERTER_SERIAL=$INVERTER_SERIAL_NUMBER \
-e DO_AUTH=true \
-e USER=solisuser \
-e PASS=$LOCAL_API_PASS \
-p 8081:8080 \
ghcr.io/bentasker/soliscloud-inverter-control:0.1
```

Or if you prefer docker compose

```sh
version: '3'

services:
  soliscloudcontrol:
    image: ghcr.io/bentasker/soliscloud-inverter-control:0.1
    container_name: soliscloudcontrol
    restart: always
    environment:
      - API_ID=${SOLIS_API_KEY_ID}
      - API_SECRET=${SOLIS_API_KEY_SECRET}
      - INVERTER_SERIAL=${INVERTER_SERIAL_NUMBER}
      - DO_AUTH=true
      - USER=solisuser
      - PASS=${LOCAL_API_PASS}
    ports:
      - 8081:8080
```

---

## API

The API only has a few endpoints, allowing charging and discharging to be started and stopped.



### Endpoints

#### `POST /api/v1/setCurrent`

Set the charge and/or (forced) discharge current.

Expects a JSON payload with `charge_current` and/or `discharge_current` attributes. 

See below for details on the JSON payload.


#### `POST /api/v1/startCharge`


Switch to charge mode immediately.

Optionally accepts a JSON request body, see below.

If no JSON request body is present, or it lacks an `end` attribute, the end time will be set 3 hours in the future.


#### `POST /api/v1/startDischarge`

Start a forced discharge immediately.

Optionally accepts a JSON request body, see below.

If no JSON request body is present, or it lacks an `end` attribute, the end time will be set 3 hours in the future.


#### `POST /api/v1/stopCharge`

Stop the charge and or discharge. Works by zeroing out the schedule that the script interacts with.

Optionally accepts a JSON request body, allowing charge rates to be set whilst stopping current charge.


#### `POST /api/v1/stopDischarge`

Stop the charge and or discharge. Works by zeroing out the schedule that the script interacts with.

Optionally accepts a JSON request body, allowing charge rates to be set whilst stopping current charge.


---

### JSON payload

The control server endpoints accept an optional JSON request body:

```json
{
  "end": "2025-01-02 14:30:00+0000",
  "charge_current": 30,
  "discharge_current": 55
}
```

Each of the attributes is optional

* `end`: when to configure the inverter to end the charge/discharge period. The inverter uses a simple clock, so if this is beyond midnight it'll be converted to midnight. Only conumed by the `start*` endpoints
* `charge_current`: current to use when charging. Consumed by `start*`, `stop*` and `setCurrent` endpoints
* `discharge_current`: current to use when force discharging



---

## Copyright

Copyright (c) 2025 [B Tasker](https://www.bentasker.co.uk)
Released under [BSD 3 clause license](https://www.bentasker.co.uk/pages/licenses/bsd-3-clause.html)
