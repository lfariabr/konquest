from core.resolvers.create_regions import create_regions

def test_create_regions():
    # Test region creation from tags
    assert create_regions('CAMPINAS') == 'Campinas'
    assert create_regions('SANTOS') == 'Santos'
    assert create_regions('TATUAPÉ') == 'São Paulo'
    assert create_regions('RANDOM TAG') == 'São Paulo'
    assert create_regions('') == 'São Paulo'
    assert create_regions(None) == 'São Paulo'