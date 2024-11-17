from core.resolvers.clean_phone_number import clean_phone_number

def test_clean_phone_number():
    # Test various phone number formats
    assert clean_phone_number('5511999999999') == '11999999999'
    assert clean_phone_number('11999999999') == '11999999999'
    assert clean_phone_number('(11) 99999-9999') == '11999999999'
    assert clean_phone_number('11 99999.9999') == '11999999999'
    assert clean_phone_number('999999999') == '999999999'
    assert clean_phone_number('') == ''
    assert clean_phone_number(None) == ''