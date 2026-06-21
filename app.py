import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PyPDF2 import PdfMerger
import io
import json # <-- Adicionado para ler o JSON dos secrets

# --- 1. CONFIGURAÇÕES E CONEXÃO ---
st.set_page_config(page_title="Gestor de Prestação de Contas", layout="wide")

@st.cache_resource
def conectar_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Lê a string JSON armazenada de forma segura no Streamlit Cloud
    cred_json_str = st.secrets["text_credentials"]
    
    # Converte a string de texto para um dicionário Python
    cred_dict = json.loads(cred_json_str)
    
    # Usa o dicionário para autenticar (ao invés de buscar um arquivo físico)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    
    return gspread.authorize(creds)

client = conectar_sheets()
planilha = client.open_by_key('1UnvAdmOGZi48Ap7BwXEq9aCfRZxJCldbl9r__c0OjY0')

# --- 2. INTERFACE DO USUÁRIO ---
st.title("📄 Gestor de Documentos - Prestação de Contas")

mes_selecionado = st.selectbox("Selecione o Mês", ["Junho 2026", "Maio 2026", "Abril 2026"])
aba = planilha.worksheet(mes_selecionado)
dados = aba.get_all_records()

# Criar uma lista apenas com as linhas que precisam de comprovante
linhas_com_doc = [linha for linha in dados if "Doc." in str(linha.get("Comprovante", ""))]
opcoes_docs = {linha["Comprovante"]: linha["Descrição / Rubrica"] for linha in linhas_com_doc}

st.markdown("---")
st.subheader("Anexar e Editar Comprovantes")

doc_selecionado = st.selectbox("Selecione a Rubrica para juntar os PDFs:", 
                               list(opcoes_docs.keys()), 
                               format_func=lambda x: f"{x} - {opcoes_docs[x]}")

# --- 3. ÁREA DE UPLOAD E MERGE ---
arquivos_upados = st.file_uploader("Arraste os PDFs aqui (pode ser mais de um)", type=['pdf'], accept_multiple_files=True)

if arquivos_upados:
    st.write(f"Você carregou {len(arquivos_upados)} arquivo(s).")
    
    if st.button("Gerar Prévia Consolidada (Merge)"):
        merger = PdfMerger()
        
        for pdf in arquivos_upados:
            merger.append(pdf)
            
        # Salvar o PDF mesclado em memória para download/preview
        pdf_final_bytes = io.BytesIO()
        merger.write(pdf_final_bytes)
        pdf_final_bytes.seek(0)
        
        st.success("PDFs consolidados com sucesso!")
        st.download_button(
            label="Baixar Prévia Consolidada",
            data=pdf_final_bytes,
            file_name=f"Comprovante_{doc_selecionado.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
        st.warning("Na versão final da nuvem, este botão também fará o upload para o Google Drive e atualizará o link na planilha.")
