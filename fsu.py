# Класс описывающий содержимое схемы ФСУ устройства
# состоит из объектов FB , которые состоят в свою очередь из объектов function

class FSU:
    def __init__(self):
        self.fbs = []


    def add_fb(self, fb):
        self.fbs.append(fb)


    def get_fbs(self):
        return self.fbs