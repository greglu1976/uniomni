
from core.OrderHandler import OrderHandler





order_data = OrderHandler()


sigs, di_sigs = order_data.get_fsu_signals()


for sig in sigs:
    print(sig["appliedDescription"], sig["name"])

for sig in di_sigs:
    print(sig["appliedDescription"], sig["name"])