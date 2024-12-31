


### Read Charge Timings

The docs say we need to request cid `103` from `/v2/api/atRead`

This results in the following output (pretty printed for convenience)
```json
{
  "msg": "success",
  "code": "0",
  "data": {
    "msg": "20,55,00:00-06:00,00:00-00:00,0,0,12:00-16:00,00:00-00:00,0,0,00:00-00:00,00:00-00:00",
    "yuanzhi": "20,55,00:00-06:00,00:00-00:00,0,0,12:00-16:00,00:00-00:00,0,0,00:00-00:00,00:00-00:00",
    "command": "AT+TEST=GIN485:01 03 a8 85 00 1e f4 4b",
    "needLoop": "false"
  },
  "orderId": "1735662097308_195",
  "time": "1735662097308"
}
```

This _differs_ to the value that the docs say we have to post to change values:
```json
[{"name": "Charge current 1", "value": "1", "type": "1", "unit": "A", "min":0, "max":100},{"name": "Discharge current 1", "value": "1", "type": "1", "unit": "A", "min":0," max":100},{"name": "Charge time 1", "name1": "Start time", "name2": "End time", "value": "1", "type": "0"},{"name": "Discharge time 1", "name1": "Start time", "name2": "End time"," value": "1", "type": "0"},{"name": "Charge current 2", "value": "1", "type": "1", "unit": "A", "min":0, "max":100},{"name": "Discharge current 2", "value": "1", "type": "1" , "unit": "A", "min":0, "max":100},{"name": "Charge Time 2", "name1": "Start Time", "name2": "End Time", "value": "1", "type": "0"},{"name": "Discharge Time 2", "name1": "Start Time ", "name2": "End time", "value": "1", "type": "0"},{"name": "Charge current 3", "value": "1", "type": "1", "unit": "A", "min":0, "max":100},{"name": "Discharge current 3"," value": "1", "type": "1", "unit": "A", "min":0, "max":100},{"name": "Charge time 3", "name1": "Start time", "name2": "End time", "value": "1", "type": "0"},{"name". "Discharge Time 3", "name1": "Start Time", "name2": "End Time", "value": "1", "type": "0"}]
```

The break down into individual times and currents is reminscent of the old control interface - earlier in 2024 Solis revised it and current is only defined once now.

The docs spreadsheet also has a sheet called `Demo` with an example that's noted as

> For hybrid inverter, Set the charging current to 50A & discharging current to 20A,
> also set the battery force charge at 2:00-3:00, battery force discharge at 3:00-4:00.

The example payload looks more like the one that I've just retrieved:

```json
{
    "cid":"103",
    "inverterSn":"xxxx",
    "value":"50,20,02:00-03:00,03:00-04:00,0,0,00:00-00:00,00:00-00:00,0,0,00:00-00:00,00:00-00:00",
    "language":"2"
}
```


