from decimal import Decimal


def convert_price(num_price) -> str:
    num_price = Decimal(str(num_price))
    if num_price % 1 == 0:
        return str(int(num_price))
    return f"{num_price:.2f}"
