
from core.OrderHandler import OrderHandler

import json

order_data = OrderHandler()

# Для раздела ФК и СД
sigs, di_sigs = order_data.get_fsu_signals()

for sig in sigs:
    pass
    #print(sig["appliedDescription"], sig["name"])

for sig in di_sigs:
    pass
    #print(sig["appliedDescription"], sig["name"])

#sigs = order_data.get_fsu_out_signals()
#print(sigs)

sigs = order_data.get_data_for_registration()
#print(sigs)

for sig in sigs:
    if sig["Name"] == "Сигналы функциональной логики":
        print(sig)

with open('data.json', 'w', encoding='utf-8') as file:
    json.dump(sigs, file, ensure_ascii=False, indent=4)