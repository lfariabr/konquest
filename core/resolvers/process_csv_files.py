# core/resolvers/process_csv_files.py

import pandas as pd
import logging
from apiCrm.dicts.ddd_dict import ddd_dict
from core.resolvers.create_stores import create_stores
from core.resolvers.create_regions import create_regions
from core.resolvers.clean_phone_number import clean_phone_number

def process_csv_files(botox_file_path=None, preenchimento_file_path=None, instagram_file_path=None):
    df_list = []

    try:
        if botox_file_path:
            try:
                # Open the file to ensure it's properly flushed
                with open(botox_file_path, 'r') as f:
                    df_botox = pd.read_csv(f)
                    if not df_botox.empty:
                        df_botox['filename'] = 'botox'  
                        df_list.append(df_botox)
            except Exception as e:
                logging.error(f"Error reading botox file: {e}")

        if preenchimento_file_path:
            try:
                # Open the file to ensure it's properly flushed
                with open(preenchimento_file_path, 'r') as f:
                    df_preenchimento = pd.read_csv(f)
                    if not df_preenchimento.empty:
                        df_preenchimento['filename'] = 'preenchimento'
                        df_list.append(df_preenchimento)
            except Exception as e:
                logging.error(f"Error reading preenchimento file: {e}")
            
        if instagram_file_path:
            try:
                # Open the file to ensure it's properly flushed
                with open(instagram_file_path, 'r') as f:
                    df_instagram = pd.read_csv(f)
                    if not df_instagram.empty:
                        df_instagram['filename'] = 'instagram'
                        df_list.append(df_instagram)
            except Exception as e:
                logging.error(f"Error reading instagram file: {e}")

        if not df_list:
            return pd.DataFrame()

        df_leads_whatsapp = pd.concat(df_list, ignore_index=True)

        # Ensure required columns exist
        required_columns = ['Nome', 'Whatsapp', 'Tags']
        if not all(col in df_leads_whatsapp.columns for col in required_columns):
            logging.error("Missing required columns in CSV file")
            return pd.DataFrame()

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
        logging.error(f"Error processing CSV files: {e}")
        return pd.DataFrame()