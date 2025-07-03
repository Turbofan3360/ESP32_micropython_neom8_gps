from machine import UART

class StreamDecodingError(Exception):
    pass

class GPSReceive:
    def __init__(self, tx_pin, rx_pin):
        self.gps = UART(2, baudrate=9600, tx=tx_pin, rx=rx_pin)
        
        self.data = {}
        self.NUM_NMEA_SENTENCES = 6
        
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
        
    def _update_data(self):
        num_sentences_read = 0
        
        while num_sentences_read < self.NUM_NMEA_SENTENCES:
            new_data = self.gps.read(1)
            while new_data != b'$':
                new_data = self.gps.read(1)
            
            while not b'\n' in new_data:
                data_byte = self.gps.read(1)
                if data_byte:
                    new_data += data_byte
            
            if self._checksum(new_data):
                try:
                    new_data = new_data.decode('utf-8')
                except UnicodeError:
                    raise StreamDecodingError
                
                self.data[new_data[3:6]] = new_data
            num_sentences_read += 1
    
    def position(self):
        try:
            self._update_data()
        except StreamDecodingError:
            self._update_data()
            
        try:
            gll_sentence = self.data["GLL"].split(",")
        except KeyError:
            return None
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
            
            return lat, long, time_stamp
        return None
        
    def velocity(self):
        try:
            self._update_data()
        except StreamDecodingError:
            self._update_data()
            
        try:
            rmc_sentence = self.data["RMC"].split(",")
        except KeyError:
            return None
        
        if rmc_sentence[2] == "A":
            time_utc = rmc_sentence[1]
            time_stamp = time_utc[:2] + ":" + time_utc[2:4] + ":" + time_utc[4:]
            
            sog = rmc_sentence[7] + "Kn"
            cog = rmc_sentence[8] + "°"
            mag_variation = rmc_sentence[10]+rmc_sentence[11]
            
            return sog, cog, mag_variation, time_stamp
        return None

    def altitude(self):
        try:
            self._update_data()
        except StreamDecodingError:
            self._update_data()
            
        try:
            gga_sentence = self.data["GGA"].split(",")
        except KeyError:
            return None
        
        if gga_sentence[6] != "0":
            alt = gga_sentence[9] + "M AMSL"
            geo_sep = gga_sentence[11] + "M"
            
            time_utc = gga_sentence[1]
            time_stamp = time_utc[:2] + ":" + time_utc[2:4] + ":" + time_utc[4:]
            
            return alt, geo_sep, time_stamp
        return None
    
    def get_data(self):
        try:
            self._update_data()
        except StreamDecodingError:
            self._update_data()
        
        try:
            gga_sentence = self.data["GGA"].split(",")
            rmc_sentence = self.data["RMC"].split(",")
        except KeyError:
            return None
        
        if gga_sentence[6] != 0 and rmc_sentence[2] == "A":
            alt = gga_sentence[9] + "M AMSL"
            geo_sep = gga_sentence[11] + "M"
            time_utc = gga_sentence[1]
            time_stamp = time_utc[:2] + ":" + time_utc[2:4] + ":" + time_utc[4:]
            
            sog = rmc_sentence[7] + "Kn"
            
            cog = rmc_sentence[8] + " Degrees"
            mag_variation = rmc_sentence[10]+rmc_sentence[11]
            
            pos_minutes = gga_sentence[2].find(".")-2
            minutes = float(gga_sentence[2][pos_minutes:])
            degrees = int(gga_sentence[2][:pos_minutes])
            lat = str(degrees+minutes/60) + gga_sentence[3]
            
            pos_minutes = gga_sentence[4].find(".")-2
            minutes = float(gga_sentence[4][pos_minutes:])
            degrees = int(gga_sentence[4][:pos_minutes])
            long = str(degrees+minutes/60) + gga_sentence[5]
            
            return lat, long, sog, cog, mag_variation, alt, geo_sep, time_stamp
        return None

if __name__ == "__main__":
    gps = GPSReceive(10, 9)
    while True:
        formatted_data = gps.get_data()
        if formatted_data:
            print(formatted_data)
