from machine import UART
from math import sqrt
import time, struct

class GPSReceive:
    def __init__(self, rx_pin, tx_pin):
        self.gps = UART(2, baudrate=9600, tx=tx_pin, rx=rx_pin)
        
        self.data = {}
        
        self._disable_vtg_sentence()
    
    def _checksum(self, nmea_sentence):
        checksum = 0
        checksum_pos = nmea_sentence.find(b'*')
        nmea_sentence_stripped = nmea_sentence[1:checksum_pos]
            
        for i in nmea_sentence_stripped:
            checksum ^= i
        checksum = ("%02X"%checksum).encode('utf-8')

        if nmea_sentence[checksum_pos+1:checksum_pos+3] == checksum:
            return True
        return False
    
    def _disable_vtg_sentence(self):
        # Uses UBX-CFG-MSG sentence to disable the VTG NMEA sentence
        packet = b'\xb5\x62\x06\x01\x03\x00\xF0\x05\x00\xff\x19'
        # Writing sentence
        self.gps.write(packet)
        
    def _update_data(self):
        num_sentences_read = 0
        
        while num_sentences_read < 5:
            new_data = self.gps.read(1)
            while new_data != b'$':
                new_data = self.gps.read(1)
            
            while not new_data[-1:] == b'\n':
                data_byte = self.gps.read(1)
                if data_byte:
                    new_data += data_byte
            
            if self._checksum(new_data):
                new_data = new_data.decode('utf-8')
                self.data[new_data[3:6]] = new_data
                
            num_sentences_read += 1
    
    def position(self):
        try:
            self._update_data()
        except UnicodeError:
            self._update_data()
            
        try:
            gll_sentence = self.data["GLL"].split(",")
            gsa_sentence = self.data["GSA"].split(",")
        except KeyError:
            return 0, 0, 0, 0
        # potential for there to be no GLL sentence, especially at first run of update_data code
        
        # checking status flag before extracting lat/long/timestamp
        if gll_sentence[6] == "A":
            pos_minutes = gll_sentence[1].find(".")-2
            minutes = float(gll_sentence[1][pos_minutes:])
            degrees = int(gll_sentence[1][:pos_minutes])
            lat = str(degrees+minutes/60) + gll_sentence[2]
            
            pos_minutes = gll_sentence[3].find(".")-2
            minutes = float(gll_sentence[3][pos_minutes:])
            degrees = int(gll_sentence[3][:pos_minutes])
            long = str(degrees+minutes/60) + gll_sentence[4]
            
            time_utc = gll_sentence[5]
            time_stamp = time_utc[:2] + ":" + time_utc[2:4] + ":" + time_utc[4:]
            
            # This is the 2D horizontal position error
            hdop = float(gsa_sentence[-3])
            position_error = hdop * 2.5 # 68% confidence level, 1 sigma - estimated accuracy of GPS module is ~2.5m from datasheet
            
            return lat, long, position_error, time_stamp
        return 0, 0, 0, 0
        
    def velocity(self, data_needs_updating=True):
        if data_needs_updating:
            try:
                self._update_data()
            except UnicodeError:
                self._update_data()
            
        try:
            rmc_sentence = self.data["RMC"].split(",")
        except KeyError:
            return 0, 0, 0, 0
        
        if rmc_sentence[2] == "A":
            time_utc = rmc_sentence[1]
            time_stamp = time_utc[:2] + ":" + time_utc[2:4] + ":" + time_utc[4:]
            sog = rmc_sentence[7] + "Kn"
            
            if rmc_sentence[8]:
                cog = rmc_sentence[8] + "°"
            else:
                cog = "N/A"

            if rmc_sentence[10] or rmc_sentence[11]:
                mag_variation = rmc_sentence[10]+rmc_sentence[11] + "°"
            else:
                mag_variation = "0°"
            
            return sog, cog, mag_variation, time_stamp
        return 0, 0, 0, 0

    def altitude(self, data_needs_updating=True):
        if data_needs_updating:
            try:
                self._update_data()
            except UnicodeError:
                self._update_data()
            
        try:
            gga_sentence = self.data["GGA"].split(",")
            gsa_sentence = self.data["GSA"].split(",")
        except KeyError:
            return 0, 0, 0, 0
        
        if gga_sentence[6] != "0":
            alt = gga_sentence[9] + "M AMSL"
            geo_sep = gga_sentence[11] + "M"
            
            time_utc = gga_sentence[1]
            time_stamp = time_utc[:2] + ":" + time_utc[2:4] + ":" + time_utc[4:]
            
            vdop = float(gsa_sentence[-2])
            
            vertical_error = vdop * 2.5 # 68% confidence level, 1 sigma - estimated accuracy of GPS module is ~2.5m from datasheet
            
            return alt, geo_sep, vertical_error, time_stamp
        
        return 0, 0, 0, 0
    
    def getdata(self):
        lat, long, position_error, timestamp = self.position()
        sog, cog, mag_variation, _ = self.velocity(data_needs_updating=False)
        alt, geo_sep, vertical_error, _ = self.altitude(data_needs_updating=False)
        
        total_error = 2.45 * sqrt(position_error*position_error + vertical_error*vertical_error) # Combining errors into one 3D error. * 2.45 to get to ~95% confidence level (2 sigma)
        
        return lat, long, alt, total_error, sog, cog, mag_variation, geo_sep, timestamp
    
    def _ubx_checksum(self, ubx_packet):
        ck_a = ck_b = 0
        
        for byte in ubx_packet:
            ck_a += byte
            ck_b += ck_a
            
        ck_a &= 0xFF
        ck_b &= 0xFF
        
        return ck_a, ck_b
    
    def setrate(self, rate, measurements_per_nav_solution):
        measurement_time_delta_ms = int(1000/rate)
        # Packing up the key settings that need changing
        measurement_time_delta_ms = struct.pack("<H", measurement_time_delta_ms)
        measurements_per_nav_solution = struct.pack("<H", measurements_per_nav_solution)
        
        packet = b'\x06\x08\x06\x00' + measurement_time_delta_ms + measurements_per_nav_solution + b'\x00\x00'
        # Getting checksums
        ck_a, ck_b = self._ubx_checksum(packet)
        ck_a = struct.pack("<B", ck_a)
        ck_b = struct.pack("<B", ck_b)
        
        packet += ck_a+ck_b
        # Adding header
        packet = b'\xb5\x62' + packet
        
        self.gps.write(packet)

if __name__ == "__main__":
    gps = GPSReceive(10, 9)
    gps.setrate(2, 3)
    while True:
        lat, long, alt, total_error, sog, cog, mag_variation, geo_sep, timestamp = gps.getdata()
        print(lat, long, alt, total_error, sog, cog, mag_variation, geo_sep, timestamp)
