

def format_time(value):





def format_value(value):
    if isinstance(value, datetime):
        formatted = value.strftime('%Y-%m-%d %H:%M:%S')
    else:
        formatted = f"{value:.2f}" if isinstance(value, float) else str(value)
    return formatted