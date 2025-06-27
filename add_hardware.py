# Дополнительный класс описания железа, только для того чтобы выдать latex таблицу сигналов для второго устройства в РЭ!!!
# Не совсем правильно, должно быть одно РЭ на одно! устройство
# Здесь создаем дополнительную таблицу
# Надеюсь класс временный и потом будет УДАЛЕН!!!

import pandas as pd
from logger import Logger



class AdditionalHardware():
    def __init__(self, path_to_hardware_desc):
        self.path_to_hardware_desc = path_to_hardware_desc

        self.is_ied2 = False # фиксация наличия второго устройсва в Руководстве по эсплуатации

        self._order_code_parsed = []
        self._slots = []
        self._table_type1 = []
        self._table_type2 = []

        if self.path_to_hardware_desc is None:
            return

        df_info = pd.read_excel(self.path_to_hardware_desc, sheet_name='Инфо')
        info = dict(zip(df_info['Ключ'], df_info['Значение']))

        if 'order_card_ied2' in info:
            Logger.info(f'В системные сигналы будет добавлена информация об втором устройстве {info["order_card_ied2"]}')
            self.is_ied2 = True
            self.order_code_parsed = info['order_card_ied2'].split('-')
        else:
            Logger.warning("Код заказа второго устройства отсутствует")
            self.is_ied2 = False

        if self.is_ied2:
            self._get_slots()
            self._table_type1 = self._get_hardware_signals_for_summ_table_latex(type=1)
            self._table_type2 = self._get_hardware_signals_for_summ_table_latex(type=2)


    def _get_slots(self):
        slot = 1
        plate = 3

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

    def _get_hardware_signals_for_summ_table_latex(self, type=1):
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


    def get_latex_tables_for_add_device(self):
        return self.is_ied2, self._table_type1, self._table_type2