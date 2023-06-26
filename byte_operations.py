def int16_into_two_ints(a16bitvar):
    highbyte = (a16bitvar >> 8) & 0xFF
    lowbyte = a16bitvar & 0xFF
    return highbyte, lowbyte


def two_ints_into16(highbyte, lowbyte):
    a16bitvar = highbyte
    a16bitvar <<= 8
    a16bitvar = a16bitvar | lowbyte
    return a16bitvar