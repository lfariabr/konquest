from apiCrm.dicts.dict_region_ident import dic_region_ident

def create_region(tag):
    """
    Determine region based on tag.
    Returns 'São Paulo' if no match is found.
    """
    if not tag:
        return 'São Paulo'
        
    # Store to region mapping
    store_region_map = {
        'LONDRINA': 'Londrina',
        'RIO DE JANEIRO': 'Rio de Janeiro',
        'SAO PAULO': 'São Paulo',
        'SOROCABA': 'Sorocaba',
        'SANTOS': 'Santos',
        'CAMPINAS': 'Campinas',
        'BELO HORIZONTE': 'Belo Horizonte'
    }
    
    tag = tag.upper()
    for store, region in store_region_map.items():
        if store in tag:
            return region
            
    return 'São Paulo'