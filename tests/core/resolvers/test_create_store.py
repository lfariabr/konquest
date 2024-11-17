from core.resolvers.create_stores import create_stores

def test_create_stores():
    # Test store creation from tags
    assert create_stores('CAMPINAS') == 'CAMPINAS'
    assert create_stores('SANTOS') == 'SANTOS'
    assert create_stores('TATUAPÉ') == 'TATUAPÉ'
    assert create_stores('RANDOM TAG') == 'CENTRAL'
    assert create_stores('') == 'CENTRAL'
    assert create_stores(None) == 'CENTRAL'