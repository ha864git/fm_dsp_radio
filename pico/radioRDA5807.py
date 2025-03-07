#
# Python module to interface with RDA5807 FM radio device using I2C bus
#
# Copyright (c) ha864 2025
#
# License: MIT
#
# Modified using the following OSS specifically for Japan.
# https://github.com/dawsonjon/101Things/tree/master/19_fm_radio/
# Copyright (c) Jonathan P Dawson 2024
# filename: rda5807.py
# description:
#
# Python module to interface with RDA5807 FM radio device using I2C bus
#
# License: MIT
#

SEQUENTIAL_ACCESS_ADDRESS = 0x10
RANDOM_ACCESS_ADDRESS     = 0x11

RDA5807M_REG_CHIPID = 0x00
RDA5807M_REG_CHIPID_MASK_ID = 0xff00         # Chip ID. BITS[15:8]
RDA5807M_REG_CHIPID_DATA_ID = 0x5800         # RDA5807=0x58

RDA5807M_REG_CONFIG = 0x02
RDA5807M_REG_CONFIG_FLG_DHIZ = 0x8000        # 1 Audio Output High-Z Disable. 1= Normal operation
RDA5807M_REG_CONFIG_FLG_DMUTE = 0x4000       # 1 Mute Disable. 1 = Normal operation
RDA5807M_REG_CONFIG_FLG_MONO = 0x2000        # Mono Select. 0 = Stereo; 1 = Force mono
RDA5807M_REG_CONFIG_FLG_BASS = 0x1000        # Bass Boost. 0 = Disabled; 1 = Bass boost enabled
RDA5807M_REG_CONFIG_FLG_RCLKNOCAL = 0x0800   # 0 default
RDA5807M_REG_CONFIG_FLG_RCLKDIRECT = 0x0400  # 0 default
RDA5807M_REG_CONFIG_FLG_SEEKUP = 0x0200      # Seek Up. 0 = Seek down; 1 = Seek up
RDA5807M_REG_CONFIG_FLG_SEEK = 0x0100        # Seek 0 = Disable stop seek; 1 = Enable
RDA5807M_REG_CONFIG_FLG_SKMODE = 0x0080      # Seek Mode 0 = wrap at band limit and continue seeking
RDA5807M_REG_CONFIG_FLG_RDS = 0x0008         # 0 default RDS/RBDS not used 
RDA5807M_REG_CONFIG_FLG_NEW = 0x0004         # New Demodulate Method Enable
RDA5807M_REG_CONFIG_FLG_RESET = 0x0002       # Soft Reset 1 = reset
RDA5807M_REG_CONFIG_FLG_ENABLE = 0x0001      # 1 Power Up Enable. 0 = Disabled; 1 = Enabled

RDA5807M_REG_TUNING = 0x03
RDA5807M_REG_TUNING_FLG_DIRECT = 0x0020      # 0 Directly Control Mode, Only used when test.
RDA5807M_REG_TUNING_FLG_TUNE = 0x0010        # Tune 1 = Enable
RDA5807M_REG_TUNING_BAND_WIDE = 0x0008       # BITS[3:2] BAND[1:0] 10=76–108 MHz (world wide)
RDA5807M_REG_TUNING_SPACE_100K = 0x0000      # BITS[1:0] SPACE[1:0] Channel Spacing. 00=100 kHz

RDA5807M_REG_GPIO   = 0x04
RDA5807M_REG_GPIO_FLG_DE = 0x0800            # De-emphasis. 0=75µs(USA); 1=50µs(Japan/EU) 
RDA5807M_REG_GPIO_FLG_SOFTMUTE_EN = 0x0200   # 1(default)=softmute enable
RDA5807M_REG_GPIO_FLG_AFCD = 0x0100          # 0(default)=AFC work 


RDA5807M_REG_VOLUME = 0x05
RDA5807M_REG_VOLUME_FLG_INTMODE = 0x8000     # for RDS mode  default:1
RDA5807M_REG_VOLUME_MASK_SEEKTH = 0x0f00     # Seek SNR threshold value BITS[11:8]
RDA5807M_REG_VOLUME_DATA_SEEKTH = 0x0800     # Seek SNR threshold value default:1000
RDA5807M_REG_VOLUME_MASK_VOLUME = 0x000f     # DAC Gain Control Bits (Volume). BITS[3:0]
RDA5807M_REG_VOLUME_DATA_VOLUME = 0x000f     # DAC Gain Control Bits (Volume). default:1111

