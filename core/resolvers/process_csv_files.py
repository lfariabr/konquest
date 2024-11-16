# core/resolvers/process_csv_files.py

import pandas as pd
from apiCrm.dicts.ddd_dict import ddd_dict
from core.resolvers import create_stores
from core.resolvers import create_regions
from core.resolvers.clean_phone_number import clean_phone_number

def process_csv_files(botox_file_path=None, preenchimento_file_path=None):
    df_list = []

    try:
        if botox_file_path:
            df_botox = pd.read_csv(botox_file_path)
            df_botox['filename'] = 'botox'  
            df_list.append(df_botox)

        if preenchimento_file_path:
            df_preenchimento = pd.read_csv(preenchimento_file_path)
            df_preenchimento['filename'] = 'preenchimento'
            df_list.append(df_preenchimento)

        if not df_list:
            return pd.DataFrame()

        df_leads_whatsapp = pd.concat(df_list, ignore_index=True)

        df_leads_whatsapp['Whatsapp'] = df_leads_whatsapp['Whatsapp'].astype(str)
        df_leads_whatsapp['Whatsapp'] = df_leads_whatsapp['Whatsapp'].apply(clean_phone_number)

        default_tag = "SEM TAGS"
        df_leads_whatsapp['Tags'] = df_leads_whatsapp['Tags'].fillna(default_tag)
        df_leads_whatsapp['Tags'] = df_leads_whatsapp['Tags'].replace('NAN', default_tag)
        df_leads_whatsapp['Tags'] = df_leads_whatsapp['Tags'].str.upper().astype(str)
        
        df_leads_whatsapp['Unidade'] = df_leads_whatsapp['Tags'].apply(create_stores)
        df_leads_whatsapp['Região'] = df_leads_whatsapp['Tags'].apply(create_regions)

        df_leads_whatsapp['DDD'] = df_leads_whatsapp['Whatsapp'].astype(str).str[:2]

        default_region = 'DDD aleatório'
        df_leads_whatsapp['Região_DDD'] = df_leads_whatsapp['DDD'].map(ddd_dict).fillna(default_region)

        default_region = 'São Paulo'
        df_leads_whatsapp['Região'] = df_leads_whatsapp.apply(
            lambda row: row['Região_DDD'] if row['Região'] == default_region or pd.isnull(row['Região']) else row['Região'],
            axis=1
        )

        df_leads_whatsapp.drop(columns=['Região_DDD'], inplace=True)

        return df_leads_whatsapp

    except Exception as e:
        print(f"Error processing CSV files: {str(e)}")
        return None