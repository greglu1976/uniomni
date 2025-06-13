

def get_summ_table_latex(fsu, isVirtKey=False, isVirtSwitch=False, isStatuses=False, isSysStatuses=False):

    table = []

    # --- Виртуальные кнопки ---
    if isVirtKey:
        head_str = r'''
            \multicolumn{9}{c|}{Виртуальные кнопки} \\
            \hline'''
        table.append(head_str)

        for row in fsu.get_fsu_buttons():
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

    # --- Виртуальные ключи ---
    if isVirtSwitch:
        head_str = r'''
            \multicolumn{9}{c|}{Виртуальные ключи} \\
            \hline'''
        table.append(head_str)

        for row in fsu.get_fsu_switches():
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

    # --- Общие сигналы ---
    if isStatuses:
        head_str = r'''
            \multicolumn{9}{c|}{Общие сигналы функциональной логики} \\
            \hline'''
        table.append(head_str)

        for row in fsu.get_fsu_statuses_sorted():
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

    # --- Системные сигналы ---
    if isSysStatuses:

        head_str = r'''
            \multicolumn{9}{c|}{Системные сигналы} \\
            \hline'''
        table.append(head_str)

        for row in fsu.get_fsu_sys_statuses_sorted():
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

    #print(table)
    return table