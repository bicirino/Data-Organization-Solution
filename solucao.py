import pandas as pd
from unidecode import unidecode
import re
import os

# ================= CONFIGURAÇÃO =================
FILE_KIDS = 'Relatório de Familias Com Seus Integrantes .csv'
FILE_MEMBERS = 'membro_rows.csv' 
FILE_OUTPUT = 'resultado_final.csv'

# Colunas do Banco
DB_COL_ID = 'id_membro'
DB_COL_EMAIL = 'email'
DB_COL_NAME = 'nome'
DB_COL_PHONE = 'telefone'

# ================= FUNÇÕES DE LIMPEZA =================

def clean_text_strict(text):
    """Normaliza: minúsculo, sem acento, sem espaços."""
    if pd.isna(text) or text == '': return ""
    return unidecode(str(text).strip().lower())

def clean_phone_strict(phone):
    """Apenas números, sem tentar adivinhar DDD."""
    if pd.isna(phone) or phone == '': return ""
    return re.sub(r'\D', '', str(phone))

# ================= CARREGAMENTO =================

def load_members_database():
    print(f"--- Carregando Banco de Membros... ---")
    try:
        df = pd.read_csv(FILE_MEMBERS, sep=',') 
        if DB_COL_ID not in df.columns: df = pd.read_csv(FILE_MEMBERS, sep=';')
    except:
        df = pd.read_csv(FILE_MEMBERS, sep=';')

    df.columns = [c.lower() for c in df.columns]
    
    map_email = {}
    map_phone = {}
    map_name_norm = {} 

    for _, row in df.iterrows():
        mid = row[DB_COL_ID.lower()]
        
        # 1. Email
        if DB_COL_EMAIL.lower() in df.columns:
            ce = clean_text_strict(row[DB_COL_EMAIL.lower()])
            if ce: map_email[ce] = mid
        
        # 2. Telefone
        if DB_COL_PHONE.lower() in df.columns:
            cp = clean_phone_strict(row[DB_COL_PHONE.lower()])
            if cp and len(cp) >= 8: 
                map_phone[cp] = mid
        
        # 3. Nome
        if DB_COL_NAME.lower() in df.columns:
            raw_name = row[DB_COL_NAME.lower()]
            cn = clean_text_strict(raw_name)
            if cn:
                map_name_norm[cn] = {'id': mid, 'official': raw_name}
            
    return map_email, map_phone, map_name_norm

# ================= PROCESSAMENTO PRINCIPAL =================

def process_data():
    map_email, map_phone, map_name_norm = load_members_database()
    
    print(f"\n--- Processando Kids... ---")
    try:
        df_kids = pd.read_csv(FILE_KIDS, sep=';', encoding='utf-8')
    except:
        df_kids = pd.read_csv(FILE_KIDS, sep=';', encoding='latin1')
    
    output_list = []
    curr_resp = {} 
    
    count_saved = 0
    count_discarded = 0

    for index, row in df_kids.iterrows():
        row_type = str(row['Text15']).strip()
        
        if row_type == 'Responsavel':
            raw_name = str(row['Text7']).strip()
            raw_email = str(row['Text11']).strip()
            raw_phone = str(row['Text10']).strip()
            
            c_name = clean_text_strict(raw_name)
            c_email = clean_text_strict(raw_email)
            c_phone = clean_phone_strict(raw_phone)
            
            match_id = None
            match_type = "NOT_FOUND"
            official_name = ""

            # 1. EMAIL
            if c_email in map_email:
                match_id = map_email[c_email]
                match_type = "EMAIL_EXATO"
                official_name = raw_name 
            
            # 2. TELEFONE
            elif c_phone in map_phone:
                match_id = map_phone[c_phone]
                match_type = "TELEFONE_EXATO"
                official_name = raw_name
            
            # 3. NOME
            elif c_name in map_name_norm:
                data = map_name_norm[c_name]
                match_id = data['id']
                official_name = data['official'] 
                match_type = "NOME_SEM_ACENTO"
            
            curr_resp = {
                'id': match_id,
                'name_db': official_name if official_name else raw_name,
                'email': raw_email,
                'phone': raw_phone,
                'method': match_type
            }

        elif row_type == 'Criança':
            # Só adiciona se tiver ID válido
            if curr_resp.get('id'):
                output_list.append({
                    'ID_Responsavel': curr_resp['id'],
                    'Nome_Responsavel_Banco': curr_resp['name_db'],
                    'Nome_Crianca': str(row['Text7']).strip(),
                    'Metodo_Match': curr_resp['method'],
                    'Email_Original': curr_resp['email'],
                    'Telefone_Original': curr_resp['phone']
                })
                count_saved += 1
            else:
                count_discarded += 1

    # ================= ORDENAÇÃO E SAÍDA =================
    if output_list:
        df_out = pd.DataFrame(output_list)
        
        # Tenta converter ID para número para ordenar corretamente (1, 2, 10 e não 1, 10, 2)
        try:
            df_out['ID_Responsavel'] = pd.to_numeric(df_out['ID_Responsavel'])
        except:
            pass # Se o ID tiver letras (UUID), ordena como texto mesmo
            
        # ORDENAÇÃO AQUI
        df_out.sort_values(by='ID_Responsavel', ascending=True, inplace=True)
        
        # Salva
        df_out.to_csv(FILE_OUTPUT, index=False, sep=';', encoding='utf-8-sig')
        
        print("\n" + "="*40)
        print("RELATÓRIO FINAL ORDENADO")
        print("="*40)
        print(f"Sucesso: {count_saved} registros.")
        print(f"Descartados (Sem vínculo seguro): {count_discarded}")
        print("-" * 40)
        print(f"Arquivo gerado: {FILE_OUTPUT}")
    else:
        print("Nenhum match encontrado. Verifique os arquivos.")

if __name__ == "__main__":
    process_data()