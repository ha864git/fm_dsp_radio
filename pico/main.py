import radioRDA5807
import swf
import ssd1306

from machine import Pin, I2C
import time

stations = [
    [76.4,"RADIO BERRY"],
    [77.1,"HOUSOU DAIGAKU"],
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
radio = radioRDA5807.RadioRDA5807(i2c)

# RDA5807 check
if not radio.address_found:
    while 1:
        oled.fill(0)
        oled.text("Check the power", 0, 0)
        oled.text("switch.", 0, 16)
        oled.show()

radio.set_volume(3)             # volume(0 - 15)
radio.mono(True)                # force mono
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
        name = ""
        station = -1
        for i in range(len(stations)):
            if fout == stations[i][0]:
                name = stations[i][1]
                station = i
                break
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
        update_disp = False

    time.sleep(0.1)