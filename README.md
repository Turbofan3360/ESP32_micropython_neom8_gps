# ESP32 Micropython NEO-M8 GPS DRIVER #

### THE CODE: ###

This code reads data off of a UART pin on the ESP32. The Neo-M8 modules outputs NMEA sentences, which this code then converts into the useful data needed. Note that all outputs are as strings.

Note: There is an occasional bug with the decoding that I can’t figure out (it only says UnicodeError: ). I will come back to this driver code in future and hopefully solve it!
There is also additional functionality I will add to this module at some point in the future.

### EXAMPLE USAGE: ###

```python3
import gps_reading_data.py as gps

module = gps.GPSReceive(10, 9)

latitude, longitude, timestamp = module.position()
sog, cog, magnetic_variation, timestamp = module.velocity()
altitude, geoid_separation, timestamp = module.altitude()

latitude, longitude, sog, cog, magnetic_variation, altitude, geoid_separation, timestamp = module.get_data()

```

For the initialization - the parameters the driver expects is the TX pin number, followed by the RX pin number.

### NMEA SENTENCE TYPES: ###

GSV: positions of satellites in view
GLL: lat,NS,lon,EW,time,status,posMode
GSA: error in satellite positions

RMC: time, status, lat, NS, lon, EW, spd, cog, date, mv, mvEW, posMode, navStatus

mv = magnetic variation, cog = course over ground, spd = speed

VTG: cogt, cogtUnit, cogm, cogmUnit, sogn, sognUnit, sogk, sogkUnit, posMode

cogt/m = course over gound true/magnetic, first sign is in knots and second in km/h

GGA: time, lat, NS,l on, EW, quality, numSV, HDOP, alt, altUnit, sep, sepUnit, diffAge, diffStation

numsv = num satellites, HDOP = measurement of error in height, altUnit/sepUnit always meters, sep = geoid separation, diffAge/diffStation used with differential GPS

Lat/Lon: first two digits before decimal point and everything after is minutes, other digits beforehand are degrees

Status flags: V - no fix/GNSS fix but user limits exceeded/dead reckoning fix but user limits exceeded
A - Dead reckoning fix, RTK float, RTK fixed, 2D GNSS fix, 3D GNSS fix, Combined GNSS/dead reckoning fix

posMode flags (GLL/VTG): N - no fix/GNSS fix but user limits exceeded
E - dead reckoning fix/dead reckoning fix but user limits exceeded
A/D (A = autonomous, D = differential GPS) - 2D/3D GNSS fix/combined GNSS and dead reckoning fix

quality flags (GGA): 0 - no pos fix/GNSS fix but user limits exceeded
5 - RTK float, 4 - RTK fixed
1/2 (1 = autonomous GNSS, 2 = differential GNSS) - 2D/3D GNSS fix/combined GNSS and dead reckoning fix

### REFERENCES: ###
 - <https://content.u-blox.com/sites/default/files/NEO-M8-FW3_DataSheet_UBX-15031086.pdf>
 - <https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf>
