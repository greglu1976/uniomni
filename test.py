
from core.OrderHandler import OrderHandler



order_data = OrderHandler()

# Для раздела ФК и СД
sigs, di_sigs = order_data.get_fsu_signals()

for sig in sigs:
    pass
    #print(sig["appliedDescription"], sig["name"])

for sig in di_sigs:
    pass
    #print(sig["appliedDescription"], sig["name"])

sigs = order_data.get_fsu_out_signals()
print(sigs)