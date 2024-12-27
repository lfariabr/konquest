import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models.contact import Contact
from core.models.user import kUser
from core.resolvers.clean_phone_number import clean_phone_number

def process_excel_file(file_path):
    """Process Excel file and return cleaned DataFrame"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Get phone numbers from column D
        if df.shape[1] >= 4:  # Ensure we have at least 4 columns
            phone_column = df.iloc[:, 3]  # Column D (0-based index 3)
            name_column = df.iloc[:, 0]  # Column A
            
            # Create clean DataFrame
            clean_df = pd.DataFrame({
                'name': name_column,
                'phone': phone_column.astype(str).apply(clean_phone_number)
            })
            
            # Remove rows with empty phones
            clean_df = clean_df[clean_df['phone'].notna() & (clean_df['phone'] != '')]
            
            return clean_df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error reading excel file: {e}")
        return pd.DataFrame()

class Command(BaseCommand):
    help = 'Import contacts from Excel files'

    def add_arguments(self, parser):
        parser.add_argument('--botox', type=str, help='Path to botox.xlsx')
        parser.add_argument('--preenchimento', type=str, help='Path to preenchimento.xlsx')
        parser.add_argument('--user', type=str, help='Email of user to assign contacts to')

    def handle(self, *args, **options):
        try:
            user = kUser.objects.get(email=options['user'])
        except kUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {options["user"]} not found'))
            return

        files_to_process = [
            (options['botox'], 'Botox'),
            (options['preenchimento'], 'Preenchimento')
        ]

        for file_path, relationship_tag in files_to_process:
            if not file_path:
                continue

            self.stdout.write(f'Processing {file_path}...')
            try:
                df = process_excel_file(file_path)
                if df.empty:
                    self.stdout.write(self.style.WARNING(f'No valid data found in {file_path}'))
                    continue

                for _, row in df.iterrows():
                    try:
                        contact, created = Contact.objects.get_or_create(
                            phone=row['phone'],
                            relationship_tag=relationship_tag,
                            defaults={
                                'name': row['name'] if pd.notna(row['name']) else '',
                                'user': user,
                                'source': 'Excel Import',
                                'created_at': timezone.datetime(2024, 12, 26, tzinfo=timezone.get_current_timezone())  # Set to Dec 26
                            }
                        )

                        if created:
                            self.stdout.write(f'Created contact: {contact.name or "No name"} ({contact.phone})')
                        else:
                            self.stdout.write(f'Contact already exists: {contact.name or "No name"} ({contact.phone})')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Error processing row: {row.to_dict()}. Error: {str(e)}'))
                        continue

                self.stdout.write(self.style.SUCCESS(f'Successfully processed {file_path}'))
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing file {file_path}: {str(e)}'))

"""
python manage.py import_contacts --botox core/management/botox.xlsx --preenchimento core/management/preenchimento.xlsx --user your.email@example.com
"""