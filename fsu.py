# Класс описывающий содержимое схемы ФСУ устройства
# состоит из объектов FB , которые состоят в свою очередь из объектов function

class FSU:
    def __init__(self):
        self.fbs = []
        self.statuses = []
        self.buttons_list = []
        self.switches_list = []
        self.control_list=[]
        self.inputs_list=[]

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

    def collect_inputs(self):
        self.inputs_list = [inp for fb in self.fbs for inp in fb.get_inputs_list()]
        #print(self.inputs_list)

    def get_fbs(self):
        return self.fbs

    # получаем весь список сигналов несортированный
    def get_fsu_statuses(self):
        return self.statuses
    # получаем весь список сигналов сортированный по алфавиту
    def get_fsu_all_statuses_sorted(self):
        return sorted(self.statuses, key=lambda x: x['Полное наименование сигнала'])
    # получаем весь список сигналов без СИСТ
    def get_fsu_statuses_sorted(self):
        other_list = [d for d in self.statuses if 'СИСТ' not in d['Полное наименование сигнала']]
        return sorted(other_list, key=lambda x: x['Полное наименование сигнала'])
    # получаем список сигналов только СИСТ
    def get_fsu_sys_statuses_sorted(self):
        sist_list = [d for d in self.statuses if 'СИСТ' in d['Полное наименование сигнала']]
        return sorted(sist_list, key=lambda x: x['Полное наименование сигнала'])


    def get_fsu_control_list(self):
        return self.control_list        

    def get_fsu_inputs_list(self):
        return self.inputs_list

    def get_fsu_buttons(self):
        return self.buttons_list

    def get_fsu_switches(self):
        return self.switches_list        