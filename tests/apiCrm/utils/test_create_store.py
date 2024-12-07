import unittest
from apiCrm.utils.create_store import create_store
from apiCrm.dicts.dict_store_ident import dic_store_ident

class TestCreateStore(unittest.TestCase):
    def test_empty_tag_returns_central(self):
        """Test that empty or None tag returns CENTRAL"""
        self.assertEqual(create_store(None), 'CENTRAL')
        self.assertEqual(create_store(''), 'CENTRAL')
        
    def test_case_insensitive_matching(self):
        """Test that store matching is case insensitive"""
        # Get first store from dictionary for testing
        test_store = next(iter(dic_store_ident.keys()))
        self.assertEqual(create_store(test_store.lower()), test_store)
        self.assertEqual(create_store(test_store.upper()), test_store)
        
    def test_partial_tag_matching(self):
        """Test that store is found in partial tag matches"""
        test_store = next(iter(dic_store_ident.keys()))
        test_tag = f"CAMPAIGN_{test_store}_2023"
        self.assertEqual(create_store(test_tag), test_store)
        
    def test_no_match_returns_central(self):
        """Test that non-matching tag returns CENTRAL"""
        self.assertEqual(create_store('NONEXISTENT_STORE'), 'CENTRAL')
        
    def test_all_stores_are_matchable(self):
        """Test that all stores in dictionary can be matched"""
        for store in dic_store_ident.keys():
            self.assertEqual(create_store(store), store)

if __name__ == '__main__':
    unittest.main()