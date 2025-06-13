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


        self._summ_table_latex = None

    def get_summ_table_latex(self):
        if self._summ_table_latex is None:  # Если таблица ещё не генерировалась
            self._summ_table_latex = self._generate_summ_table_latex()
        return self._summ_table_latex        


    def add_fb(self, fb):
        self.fbs.append(fb)

    def collect_statuses(self):
        self.statuses = [status for fb in self.fbs for status in fb.get_fb_statuses()]
        #print(self.statuses)

    def collect_control(self):
        self.buttons_list = [btn for fb in self.fbs for btn in fb.get_buttons_list()]
        unique_buttons = {item['Полное наименование сигнала']: item 
        for item in self.buttons_list}
        self.buttons_list = list(unique_buttons.values())


        self.switches_list = [sw for fb in self.fbs for sw in fb.get_switches_list()]
        unique_switches = {item['Полное наименование сигнала']: item 
        for item in self.switches_list}
        self.switches_list = list(unique_switches.values())        
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
        return sorted(self.buttons_list, key=lambda x: x['Полное наименование сигнала'])

    def get_fsu_switches(self):
        return sorted(self.switches_list, key=lambda x: x['Полное наименование сигнала'])         


    # Генерация суммарной таблицы в формате LATEX
    def _generate_summ_table_latex(self):
        table = []
            # Добавляем раздел, только если есть данные
        if self.get_fsu_buttons():  # Если список не пуст
            table.append(r'''\multicolumn{9}{c|}{Виртуальные кнопки} \\ \hline''')
            for row in self.get_fsu_buttons():
                str = r'\raggedright '
                str += row['Полное наименование сигнала']
                str += r' & \centering '
                str += row['Наименование сигналов на ФСУ']
                str += r' & \centering'
                str += row['Дискретные входы']
                str += r' & \centering'
                str += row['Выходные реле']
                str += r' & \centering'
                str += row['Светодиоды']
                str += r' & \centering'
                str += row['ФК']
                str += r' & \centering'
                str += row['РС']
                str += r' & \centering'
                str += row['РАС']
                str += r' & \centering \arraybackslash'
                str += row['Пуск РАС']
                str += r' \\'
                str += r'\hline'
                table.append(str)
        if self.get_fsu_switches():
            table.append(r'''\multicolumn{9}{c|}{Виртуальные ключи} \\ \hline''')
            for row in self.get_fsu_switches():
                str = r'\raggedright '
                str += row['Полное наименование сигнала']
                str += r' & \centering '
                str += row['Наименование сигналов на ФСУ']
                str += r' & \centering'
                str += row['Дискретные входы']
                str += r' & \centering'
                str += row['Выходные реле']
                str += r' & \centering'
                str += row['Светодиоды']
                str += r' & \centering'
                str += row['ФК']
                str += r' & \centering'
                str += row['РС']
                str += r' & \centering'
                str += row['РАС']
                str += r' & \centering \arraybackslash'
                str += row['Пуск РАС']
                str += r' \\'
                str += r'\hline'
                table.append(str)
        if self.get_fsu_statuses_sorted():
            table.append(r'''\multicolumn{9}{c|}{Общие сигналы} \\ \hline''')
            for row in self.get_fsu_statuses_sorted():
                str = r'\raggedright '
                str += row['Полное наименование сигнала']
                str += r' & \centering '
                str += row['Наименование сигналов на ФСУ']
                str += r' & \centering'
                str += row['Дискретные входы']
                str += r' & \centering'
                str += row['Выходные реле']
                str += r' & \centering'
                str += row['Светодиоды']
                str += r' & \centering'
                str += row['ФК']
                str += r' & \centering'
                str += row['РС']
                str += r' & \centering'
                str += row['РАС']
                str += r' & \centering \arraybackslash'
                str += row['Пуск РАС']
                str += r' \\'
                str += r'\hline'
                table.append(str)
        if self.get_fsu_sys_statuses_sorted():
            table.append(r'''\multicolumn{9}{c|}{Системные сигналы} \\ \hline''')
            for row in self.get_fsu_sys_statuses_sorted():
                str = r'\raggedright '
                str += row['Полное наименование сигнала']
                str += r' & \centering '
                str += row['Наименование сигналов на ФСУ']
                str += r' & \centering'
                str += row['Дискретные входы']
                str += r' & \centering'
                str += row['Выходные реле']
                str += r' & \centering'
                str += row['Светодиоды']
                str += r' & \centering'
                str += row['ФК']
                str += r' & \centering'
                str += row['РС']
                str += r' & \centering'
                str += row['РАС']
                str += r' & \centering \arraybackslash'
                str += row['Пуск РАС']
                str += r' \\'
                str += r'\hline'
                table.append(str)
        return table 
    
    def get_table_settings_latex(self, func_iec_name, fb_iec_name, header = None):
        for fb in self.fbs:
            if fb.get_fb_iec_name() == fb_iec_name:
                for func in fb.get_functions():
                    if func.get_iec_name() == func_iec_name:

                        return func.get_settings_for_latex(header)

        return 