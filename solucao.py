import pandas as pd
from unidecode import unidecode
import re
import os

# ================= CONFIGURAÇÃO =================
FILE_KIDS = 'Relatório de Familias Com Seus Integrantes .csv'
FILE_MEMBERS = 'membro_rows.csv' 
FILE_OUTPUT = 'resultado_seguranca_maxima.csv'

# Colunas do Banco (Verifique se estão certas)
DB_COL_ID = 'id_membro'
DB_COL_EMAIL = 'email'
DB_COL_NAME = 'nome'
DB_COL_PHONE = 'telefone'

# ================= FUNÇÕES DE LIMPEZA =================

def clean_text_strict(text):
    """
    Remove acentos, espaços e coloca em minúsculo.
    NÃO muda letras (h, y, w, z).
    Ex: 'Andréia ' -> 'andreia' (Match com Andreia)
    Ex: 'Matheus' -> 'matheus' (SEM Match com Mateus)
    """
    if pd.isna(text) or text == '': return ""
    return unidecode(str(text).strip().lower())

def clean_phone_strict(phone):
    """Apenas números. Sem tentativa de adivinhar DDD."""
    if pd.isna(phone) or phone == '': return ""
    return re.sub(r'\D', '', str(phone))

# ================= CARREGAMENTO =================

def load_members_database():
    print(f"--- Carregando Banco (Modo Risco Zero)... ---")
    try:
        df = pd.read_csv(FILE_MEMBERS, sep=',') 
        if DB_COL_ID not in df.columns: df = pd.read_csv(FILE_MEMBERS, sep=';')
    except:
        df = pd.read_csv(FILE_MEMBERS, sep=';')

    df.columns = [c.lower() for c in df.columns]
    
    # Mapas para busca exata
    map_email = {}
    map_phone = {}
    map_name_norm = {} # Chave é o nome normalizado (sem acento)

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
        
        # 3. Nome Normalizado
        if DB_COL_NAME.lower() in df.columns:
            raw_name = row[DB_COL_NAME.lower()]
            cn = clean_text_strict(raw_name)
            if cn:
                # Guardamos o ID e o Nome Original Bonito
                map_name_norm[cn] = {'id': mid, 'official': raw_name}
            
    return map_email, map_phone, map_name_norm

# ================= PROCESSAMENTO =================

def process_data():
    map_email, map_phone, map_name_norm = load_members_database()
    
    print(f"\n--- Processando Kids... ---")
    try:
        df_kids = pd.read_csv(FILE_KIDS, sep=';', encoding='utf-8')
    except:
        df_kids = pd.read_csv(FILE_KIDS, sep=';', encoding='latin1')
    
    output_list = []
    curr_resp = {} 
    
    stats = {'email': 0, 'phone': 0, 'name': 0, 'manual': 0}

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

            # 1. EMAIL (Prioridade Máxima)
            if c_email in map_email:
                match_id = map_email[c_email]
                match_type = "EMAIL_EXATO"
                # Recupera o nome oficial fazendo busca reversa (opcional) ou mantém o do CSV
                official_name = raw_name 
                stats['email'] += 1
            
            # 2. TELEFONE (Apenas idêntico)
            elif c_phone in map_phone:
                match_id = map_phone[c_phone]
                match_type = "TELEFONE_EXATO"
                official_name = raw_name
                stats['phone'] += 1
            
            # 3. NOME NORMALIZADO (Sem acento, mas com letras iguais)
            elif c_name in map_name_norm:
                data = map_name_norm[c_name]
                match_id = data['id']
                official_name = data['official'] # Usa o nome oficial do banco (ex: Andréia)
                match_type = "NOME_SEM_ACENTO"
                stats['name'] += 1
            
            else:
                match_type = "FALHA"
                match_id = "MANUAL_CHECK"
                stats['manual'] += 1

            curr_resp = {
                'id': match_id,
                'name_db': official_name if official_name else raw_name,
                'email': raw_email,
                'phone': raw_phone,
                'method': match_type
            }

        elif row_type == 'Criança':
            output_list.append({
                'ID_Responsavel': curr_resp.get('id', 'MANUAL_CHECK'),
                'Nome_Responsavel': curr_resp.get('name_db'),
                'Nome_Crianca': str(row['Text7']).strip(),
                'Email_Original': curr_resp.get('email'),
                'Telefone_Original': curr_resp.get('phone'),
                'Metodo_Match': curr_resp.get('method', 'FALHA')
            })

    # ================= SAÍDA =================
    df_out = pd.DataFrame(output_list)
    df_out.to_csv(FILE_OUTPUT, index=False, sep=';', encoding='utf-8-sig')
    
    print("\n" + "="*40)
    print("RELATÓRIO RISCO ZERO")
    print("="*40)
    print(f"EMAIL (Exato):          {stats['email']}")
    print(f"TELEFONE (Exato):       {stats['phone']}")
    print(f"NOME (Sem acentos):     {stats['name']}")
    print("-" * 30)
    print(f"NÃO ENCONTRADO (Fazer Manual): {stats['manual']}")
    print(f"\nArquivo gerado: {FILE_OUTPUT}")

if __name__ == "__main__":
    process_data()