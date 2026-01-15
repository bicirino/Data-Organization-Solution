import pandas as pd
import os
import io


# Define arquivos de entrada e saída 
LISTA_DE_ARQUIVOS = [
    {
        "entrada": "membro_rows.csv", 
        "saida": "membros_LIMPO.csv"
    },
    {
        "entrada": "Relatório de Familias Com Seus Integrantes .csv", 
        "saida": "kids_LIMPO.csv"
    }
]

# Funções de limpeza e correção
def consertar_mojibake(valor):
    """
    Conserta o erro de codificação onde UTF-8.
    """
    if pd.isna(valor) or valor == '':
        return ""
    
    texto = str(valor)
    
    try:
       
        return texto.encode('cp1252').decode('utf-8')
    except:
        
        return texto

def limpar_visual(valor):
    """
    Remove ''sujeira' numérica.
    """
    if pd.isna(valor) or valor == '':
        return ""
    
    texto = str(valor).strip()
    
    # Remove sufixo .0 (comum em IDs e Telefones no Pandas)
    if texto.endswith('.0'):
        texto = texto[:-2]
        
    # Remove string 'nan'
    if texto.lower() == 'nan':
        return ""
        
    return texto

# ================= MOTOR DE PROCESSAMENTO =================

def processar_limpeza():
    print("--- INICIANDO LIMPEZA DOS ARQUIVOS ---\n")

    for item in LISTA_DE_ARQUIVOS:
        arq_in = item['entrada']
        arq_out = item['saida']
        
        print(f"-> Lendo arquivo: {arq_in} ...")
        
        if not os.path.exists(arq_in):
            print(f"   [ERRO] Arquivo não encontrado: {arq_in}")
            continue

        # 1. LEITURA BRUTA
        # Lemos o arquivo tentando pegar os caracteres "quebrados" (cp1252 ou latin1)
        # Se lermos como utf-8 direto, o Python pode esconder o erro ou dar crash.
        conteudo = ""
        try:
            with open(arq_in, 'r', encoding='cp1252') as f:
                conteudo = f.read()
        except:
            try:
                with open(arq_in, 'r', encoding='latin1') as f:
                    conteudo = f.read()
            except:
                print("   [ERRO CRÍTICO] Não foi possível ler o arquivo.")
                continue

        # 2. CONVERSÃO PARA TABELA (FORÇANDO TEXTO)
        # Detecta separador automaticamente (; ou ,)
        sep = ';' if ';' in conteudo.splitlines()[0] else ','
        
        try:
            # dtype=str impede que '00123' vire 123 e impede '1' virar '1.0'
            df = pd.read_csv(io.StringIO(conteudo), sep=sep, dtype=str)
        except Exception as e:
            print(f"   [ERRO] Falha ao tabular CSV: {e}")
            continue

        # 3. APLICAÇÃO DA LIMPEZA (Célula por Célula)
        # Passo A: Conserta os acentos (ANDRÃ‰ -> ANDRÉ)
        print("   Aplicando correção de acentos (UTF-8)...")
        df = df.applymap(consertar_mojibake)
        
        # Passo B: Limpa visual (.0 e nan)
        print("   Removendo sujeira numérica (.0)...")
        df = df.applymap(limpar_visual)
        
        # Passo C: Padroniza colunas (minusculo, sem espaco)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # 4. SALVAMENTO
        # utf-8-sig: Adiciona BOM para o Excel abrir com acentos corretos
        print(f"   Salvando arquivo limpo...")
        df.to_csv(arq_out, index=False, sep=';', encoding='utf-8-sig')
        
        print(f"   [SUCESSO] Gerado: {arq_out}\n")

    print("--- FIM DA LIMPEZA ---")
    print("Verifique os arquivos '_LIMPO.csv'.")

if __name__ == "__main__":
    processar_limpeza()