RDA5807M_REG_I2S    = 0x06
RDA5807M_REG_I2S_DATA_DEFAULT   = 0x0000     # i2s default

RDA5807M_REG_BLEND  = 0x07
RDA5807M_REG_BLEND_MASK_TH_SOFRBLEND = 0x7c00 # BITS[14:10] Threshold for noise soft blend setting, unit 2dB
RDA5807M_REG_BLEND_DATA_TH_SOFRBLEND = 0x4000 # default 10000
RDA5807M_REG_BLEND_FLG_SOFTBLEND_EN = 0x0002  # default 1 If 1, Softblend enable 

RDA5807M_REG_STATUS = 0x0A
RDA5807M_REG_STATUS_FLG_STC = 0x4000         # Seek/Tune Complete. 1 = Complete
RDA5807M_REG_STATUS_FLG_SF = 0x2000          # Seek Fail. 1 = Seek failure
RDA5807M_REG_STATUS_FLG_ST = 0x0400          # Stereo Indicator 0 = Mono; 1 = Stereo
RDA5807M_REG_STATUS_MASK_READCHAN = 0x03ff   # Read Channel. BITS[9:0]

RDA5807M_REG_RSSI = 0x0B
RDA5807M_REG_RSSI_MASK_RSSI = 0xfe00         # RSSI（Received Signal Strength Indicator）0-127
RDA5807M_REG_RSSI_FLG_FMTRUE = 0x0100        # 1=the current channel is a station
RDA5807M_REG_RSSI_FLG_FMREADY = 0x0080       # 1=ready, 0=not ready

