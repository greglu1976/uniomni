# Класс описывающий содержимое схемы ФСУ устройства
# состоит из объектов FB , которые состоят в свою очередь из объектов function

class FSU:
    def __init__(self):
        self.fbs = []
        self.statuses = []
        self.buttons_list = []
        self.switches_list = []
        self.control_list=[]

    def add_fb(self, fb):
        self.fbs.append(fb)

    def collect_statuses(self):
        self.statuses = [status for fb in self.fbs for status in fb.get_fb_statuses()]
        #print(self.statuses)

    def collect_control(self):
        self.buttons_list = [btn for fb in self.fbs for btn in fb.get_buttons_list()]
        self.switches_list = [sw for fb in self.fbs for sw in fb.get_switches_list()]
        self.control_list = self.buttons_list + self.switches_list
        #print(self.switches_list)

    def get_fbs(self):
        return self.fbs

    def get_fsu_statuses(self):
        return self.statuses

    def get_fsu_control_list(self):
        return self.control_list        