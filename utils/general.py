def padded_intstring(number: int, max_length: int = 10) -> str:
    intstring = str(number)
    return (max_length-len(intstring))*'0' + intstring
