from apiCrm.dicts.stores import stores

def create_stores(tag):
    return next((store for store in stores if store in tag), 'CENTRAL')
