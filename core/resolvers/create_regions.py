from apiCrm.dicts.region_map import region_map

def create_regions(tag):
    return region_map.get(next((region for region in region_map if region in tag), 'CENTRAL'), 'São Paulo')
