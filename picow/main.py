import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import radioRDA5807
import swf
import ssd1306

from machine import Pin, I2C
import time

class radioRDA5807b(radioRDA5807.RadioRDA5807):
    def __init__(self, i2c):
        super().__init__(i2c)
    def get_status(self):
        conf = self.read_reg(radioRDA5807.RDA5807M_REG_CONFIG)
        mute = 'mute' if (conf & radioRDA5807.RDA5807M_REG_CONFIG_FLG_DMUTE) == 0 else 'unmute'
        bass = 'bass' if (conf & radioRDA5807.RDA5807M_REG_CONFIG_FLG_BASS) != 0 else 'nobass'
        out_mono = 'out_mono' if (conf & radioRDA5807.RDA5807M_REG_CONFIG_FLG_MONO) != 0 else 'out_stereo'
        data = self.read_reg(radioRDA5807.RDA5807M_REG_STATUS)
        frequency = self.start_frequency_MHz + ((data & radioRDA5807.RDA5807M_REG_STATUS_MASK_READCHAN) * self.frequency_spacing_MHz)
        stereo = 'stereo' if (data & radioRDA5807.RDA5807M_REG_STATUS_FLG_ST) != 0 else 'mono'
        rssi = self.read_reg(radioRDA5807.RDA5807M_REG_RSSI) >> 9
        volume = self.get_volume()
        return frequency, stereo, rssi, volume, mute, bass, out_mono

stations = [
    [76.4,"RADIO BERRY"],
    [79.5,"NACK5"],
    [78.0,"bayfm"],
    [80.0,"TOKYO FM"],
    [80.3,"NHK FM UTUNOMIYA"],
    [80.7,"NHK FM CHIBA"],
    [81.3,"J-WAVE"],
    [81.6,"NHK FM GUNMA"],
    [81.9,"NHK FM KANAGAWA"],
    [82.5,"NHK FM TOKYO"],
    [83.0,"FM-Fuji"],
    [83.2,"NHK FM IBARAKI"],
    [84.7,"Fm yokohama"],
    [85.1,"NHK FM SAITAMA"],
    [85.6,"NHK FM YAMANASHI"],
    [86.3,"FM GUNMA"],
    [89.7,"Inter FM"],
    [90.5,"TBS RADIO"],
    [90.9,"YAMANASHI HOUSOU"],
    [91.6,"BUNKA HOUSOU"],
    [92.4,"R-F-RADIO NIPPON"],
    [93.0,"NIPPON HOUSOU"],
    [94.1,"TOCHIGI HOUSOU"],
    [94.6,"LuckyFM IBARAKI"]
]

ble = bluetooth.BLE()
p = BLESimplePeripheral(ble)

led = machine.Pin("LED", machine.Pin.OUT)

# setup the I2C communication
i2c = I2C(0, sda=Pin(4), scl=Pin(5))

# Set up the OLED display (128x64 pixels) on the I2C bus
# SSD1306_I2C is a subclass of FrameBuffer. FrameBuffer provides support for graphics primitives.
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Clear the display by filling it with black
oled.fill(0)
oled.show()

# initialize RDA5807
radio = radioRDA5807b(i2c)

# RDA5807 check
if not radio.address_found:
    while 1:
        oled.fill(0)
        oled.text("Check the power", 0, 0)
        oled.text("switch.", 0, 16)
        oled.show()

radio.set_volume(3)             # volume(0 - 15)
radio.mono(True)                # force mono
out_mono = True
radio.bass_boost(True)          # enable bass boost

station = 0
radio.set_frequency_MHz(stations[station][0])
name = stations[station][1]
fout = radio.get_frequency_MHz()
print(fout, name)

vm = radio.get_volume()
print(vm)

volume_up = swf.swf(21)         # button volume up      --> GP21
volume_down = swf.swf(20)       # button volume down    --> GP20
seek_station = swf.swf(19)      # button seek station   --> GP19
select_station = swf.swf(18)    # button select station --> GP18 

update_disp = True
last_rssi = 0

def get_station_name(frequency):
    name = "------"
    station = -1
    for i in range(len(stations)):
        if frequency == stations[i][0]:
            name = stations[i][1]
            station = i
            break
    return name, station

