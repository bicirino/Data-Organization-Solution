#Declaração de bibliotecas
import pandas as pd
from unidecode import unidecode
import os 
#____________________________________________________________________________________________________________________________________________________

# Configurações de arquivos
ARQUIVO_KIDS = 'Relatório de Familias Com Seus Integrantes .csv'
ARQUIVO_MEMBROS = 'membro_rows.csv' 
ARQUIVO_SAIDA = 'tabela_associativa_final.csv'
#___________________________________________________________________________________________________________________________________________________

# Função principal
def processar_dados():
    print("1. Lendo arquivo de Membros...")
    try:
        # Carrega o CSV de membros
        # Ajuste 'sep' se o separador for ponto-e-vírgula (;) ou vírgula (,)
        df_membros = pd.read_csv(ARQUIVO_MEMBROS, sep=',') 
        
        # Limpeza básica (converter email para minúsculo para garantir a monopolização)
        df_membros['email'] = df_membros['email'].astype(str).str.lower().str.strip()
        
        # Cria um "mapa" para busca rápida: Email -> ID
        mapa_ids = dict(zip(df_membros['email'], df_membros['id_membro']))
        print(f"   -> {len(mapa_ids)} membros carregados.")
        
    except FileNotFoundError:
        print(f"ERRO: Não encontrei o arquivo '{ARQUIVO_MEMBROS}'.")
        return

    print("2. Lendo relatório do Kids...")
    df_kids = pd.read_csv(ARQUIVO_KIDS, sep=';', encoding='utf-8')

    lista_final = []
    
    # Variáveis temporárias 
    pai_atual_nome = None
    pai_atual_email = None
    pai_atual_id = None

    # Laço de repetição para processar cada linha do relatório Kids
    for index, row in df_kids.iterrows():
        
        
        nome = str(row['Text7']).strip()
        tipo = str(row['Text15']).strip() 
        email_bruto = str(row['Text11']).strip()
        
        if tipo == 'Responsavel':
            # Atualiza o valor das variáveis temporárias 
            pai_atual_nome = nome
            pai_atual_email = email_bruto.lower()
            
            # Busca o ID desse email 
            pai_atual_id = mapa_ids.get(pai_atual_email, 'ID_NAO_ENCONTRADO')
            
        elif tipo == 'Criança':
            # Se é criança, vinculamos ao último responsável lido
            if pai_atual_nome:
                lista_final.append({
                    'id_responsavel': pai_atual_id,
                    'nome_responsavel': pai_atual_nome,
                    'email_responsavel': pai_atual_email,
                    'nome_crianca': nome
                })

#___________________________________________________________________________________________________________________________________
    
    # Gerando o arquivo final
    df_saida = pd.DataFrame(lista_final)
    df_saida.to_csv(ARQUIVO_SAIDA, index=False, sep=';')
    
    print("-" * 30)
    print(f"SUCESSO! Arquivo gerado: {ARQUIVO_SAIDA}")
    print(f"Total de crianças vinculadas: {len(lista_final)}")
    
    # Contagem de quantos não foram encontrados
    nao_achados = len([x for x in lista_final if x['id_responsavel'] == 'ID_NAO_ENCONTRADO'])
    if nao_achados > 0:
        print(f"ATENÇÃO: {nao_achados} crianças ficaram com responsável 'ID_NAO_ENCONTRADO'.")
        print("Verifique se o email no relatório Kids é exatamente igual ao do banco de membros.")

#___________________________________________________________________________________________________________________________________
# Encerramento
if __name__ == "__main__":
    processar_dados()