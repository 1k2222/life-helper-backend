def get_ordinal_suffix(number):
    if not isinstance(number, int):
        return str(number) # 如果不是整数，则直接返回原样字符串

    if 11 <= number <= 13:
        # 特殊情况：11th, 12th, 13th
        return str(number) + "th"
    else:
        last_digit = number % 10
        if last_digit == 1:
            return str(number) + "st"
        elif last_digit == 2:
            return str(number) + "nd"
        elif last_digit == 3:
            return str(number) + "rd"
        else:
            return str(number) + "th"