def on_rx(data):
    global vm, update_disp, fout, name, station
    cmd = data.decode('utf-8').replace('\n','')
    print(cmd)
    args = cmd.split(' ')

    if len(args) == 3:
        if args[0] == 'read':
            if args[1] == 'reg':
                p.send('read reg ' + args[2])
                data = radio.read_reg(int(args[2]))
                p.send('reg ' + args[2] + ' ' + '{:04X}'.format(data))
    elif len(args) == 4:
        if args[0] == 'write':
            if args[1] == 'reg':
                p.send('write reg ' + args[2] + ' ' + args[3])
                radio.write_reg(int(args[2]), int(args[3]))
                data = radio.read_reg(int(args[2]))
                p.send('reg ' + args[2] + ' ' + '{:04X}'.format(data))
    elif len(args) == 5:
        if args[0] == 'update':
            if args[1] == 'reg':
                p.send('update reg ' + args[2] + ' ' + args[3] + ' ' + args[4])
                radio.update_reg(int(args[2]), int(args[3]), int(args[4]))
                data = radio.read_reg(int(args[2]))
                p.send('reg ' + args[2] + ' ' + '{:04X}'.format(data))                                   
    elif len(args) == 2:
        if args[0] == 'frequency':
            radio.set_frequency_MHz(float(args[1]))
            name = '-----'
            fout = radio.get_frequency_MHz()
            p.send('frequency ' + '{:.01f}'.format(fout))
            name, station = get_station_name(fout)
        elif args[0] == 'seek':
            if args[1] == 'up':
                radio.seek_up()
            elif args[1] == 'down':
                radio.seek_down()
            fout = radio.get_frequency_MHz()
            p.send('frequency ' + '{:.01f}'.format(fout))
            name, station = get_station_name(fout)
        elif args[0] == 'mute':
            if args[1] == 'on':
                radio.mute(True)
            elif args[1] == 'off':
                radio.mute(False)
        elif args[0] == 'mono':
            if args[1] == 'on':
                radio.mono(True)
            elif args[1] == 'off':
                radio.mono(False)
        elif args[0] == 'bass':
            if args[1] == 'on':
                radio.bass_boost(True)
            elif args[1] == 'off':
                radio.bass_boost(False)
        elif args[0] == 'volume':
            vm = radio.get_volume()
            if args[1] == 'up':
                if vm < 15:
                    vm += 1
                    radio.set_volume(vm)
            elif args[1] == 'down':
                if vm > 0:
                    vm -= 1
                    radio.set_volume(vm)
            else:
                vm = int(args[1])
                radio.set_volume(vm)
            update_disp = True
            p.send('volume ' + str(vm))
    elif len(args) == 1:
        if args[0] == 'status':
            frequency, stereo, rssi, volume, mute, bass, out_mono = radio.get_status()
            p.send('status ' + '{:.01f}'.format(frequency) + ' ' + stereo + ' ' + str(rssi) + ' ' + str(volume) + ' ' + mute + ' ' + bass+ ' ' + out_mono)
    else:
            p.send('?')
                   
p.on_write(on_rx)

while True:

    if volume_up.is_on_edge():
        if vm < 15:
            vm += 1
            radio.set_volume(vm)
            vm = radio.get_volume()
            print(vm)
            update_disp = True

    if volume_down.is_on_edge():
        if vm > 0:
            vm -= 1
            radio.set_volume(vm)
            vm = radio.get_volume()
            print(vm)
            update_disp = True

    if seek_station.is_on_edge():
        oled.fill(0)
        oled.text("-- seek up --", 0, 0)
        oled.show()
        radio.seek_up()
        fout = radio.get_frequency_MHz()
        name, station = get_station_name(fout)
        print(fout, name)
        update_disp = True
        
    if select_station.is_on_edge():
        station += 1
        if station >= len(stations):
            station = 0
        radio.set_frequency_MHz(stations[station][0])
        name = stations[station][1]
        fout = radio.get_frequency_MHz()
        print(fout, name)
        update_disp = True

    rssi = radio.get_signal_strength()
    if rssi != last_rssi:
        last_rssi = rssi
        update_disp = True
    
    if update_disp:
        oled.fill(0)
        oled.text('RSSI:' + str(rssi), 0, 0)
        oled.text(str(fout) + 'MHz Vol:' + str(vm), 0, 16)
        oled.text(name, 0, 32)
        oled.show()
        frequency, stereo, rssi, volume, mute, bass, out_mono = radio.get_status()
        p.send('status ' + '{:.01f}'.format(frequency) + ' ' + stereo + ' ' + str(rssi) + ' ' + str(volume) + ' ' + mute + ' ' + bass + ' ' + out_mono)
        update_disp = False

    if p.is_connected():
        led.on()
    else:
        led.off()

    time.sleep(0.1)