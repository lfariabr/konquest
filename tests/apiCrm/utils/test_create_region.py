import unittest
from apiCrm.utils.create_region import create_region
from apiCrm.dicts.dict_region_ident import dic_region_ident

class TestCreateRegion(unittest.TestCase):
    def test_empty_tag_returns_sao_paulo(self):
        """Test that empty or None tag returns São Paulo"""
        self.assertEqual(create_region(None), 'São Paulo')
        self.assertEqual(create_region(''), 'São Paulo')
        
    def test_case_insensitive_matching(self):
        """Test that region matching is case insensitive"""
        # Test with a known store-region pair
        self.assertEqual(create_region('londrina'), 'Londrina')
        self.assertEqual(create_region('LONDRINA'), 'Londrina')
        
    def test_partial_tag_matching(self):
        """Test that region is found in partial tag matches"""
        test_tag = "CAMPAIGN_LONDRINA_2023"
        self.assertEqual(create_region(test_tag), 'Londrina')
        
    def test_no_match_returns_sao_paulo(self):
        """Test that non-matching tag returns São Paulo"""
        self.assertEqual(create_region('NONEXISTENT_STORE'), 'São Paulo')
        
    def test_all_stores_map_to_regions(self):
        """Test that all stores map to their regions"""
        store_region_map = {
            'LONDRINA': 'Londrina',
            'RIO DE JANEIRO': 'Rio de Janeiro',
            'SAO PAULO': 'São Paulo',
            'SOROCABA': 'Sorocaba',
            'SANTOS': 'Santos',
            'CAMPINAS': 'Campinas',
            'BELO HORIZONTE': 'Belo Horizonte'
        }
        for store, expected_region in store_region_map.items():
            self.assertEqual(create_region(store), expected_region)

if __name__ == '__main__':
    unittest.main()