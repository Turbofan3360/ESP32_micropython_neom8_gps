# ESP32 Micropython NEO-M8 GPS


After receiving my GPS modules, I first did some research on their communication protocols and how to read/send data. The main datasheet for this module (https://content.u-blox.com/sites/default/files/NEO-M8-FW3_DataSheet_UBX-15031086.pdf) didn’t have a lot of info on this, but I found another receiver description and protocol specification sheet which had all the detail I wanted (https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf). I then started writing code to read data off the ESP32 UART. I had many iterations of this code, trying to get it to be as fast and efficient as possible. Eventually, I ended up with the code in /NEO-M8-GPS/reading_gps_data.py

Currently, this code simply reads data off the UART (only a set number of NMEA sentences, 6 in this case, as that is the number sent by the NEO-M8), ensures it has all the data before decoding it and adding it to a dictionary. There is an occasional bug with the decoding that I can’t figure out (it only says UnicodeError: ), which is why that section of code is in a try/except. My next task is to implement code to process the NMEA sentences to get the data needed in the required formats.

It was easy enough to code the string manipulation in order to pull out the data from each NMEA sentence. However, I was getting KeyErrors from my dictionary, UnicodeErrors and errors with the checksum (I wrote a method to check the checksum). As a result, it was quite variable in the time it would take to get fix data and it occasionally missed the first couple of bytes of data, among a couple of errors. As a result, I then rewrote my code such that it always reads 1 byte at a time, and starts appending the bytes to a variable once it finds the “$” sign at the start of the NMEA sentence, and then reads until the new line character “\n”. This turns out to be a far more consistent and reliable method for reading data, so much more effective method! This also turns up far fewer errors - although I’ve left in all the error catching code to ensure reliability.


**NMEA SENTENCE TYPES:**

GSV: positions of satellites in view
GLL: lat,NS,lon,EW,time,status,posMode
GSA: error in satellite positions

RMC: time,status,lat,NS,lon,EW,spd,cog,date,mv,mvEW,posMode,navStatus

mv = magnetic variation, cog = course over ground, spd = speed

VTG: cogt,cogtUnit,cogm,cogmUnit,sogn,sognUnit,sogk,sogkUnit,posMode

cogt/m = course over gound true/magnetic, first sign is in knots and second in km/h

GGA: time,lat,NS,lon,EW,quality,numSV,HDOP,alt,altUnit,sep,sepUnit,diffAge,diffStation

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
