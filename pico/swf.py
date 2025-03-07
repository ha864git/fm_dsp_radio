#
#  switch chattering filter
#
import machine
class swf(object):
    def __init__(self, port=21, activate_value=0, delay_times=3):
        self.sw = machine.Pin(port, machine.Pin.IN, machine.Pin.PULL_UP) 
        self.last_value = self.sw.value()
        self.delay_count = 0
        self.delay_times = delay_times
        self.activate_value = activate_value

    def is_on_edge(self):
        if self.last_value != self.sw.value():
            self.delay_count += 1
            if self.delay_count >= self.delay_times:
                self.last_value = 1 if self.last_value == 0 else 0
                if self.last_value == self.activate_value:
                    return True
        else:
            self.delay_count = 0
        return False