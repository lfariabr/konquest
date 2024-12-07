# List of valid stores
from apiCrm.dicts.dict_store_ident import dic_store_ident

def create_store(tag):
    """
    Determine store based on tag.
    Returns 'CENTRAL' if no match is found.
    """
    if not tag:
        return 'CENTRAL'
        
    tag = tag.upper()
    for store in dic_store_ident.keys():
        if store in tag:
            return store
    return 'CENTRAL'
