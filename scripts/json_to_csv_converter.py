import csv
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_data_row(line):
    """Check if the line contains actual data by looking for tab-separated fields."""
    if not line or '\t' not in line:
        return False
    fields = [f.strip() for f in line.split('\t') if f.strip()]
    # Check for minimum fields and proper format
    if len(fields) < 8:  # We expect at least 8 fields for a valid data row
        return False
    # First field should be numeric (ID)
    try:
        int(fields[0].strip())  # ID should be numeric
        return True
    except (ValueError, IndexError):
        return False

def clean_field(field):
    """Clean individual field values."""
    if isinstance(field, str):
        return field.strip().strip('"').strip()
    return str(field)

def extract_url(line):
    """Extract URL from different formats in the file."""
    match = re.search(r'https://procorpo-[^.]+\.indiquemultiplique\.com\.br/painel/sharings', line)
    return match.group(0) if match else None

def process_data_section(lines, current_url, seen_rows, data_rows):
    """Process a section of data lines."""
    for line in lines:
        line = line.strip()
        if not line or not is_data_row(line):
            continue

        fields = line.split('\t')
        # Ensure we have all fields
        while len(fields) < 14:
            fields.append('')
            
        fields = [clean_field(f) for f in fields]
        
        # Create a unique key for this row using ID and URL
        # This ensures we don't mix up IDs from different locations
        row_key = f"{current_url}_{fields[0]}"
        
        # Only add if we haven't seen this combination before
        if row_key not in seen_rows:
            seen_rows.add(row_key)
            data_rows.append([current_url] + fields)
            if len(data_rows) % 100 == 0:
                logger.info(f"Processed {len(data_rows)} rows...")

def convert_to_csv():
    try:
        # Read the file as text
        logger.info("Reading file...")
        with open('dados.json', 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Define CSV headers
        headers = [
            'URL', 'ID', 'Nome', 'Email', 'Telefone', 'Consultor', 'Mensagem', 
            'Rede Social', 'Compartilhamentos', 'Conversoes', 
            'Data Criacao', 'Data Atualizacao', 'Status', 'Observacao', 'Convidados'
        ]
        
        # Prepare CSV file
        output_filename = f'dados_convertidos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        logger.info(f"Creating CSV file: {output_filename}")
        
        # Process data
        data_rows = []
        seen_rows = set()  # Track unique rows by URL + ID
        current_url = None
        current_section = []
        
        # Process each line
        for line in lines:
            # Check for URL
            url = extract_url(line)
            if url:
                # Process previous section if exists
                if current_url and current_section:
                    process_data_section(current_section, current_url, seen_rows, data_rows)
                    current_section = []
                current_url = url
                continue
            
            # Add line to current section
            if current_url:
                current_section.append(line)
        
        # Process the last section
        if current_url and current_section:
            process_data_section(current_section, current_url, seen_rows, data_rows)
        
        # Write to CSV
        with open(output_filename, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(data_rows)
                    
        # Get unique URLs
        unique_urls = {row[0] for row in data_rows}
        
        logger.info(f"Conversion completed successfully!")
        logger.info(f"Found {len(unique_urls)} unique URLs")
        logger.info(f"Processed {len(data_rows)} unique rows of data")
        return output_filename
        
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        output_file = convert_to_csv()
        print(f"Successfully converted file to CSV. Output file: {output_file}")
    except Exception as e:
        print(f"Failed to convert file to CSV: {str(e)}")
