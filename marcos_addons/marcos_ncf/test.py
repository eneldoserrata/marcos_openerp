# -*- encoding: utf-8 -*-
# Just run 'python test_idvalidator.py' to test
from idvalidator import is_ncf

def test():
    ## General tests ##
    ncf = 'A010010010100000001'
    assert is_ncf(ncf)
    ncf = 'P100100100200000010'
    assert is_ncf(ncf)
    ncf = 'A111001000300000100'
    assert is_ncf(ncf)
    ncf = 'P111111110400001000'
    assert is_ncf(ncf)

    # Posicion 1
    # Validar que de todas las letras solo acepte A y P
    upper_letters = 'BCDEFGHIJKLMNOQRSTUVWXYZ'
    lower_letters = 'abcdefghijklmnopqrstuvwxyz'
    ncf_numbers = '010010010100000001'
    for letter in upper_letters:
        ncf = letter + ncf_numbers
        assert not is_ncf(ncf)
    for letter in lower_letters:
        ncf = letter + ncf_numbers
        assert not is_ncf(ncf)

    # Invalidos
    ncf = 'A00001000000001'
    assert not is_ncf(ncf)
    ncf = 'Axx010100000001'
    assert not is_ncf(ncf)
    ncf = 'A0x0010000000001'
    assert not is_ncf(ncf)
    ncf = 'Ax10010000'
    assert not is_ncf(ncf)

    # Posiciones 2-3
    ncf = 'A000010010100000001'
    assert not is_ncf(ncf)
    ncf = 'Axx0010010100000001'
    assert not is_ncf(ncf)
    ncf = 'A0x0010010100000001'
    assert not is_ncf(ncf)
    ncf = 'Ax10010010100000001'
    assert not is_ncf(ncf)

    # Posiciones 4-6
    ncf = 'A010000010100000001'
    assert not is_ncf(ncf)
    ncf = 'A01xxx0010100000001'
    assert not is_ncf(ncf)
    ncf = 'A0100x0010100000001'
    assert not is_ncf(ncf)
    ncf = 'A010x10010100000001'
    assert not is_ncf(ncf)
    ncf = 'A01x010010100000001'
    assert not is_ncf(ncf)

    # Posiciones 7-9
    ncf = 'A010010000100000001'
    assert not is_ncf(ncf)
    ncf = 'A01001xxx0100000001'
    assert not is_ncf(ncf)
    ncf = 'A0100100x0100000001'
    assert not is_ncf(ncf)
    ncf = 'A010010x10100000001'
    assert not is_ncf(ncf)
    ncf = 'A01001x010100000001'
    assert not is_ncf(ncf)

    # Posiciones 10-11
    ncf = 'A010010010100000001'
    assert is_ncf(ncf)
    ncf = 'A010010010200000001'
    assert is_ncf(ncf)
    ncf = 'A010010010300000001'
    assert is_ncf(ncf)
    ncf = 'A010010010400000001'
    assert is_ncf(ncf)
    ncf = 'A010010011100000001'
    assert is_ncf(ncf)
    ncf = 'A010010011200000001'
    assert is_ncf(ncf)
    ncf = 'A010010011300000001'
    assert is_ncf(ncf)
    ncf = 'A010010011400000001'
    assert is_ncf(ncf)
    ncf = 'A010010011500000001'
    assert is_ncf(ncf)
    ncf = 'A010010010000000001'
    assert not is_ncf(ncf)
    ncf = 'A010010010500000001'
    assert not is_ncf(ncf)
    ncf = 'A010010010600000001'
    assert not is_ncf(ncf)
    ncf = 'A010010010700000001'
    assert not is_ncf(ncf)
    ncf = 'A010010010800000001'
    assert not is_ncf(ncf)
    ncf = 'A010010010900000001'
    assert not is_ncf(ncf)
    ncf = 'A010010011000000001'
    assert not is_ncf(ncf)
    ncf = 'A010010011600000001'
    assert not is_ncf(ncf)
    ncf = 'A010010019900000001'
    assert not is_ncf(ncf)

    # Posiciones 12-19
    ncf = 'A010010010100000000'
    assert not is_ncf(ncf)
    ncf = 'A01001001010000000x'
    assert not is_ncf(ncf)
    ncf = 'A0100100101000000x1'
    assert not is_ncf(ncf)
    ncf = 'A010010010100000x01'
    assert not is_ncf(ncf)
    ncf = 'A01001001010000x001'
    assert not is_ncf(ncf)
    ncf = 'A0100100101000x0001'
    assert not is_ncf(ncf)
    ncf = 'A010010010100x00001'
    assert not is_ncf(ncf)
    ncf = 'A01001001010x000001'
    assert not is_ncf(ncf)
    ncf = 'A0100100101x0000001'
    assert not is_ncf(ncf)

if __name__ == '__main__':
    test()
    print 'All tests passed.'
