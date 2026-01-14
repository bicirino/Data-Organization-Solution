#Declaração de bibliotecas
import pandas as pd
from unidecode import unidecode
import os 
import re 
#____________________________________________________________________________________________________________________________________________________

# Configurações de arquivos
FILE_KIDS = 'Relatório de Familias Com Seus Integrantes .csv'
FILE_MEMBERS = 'membro_rows.csv' 
FILE_OUTPUT = 'tabela_associativa_final.csv'
#___________________________________________________________________________________________________________________________________________________

# Monopolização de texto e limpeza de dados
def clean_text(text):
    """Remove acentos, converte para minúsculo e remove espaços extras."""
    if pd.isna(text) or text == '':
        return None
    text = str(text).strip().lower()
    return unidecode(text)
#____________________________________________________________________________________________________________________________________________________
# Monopolização de telefones 
def clean_phone(phone):
    """Keep only numbers. Removes (), -, spaces."""
    if pd.isna(phone) or phone == '':
        return None
    clean = re.sub(r'\D', '', str(phone))
    return clean

#____________________________________________________________________________________________________________________________________________________
# Carregamento do banco de membros
def load_members_database():
    print(f"--- Loading Members Database: {FILE_MEMBERS} ---")
    
    if not os.path.exists(FILE_MEMBERS):
        print(f"CRITICAL ERROR: File '{FILE_MEMBERS}' not found.")
        return None, None, None, None

    
    try:
        df = pd.read_csv(FILE_MEMBERS, sep=',') 
        if 'email' not in df.columns and 'Email' not in df.columns:
           
            df = pd.read_csv(FILE_MEMBERS, sep=';')
    except:
        df = pd.read_csv(FILE_MEMBERS, sep=';')

   
    df.columns = [c.lower() for c in df.columns]

    
    if 'id' not in df.columns:
        print(f"ERROR: Column 'id' not found. Available columns: {list(df.columns)}")
        return None, None, None, None

    
    map_email = {}
    map_phone = {}
    map_name = {}
    map_original_names = {} 

    count = 0
    for _, row in df.iterrows():
        mid = row['id']
        
        
        if 'email' in df.columns:
            cleaned_email = clean_text(row['email'])
            if cleaned_email:
                map_email[cleaned_email] = mid
                if 'nome' in df.columns:
                    map_original_names[mid] = row['nome']

        
        phone_col = next((col for col in ['telefone', 'celular', 'phone', 'whatsapp'] if col in df.columns), None)
        if phone_col:
            cleaned_phone = clean_phone(row[phone_col])
            if cleaned_phone:
                map_phone[cleaned_phone] = mid
        
        
        if 'nome' in df.columns:
            cleaned_name = clean_text(row['nome'])
            if cleaned_name:
                map_name[cleaned_name] = mid

        count += 1
            
    print(f"-> Database loaded. {count} members processed.")
    print(f"-> Lookup indexes built: By Email, By Phone, By Name.")
    return map_email, map_phone, map_name, map_original_names

#____________________________________________________________________________________________________________________________________________________
# Processamento principal dos dados

def process_data():
    map_email, map_phone, map_name, map_db_names = load_members_database()
    if not map_email:
        return

    print(f"\n--- Processing Kids Report: {FILE_KIDS} ---")
    
   
    df_kids = pd.read_csv(FILE_KIDS, sep=';', encoding='utf-8')
    
    output_list = []
    
    
    current_parent_name = None
    current_parent_raw_email = None
    current_parent_raw_phone = None
    current_parent_id = None
    match_method = "NONE" 
    
    stats = {'email_match': 0, 'phone_match': 0, 'name_match': 0, 'failed': 0}

    for index, row in df_kids.iterrows():
        
        
        raw_name = str(row['Text7']).strip()
        row_type = str(row['Text15']).strip() 
        raw_email = str(row['Text11']).strip()
        raw_phone = str(row['Text10']).strip() 
        
        if row_type == 'Responsavel':
            current_parent_name = raw_name
            current_parent_raw_email = raw_email
            current_parent_raw_phone = raw_phone
            
       
            
            
            clean_e = clean_text(raw_email)
            found_id = map_email.get(clean_e)
            match_method = "EMAIL"
            
            
            if not found_id:
                clean_p = clean_phone(raw_phone)
                found_id = map_phone.get(clean_p)
                match_method = "PHONE"
            
            
            if not found_id:
                clean_n = clean_text(raw_name)
                found_id = map_name.get(clean_n)
                match_method = "NAME"
            
            if not found_id:
                match_method = "NOT_FOUND"
                
            current_parent_id = found_id
            
        elif row_type == 'Criança':
            if current_parent_name:
                
                official_name = map_db_names.get(current_parent_id, current_parent_name)
                
              
                if current_parent_id:
                    if match_method == "EMAIL": stats['email_match'] += 1
                    elif match_method == "PHONE": stats['phone_match'] += 1
                    elif match_method == "NAME": stats['name_match'] += 1
                else:
                    stats['failed'] += 1

                output_list.append({
                    'ID_Responsavel': current_parent_id if current_parent_id else 'MANUAL_CHECK',
                    'Nome_Responsavel': official_name,
                    'Email_Responsavel': current_parent_raw_email,
                    'Telefone_Responsavel': current_parent_raw_phone,
                    'Nome_Crianca': raw_name,
                    'Metodo_Match': match_method if current_parent_id else 'FALHA'
                })

#____________________________________________________________________________________________________________________________________________________
# Exportação dos resultados
    df_out = pd.DataFrame(output_list)
    
    # Export with 'utf-8-sig' to fix Excel accent issues
    df_out.to_csv(FILE_OUTPUT, index=False, sep=';', encoding='utf-8-sig')
    
    print("\n" + "="*40)
    print("FINAL REPORT")
    print("="*40)
    print(f"Matches by EMAIL: {stats['email_match']}")
    print(f"Matches by PHONE: {stats['phone_match']}")
    print(f"Matches by NAME : {stats['name_match']}")
    print(f"FAILURES        : {stats['failed']}")
    print("-" * 40)
    print(f"File generated: {FILE_OUTPUT}")
    print("Instruction: Open this file directly in Excel.")
#____________________________________________________________________________________________________________________________________________________
# Encerramento 
if __name__ == "__main__":
    process_data()