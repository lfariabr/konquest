from apiCrm.dicts.stores import stores

def create_stores(tag):
    if tag is None or not str(tag).strip():
        return 'CENTRAL'
    tag = str(tag).strip()
    return next((store for store in stores if store in tag), 'CENTRAL')
