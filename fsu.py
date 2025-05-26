# Класс описывающий содержимое схемы ФСУ устройства
# состоит из объектов FB , которые состоят в свою очередь из объектов function

class FSU:
    def __init__(self):
        self.fbs = []
        self.statuses = []

    def add_fb(self, fb):
        self.fbs.append(fb)


    def collect_statuses(self):
        self.statuses = [status for fb in self.fbs for status in fb.get_fb_statuses()]
        print(self.statuses)


    def get_fbs(self):
        return self.fbs

    def get_fsu_statuses(self):
        return self.statuses