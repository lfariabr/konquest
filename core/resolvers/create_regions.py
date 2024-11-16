from apiCrm.dicts.region_map import region_map

def create_regions(tag):
    if tag is None or not str(tag).strip():
        return 'São Paulo'
    tag = str(tag).strip()
    return region_map.get(next((region for region in region_map if region in tag), 'CENTRAL'), 'São Paulo')
