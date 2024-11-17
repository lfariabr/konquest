import os
import pytest
import tempfile
import pandas as pd
from core.resolvers.process_csv_files import process_csv_files

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
