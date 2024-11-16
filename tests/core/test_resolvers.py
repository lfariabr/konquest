import pytest
from core.resolvers.clean_phone_number import clean_phone_number
from core.resolvers.create_regions import create_regions
from core.resolvers.create_stores import create_stores
from core.resolvers.process_csv_files import process_csv_files
import pandas as pd
import tempfile
import os

def test_clean_phone_number():
    # Test various phone number formats
    assert clean_phone_number('5511999999999') == '11999999999'
    assert clean_phone_number('11999999999') == '11999999999'
    assert clean_phone_number('(11) 99999-9999') == '11999999999'
    assert clean_phone_number('11 99999.9999') == '11999999999'
    assert clean_phone_number('999999999') == '999999999'
    assert clean_phone_number('') == ''
    assert clean_phone_number(None) == ''

def test_create_regions():
    # Test region creation from tags
    assert create_regions('CAMPINAS') == 'Campinas'
    assert create_regions('SANTOS') == 'Santos'
    assert create_regions('TATUAPÉ') == 'São Paulo'
    assert create_regions('RANDOM TAG') == 'São Paulo'
    assert create_regions('') == 'São Paulo'
    assert create_regions(None) == 'São Paulo'

def test_create_stores():
    # Test store creation from tags
    assert create_stores('CAMPINAS') == 'CAMPINAS'
    assert create_stores('SANTOS') == 'SANTOS'
    assert create_stores('TATUAPÉ') == 'TATUAPÉ'
    assert create_stores('RANDOM TAG') == 'CENTRAL'
    assert create_stores('') == 'CENTRAL'
    assert create_stores(None) == 'CENTRAL'

def test_process_csv_files():
    # Create temporary CSV files for testing
    botox_data = pd.DataFrame({
        'Nome': ['Test User 1', 'Test User 2'],
        'Whatsapp': ['5511999999999', '5511888888888'],
        'Tags': ['CAMPINAS', 'TATUAPÉ']
    })
    
    preench_data = pd.DataFrame({
        'Nome': ['Test User 3', 'Test User 4'],
        'Whatsapp': ['5511777777777', '5511666666666'],
        'Tags': ['SANTOS', '']
    })
    
    # Create temporary files
    botox_path = tempfile.mktemp(suffix='.csv')
    preench_path = tempfile.mktemp(suffix='.csv')
    
    try:
        # Save DataFrames to CSV files
        botox_data.to_csv(botox_path, index=False)
        preench_data.to_csv(preench_path, index=False)
        
        # Test processing single file
        df_botox = process_csv_files(botox_file_path=botox_path)
        assert len(df_botox) == 2
        assert df_botox.iloc[0]['Whatsapp'] == '11999999999'
        assert df_botox.iloc[0]['Unidade'] == 'CAMPINAS'
        assert df_botox.iloc[0]['Região'] == 'Campinas'
        assert df_botox.iloc[1]['Unidade'] == 'TATUAPÉ'
        assert df_botox.iloc[1]['Região'] == 'São Paulo'
        
        # Test processing both files
        df_both = process_csv_files(botox_file_path=botox_path, preenchimento_file_path=preench_path)
        assert len(df_both) == 4
        assert df_both.iloc[2]['Whatsapp'] == '11777777777'
        assert df_both.iloc[2]['Unidade'] == 'SANTOS'
        assert df_both.iloc[2]['Região'] == 'Santos'
        assert df_both.iloc[3]['Unidade'] == 'CENTRAL'
        assert df_both.iloc[3]['Região'] == 'São Paulo'
    
    finally:
        # Clean up temporary files
        if os.path.exists(botox_path):
            os.unlink(botox_path)
        if os.path.exists(preench_path):
            os.unlink(preench_path)
