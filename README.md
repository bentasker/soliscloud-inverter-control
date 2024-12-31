# Soliscloud Inverter Control Script

A simple python class to interace with a Solis inverter via the Soliscloud Control API.

[Issue tracking](https://projects.bentasker.co.uk/gils_projects/project/misc/soliscloud-inverter-control.html).


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
```sh
export API_ID=1233456789
export API_SECRET=blahblahlah
export API_URL=https://www.soliscloud.com:13333
export INVERTER_SERIAL=0987654321
```


---

### Copyright

Copyright (c) 2024 [B Tasker](https://www.bentasker.co.uk)
Released under [BSD 3 clause license](https://www.bentasker.co.uk/pages/licenses/bsd-3-clause.html)