class RadioRDA5807:

    """ Access RDA5807M Device """
    
    def __init__(self, i2c):

        """ Configure RDA5807M Device

        arguments:
        i2c                     - an I2C bus object

        """

        self.i2c = i2c
        self.mute_flag = False
        self.bass_boost_flag = False
        self.mono_flag = False

        #read i2c address and check
        self.address_found = False
        address = self.i2c.scan()
        for i in address:
            if i == RANDOM_ACCESS_ADDRESS:
                self.address_found = True
        if not self.address_found:
            return

        #read chip ID and check
        data = self.read_reg(RDA5807M_REG_CHIPID)
        if(data & RDA5807M_REG_CHIPID_MASK_ID == RDA5807M_REG_CHIPID_DATA_ID):
            print("Radio RDA5807 Found!")
            
        config = RDA5807M_REG_CONFIG_FLG_DHIZ | RDA5807M_REG_CONFIG_FLG_DMUTE | RDA5807M_REG_CONFIG_FLG_ENABLE
        self.write_reg(RDA5807M_REG_CONFIG, config | RDA5807M_REG_CONFIG_FLG_RESET)
        self.start_frequency_MHz = 76.0
        self.frequency_spacing_MHz = 0.1
        self.write_reg(RDA5807M_REG_TUNING, 0x0000 | RDA5807M_REG_TUNING_BAND_WIDE | RDA5807M_REG_TUNING_SPACE_100K)
        self.write_reg(RDA5807M_REG_GPIO, RDA5807M_REG_GPIO_FLG_DE | RDA5807M_REG_GPIO_FLG_SOFTMUTE_EN)
        self.write_reg(RDA5807M_REG_VOLUME, RDA5807M_REG_VOLUME_FLG_INTMODE | RDA5807M_REG_VOLUME_DATA_SEEKTH | RDA5807M_REG_VOLUME_DATA_VOLUME)
        self.write_reg(RDA5807M_REG_I2S, RDA5807M_REG_I2S_DATA_DEFAULT)
        self.write_reg(RDA5807M_REG_BLEND, RDA5807M_REG_BLEND_DATA_TH_SOFRBLEND | RDA5807M_REG_BLEND_FLG_SOFTBLEND_EN)
        config |= RDA5807M_REG_CONFIG_FLG_NEW
        self.write_reg(RDA5807M_REG_CONFIG, config)

    def set_frequency_MHz(self, frequency_MHz):

        """ Set tuned frequency in MHz """

        frequency_in = frequency_MHz
        while True:
            frequency_steps = int((frequency_in - self.start_frequency_MHz)/self.frequency_spacing_MHz)
            data = ((frequency_steps << 6) | RDA5807M_REG_TUNING_FLG_TUNE | RDA5807M_REG_TUNING_BAND_WIDE | RDA5807M_REG_TUNING_SPACE_100K)
            self.write_reg(RDA5807M_REG_TUNING, data)
            while True:
                data = self.read_reg(RDA5807M_REG_TUNING)
                if not data & RDA5807M_REG_TUNING_FLG_TUNE:
                    break
            frequency_out = self.start_frequency_MHz + ((self.read_reg(RDA5807M_REG_STATUS) & RDA5807M_REG_STATUS_MASK_READCHAN) * self.frequency_spacing_MHz)
            if frequency_out == frequency_MHz:
                break
            frequency_in = frequency_in + (frequency_in - frequency_out) / 2
            
    def get_frequency_MHz(self):

        """ Get tuned frequency in MHz """

        frequency = self.start_frequency_MHz + ((self.read_reg(RDA5807M_REG_STATUS) & RDA5807M_REG_STATUS_MASK_READCHAN) * self.frequency_spacing_MHz)
        return frequency


    def set_volume(self, volume):

        """ Set volume 0 to 15 """

        volume &= 0xf
        self.update_reg(RDA5807M_REG_VOLUME, 0xf, volume) #bits 3:0
        
    def get_volume(self):

        """ Get Volume 0 to 15 """

        return self.read_reg(RDA5807M_REG_VOLUME) & 0xf #bits 3:0
   
    def mute(self, mute):

        """ Mute True = mute False = Normal """

        if not mute:
          self.update_reg(RDA5807M_REG_CONFIG, RDA5807M_REG_CONFIG_FLG_DMUTE, RDA5807M_REG_CONFIG_FLG_DMUTE)
        else:
          self.update_reg(RDA5807M_REG_CONFIG, RDA5807M_REG_CONFIG_FLG_DMUTE, 0)
        self.mute_flag = mute
        
    def bass_boost(self, bass_boost):

        """ Bass Boost True = enable bass boost False = disable bass boost """

        if bass_boost:
          self.update_reg(RDA5807M_REG_CONFIG, RDA5807M_REG_CONFIG_FLG_BASS, RDA5807M_REG_CONFIG_FLG_BASS)
        else:
          self.update_reg(RDA5807M_REG_CONFIG, RDA5807M_REG_CONFIG_FLG_BASS, 0)
        self.bass_boost_flag = bass_boost
        
    def mono(self, mono):

        """ Force Mono True = force mono False = stereo """

        if mono:
          self.update_reg(RDA5807M_REG_CONFIG, RDA5807M_REG_CONFIG_FLG_MONO, RDA5807M_REG_CONFIG_FLG_MONO)
        else:
          self.update_reg(RDA5807M_REG_CONFIG, RDA5807M_REG_CONFIG_FLG_MONO, 0)
        self.mono_flag = mono

    def seek_up(self):

        """ Find next station (blocks until tuning completes) """

        self.update_reg(RDA5807M_REG_CONFIG,
            (RDA5807M_REG_CONFIG_FLG_SEEKUP | RDA5807M_REG_CONFIG_FLG_SEEK), 
            (RDA5807M_REG_CONFIG_FLG_SEEKUP | RDA5807M_REG_CONFIG_FLG_SEEK))
        while 1:
            data = self.read_reg(RDA5807M_REG_STATUS)
            if data & RDA5807M_REG_STATUS_FLG_STC:
                break
        
    def seek_down(self):

        """ Find previous station (blocks until tuning completes) """

        self.update_reg(RDA5807M_REG_CONFIG,
            (RDA5807M_REG_CONFIG_FLG_SEEKUP | RDA5807M_REG_CONFIG_FLG_SEEK),
            RDA5807M_REG_CONFIG_FLG_SEEK)
        while 1:
            data = self.read_reg(RDA5807M_REG_STATUS)
            if data & RDA5807M_REG_STATUS_FLG_STC:
                break

    def get_signal_strength(self):

        """ Recieved Signal Strength Indicator 0 = low, 127 = high (logarithmic)"""

        rssi = self.read_reg(RDA5807M_REG_RSSI) >> 9
        return rssi

    def update_reg(self, reg, mask, value):

        """ Update specific bits in I2C register """

        data = self.read_reg(reg)
        data = (data & ~mask) | value
        self.write_reg(reg, data)

    def read_reg(self, reg):

        """ Read data from i2c register """

        self.i2c.writeto(RANDOM_ACCESS_ADDRESS, bytes([reg]))
        data = self.i2c.readfrom(RANDOM_ACCESS_ADDRESS, 2)
        return (data[0] << 8) | data[1]

    def write_reg(self, reg, data):

        """ Write data to i2c register """

        data = bytes([reg, data >> 8, data&0xff])
        self.i2c.writeto(RANDOM_ACCESS_ADDRESS, data)