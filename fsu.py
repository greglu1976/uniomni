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

        self.order_code_parsed = [] # устанавливается сеттером
        self._slots = [] # хранит описание слотов устройства для таблицы системных сигналов устройства (платы ввода вывода и тд)
        self._fsu_signals_latex = []
        self._fsu_system_signals_latex = []

        self._table_for_latex_type = 1
        self._summ_table_latex = None

        self._tables_of_add_device = tuple() # возвращаемые таблицы второго устройства от объекта класса AdditionalHardware     

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
        #return sorted(other_list, key=lambda x: x['Полное наименование сигнала']) # ВКЛЮЧИТЬ СОРТИРОВКУ
        return other_list
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
        #return sorted(self.switches_list, key=lambda x: x['Полное наименование сигнала'])         
        return self.switches_list 

    # Генерация суммарной таблицы в формате LATEX
    def _generate_summ_table_latex(self):
        def _generate_row(row):
            row_str = '\\raggedright '
            row_str += row['Полное наименование сигнала'].replace('_', r'\_')
            row_str += ' & \\centering '
            row_str += row['Наименование сигналов на ФСУ'].replace('_', r'\_')
            row_str += ' & \\centering '
            row_str += row['Дискретные входы'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['Выходные реле'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['Светодиоды'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['ФК'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['РС'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['РАС'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering \\arraybackslash '
            row_str += row['Пуск РАС'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' \\\\ \\hline\n'
            return row_str

        def _generate_section(data, title=''):
            section = []
            if data:
                #section.append(f'\\multicolumn{{9}}{{c|}}{{{title}}} \\\\\n\\hline\n')
                if title:
                    section.append(f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{title}}}}} \\\\\n\\hline\n')
                for row in data:
                    section.append(_generate_row(row))
            return section

        table = []
        table.extend(_generate_section(self.get_fsu_buttons(), "Виртуальные кнопки"))
        table.extend(_generate_section(self.get_fsu_switches(), "Виртуальные ключи"))

        if self._table_for_latex_type == 1:
            table.extend(_generate_section(self.get_fsu_statuses_sorted(), "Общие сигналы функциональной логики")) # Суммарная таблица сигналов ТИП 1

            if self._tables_of_add_device[0]:
                table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Системные сигналы устройства I архитектуры"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            else:
                table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Системные сигналы устройства"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2

            table.extend(self.get_hardware_signals_for_summ_table_latex(type=1))
            if self._tables_of_add_device[0]:
                table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Системные сигналы устройства II архитектуры"}}}}} \\\\\n\\hline\n'))
                table.extend(self._tables_of_add_device[1])

            #table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Общие системные сигналы"}}}}} \\\\\n\\hline\n'))
            #table.extend(_generate_section(self.get_fsu_sys_statuses_sorted())) # для таблицы 1 типа отдельно системные сигналы
        else:
            table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Общие сигналы функциональной логики"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            table.extend(self.get_formatted_signals_for_latex()) # Суммарная таблица сигналов по функциям ТИП 2
            if self._tables_of_add_device[0]:
                table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Системные сигналы (СИСТ) устройства I архитектуры"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            else:
                table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Системные сигналы (СИСТ) устройства"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            table.extend('\\rowcolor{gray!15} \n')
            table.extend((f'\\multicolumn{{9}}{{c|}}{{{"Диагностические сигналы (Диагностика)"}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            table.extend(self.get_hardware_signals_for_summ_table_latex(type=2)) # Сборка сигналов, зависящих от исполнения устройства (по платам)

            if self._tables_of_add_device[0]:
                table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Системные сигналы (СИСТ) устройства II архитектуры"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
                table.extend('\\rowcolor{gray!15} \n')
                table.extend((f'\\multicolumn{{9}}{{c|}}{{{"Диагностические сигналы (Диагностика)"}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
                table.extend(self._tables_of_add_device[2])

            #table.extend((f'\\multicolumn{{9}}{{c|}}{{\\textbf{{{"Общие системные сигналы (СИСТ)"}}}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            #table.extend('\\rowcolor{gray!15} \n')
            #table.extend((f'\\multicolumn{{9}}{{c|}}{{{"Диагностические сигналы (Диагностика)"}}} \\\\\n\\hline\n')) # Суммарная таблица сигналов ТИП 2
            #table.extend(self.get_system_formatted_signals_for_latex()[3:]) # Суммарная таблица системных сигналов из ФБ СИСТ ТИП 2
        
        return table

    # Генерация таблицы в формате LATEX для подраздела РЭ с выбором функции   
    def get_table_settings_latex(self, func_iec_name, fb_iec_name, header = None):
        for fb in self.fbs:
            if fb.get_fb_iec_name() == fb_iec_name:
                for func in fb.get_functions():
                    if func.get_iec_name() == func_iec_name:

                        return func.get_settings_for_latex(header)

        return 

    # Генерация таблицы сигналов разбитой по функциям (тип 2) LATEX
    def _is_signals_for_latex(self):
        for fb in self.fbs:
            if fb.get_formatted_signals_for_latex():
                return True
        return False

    def _create_system_formatted_signals_for_latex(self,fb):
        self._fsu_system_signals_latex.extend(fb.get_formatted_signals_for_latex())

    def _create_formatted_signals_for_latex(self):
        if not self._is_signals_for_latex():
            return
        for fb in self.fbs:
            if 'СИСТ' in fb.get_fb_name():
                self._create_system_formatted_signals_for_latex(fb)
                continue
            self._fsu_signals_latex.extend(fb.get_formatted_signals_for_latex())

    def get_system_formatted_signals_for_latex(self):
        return self._fsu_system_signals_latex

    def get_formatted_signals_for_latex(self):
        if not self._fsu_signals_latex:
            self._create_formatted_signals_for_latex()
        #print(self._fsu_signals_latex)
        return self._fsu_signals_latex

    def set_table_for_latex_type(self, type):
        self._table_for_latex_type = type

    def set_order_code_parsed(self, order_code):
        self.order_code_parsed = order_code

    def _get_slots(self):
        slot = 1
        plate = 3
        #print(self.order_code_parsed)

        while True:
            current_plate = self.order_code_parsed[plate]
            if current_plate == 'x' or current_plate == 'х':
                slot+=1
                plate+=1
                continue
            if current_plate in ['P02c', 'Р02с']:
                self._slots.append({'num': slot, 'purpose': 'supply'})
                slot+=1
                plate+=1 
                continue
            if current_plate in [ 'P02', 'Р02']:
                self._slots.append({'num': slot, 'purpose': 'supply'})
                slot+=1
                plate+=1                
                continue            
            if 'B' in current_plate or 'В' in current_plate:
                self._slots.append({'num': slot, 'purpose': 'inputs'})
                slot+=1
                plate+=1                
                continue                
            if 'K' in current_plate or 'К' in current_plate:
                self._slots.append({'num': slot, 'purpose': 'outputs'})
                slot+=1
                plate+=1                
                continue
            if 'M' in current_plate or 'М' in current_plate:
                self._slots.append({'num': slot, 'purpose': 'analogs'})
                slot+=1
                plate+=1                
                continue
            if 'C' in current_plate or 'С' in current_plate:
                self._slots.append({'num': slot, 'purpose': 'cpu'})
                break

    def get_hardware_signals_for_summ_table_latex(self, type=1):
        # часть вторая - генерируем из словаря latex разметку
        if not self._slots:
            self._get_slots()
        prefix = 'СИСТ / Диагностика: ' if type ==1 else ''   
        latex_slots = []
        for slot in self._slots:
            if slot['purpose'] == 'supply':
                latex_slots.append(f'\\raggedright  {prefix}Неисправность 12 В & \centering Слот М'+ str(slot['num']) +' Неиспр.12В & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                latex_slots.append(f'\\raggedright  {prefix}Неисправность внешнего питания & \centering Слот М'+ str(slot['num']) +' Нет внеш.питания & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                latex_slots.append(f'\\raggedright  {prefix}Критическая ошибка & \centering Слот М'+ str(slot['num']) +' Неисп.внеш.питания & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                continue
            if slot['purpose'] == 'inputs' or slot['purpose'] == 'outputs':
                latex_slots.append(f'\\raggedright  {prefix}Отказ модуля & \centering Слот М'+ str(slot['num']) +' Отказ модуля & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                latex_slots.append(f'\\raggedright  {prefix}Критическая ошибка & \centering Слот М'+ str(slot['num']) +' Модуль не определен & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                continue
            if slot['purpose'] == 'analogs':
                latex_slots.append(f'\\raggedright  {prefix}Отказ модуля & \centering Слот М'+ str(slot['num']) +' Отказ модуля & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                latex_slots.append(f'\\raggedright  {prefix}Критическая ошибка & \centering Слот М'+ str(slot['num']) +' Модуль не определен & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')
                latex_slots.append(f'\\raggedright  {prefix}Неисправность АЦП & \centering Слот М'+ str(slot['num']) +' Неисправность АЦП & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering -- & \centering \\arraybackslash -- \\\\ \hline \n')               
            if slot['purpose'] == 'cpu':
                pass
        return latex_slots                                        