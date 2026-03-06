import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Verificação", layout="wide")

st.title("Relatórios CSV ➡️ Excel")
st.info("Insira o arquivo 'export.csv' abaixo para processar os dados.")

# --- 1. UPLOAD DO ARQUIVO ---
uploaded_file = st.file_uploader("Arraste seu CSV aqui", type="csv")

if uploaded_file is not None:
    # Lendo o arquivo subido
    rel = pd.read_csv(uploaded_file)
    
    # --- 2. SEU CÓDIGO DE FILTRAGEM ---
    list_cabecalho = [
        "Image Filename","Issue Severity","Issue Longitude","Issue Latitude",
        "Issue Type Name","Issue Component Name","Issue Temp Min","Issue Temp Max",
        "Issue Temp Avg","Issue Temp Delta","Issue Field Type","Issue Field"
    ]
    
    # Criando o dataframe filtrado
    cabecalho_1 = rel[list_cabecalho].copy()
    
    # Inicializando colunas
    cabecalho_1["Severidade"] = "0"
    cabecalho_1["Localização"] = "OK"
    cabecalho_1["Posição"] = "OK"

    # Identificando índices vazios
    indices_longit = rel[rel['Issue Longitude'].isna()].index.tolist()
    indices_delta = rel[rel['Issue Temp Delta'].isna()].index.tolist()
    indices_coment = rel[rel['Issue Field'].isna()].index.tolist()

    # Aplicando marcações de verificação
    cabecalho_1.loc[indices_coment, "Posição"] = "Verificar Posição"
    cabecalho_1.loc[indices_longit, "Localização"] = "Verificar Localização"
    cabecalho_1.loc[indices_delta, "Severidade"] = "VERIFICAR"

    # Tratamento da coluna Delta (Removendo o último caractere e convertendo)
    def tratar_delta(valor):
        try:
            val_str = str(valor)
            return float(val_str[:-1]) if val_str.endswith(('C', 'F', 'K')) else float(val_str)
        except:
            return 0.0

    cabecalho_1["delta_float"] = cabecalho_1["Issue Temp Delta"].apply(tratar_delta)

    # Lógica de Severidade (Sua estrutura de IF/ELIF)
    for i in range(len(cabecalho_1)):
        linha_delta = cabecalho_1.loc[i, "delta_float"]
        issue_sev = str(cabecalho_1.loc[i, "Issue Severity"])
        damage_type = str(cabecalho_1.loc[i, "Issue Type Name"])

        if damage_type in ["Damage", "Open String"]:
            cabecalho_1.loc[i, "Severidade"] = "OK"
        elif linha_delta < 5 and "Severity 1" in issue_sev:
            cabecalho_1.loc[i, "Severidade"] = "OK"
        elif 5 <= linha_delta < 20 and "Severity 2" in issue_sev:
            cabecalho_1.loc[i, "Severidade"] = "OK"
        elif 20 <= linha_delta < 40 and "Severity 3" in issue_sev:
            cabecalho_1.loc[i, "Severidade"] = "OK" # Ajustado conforme seu padrão
            cabecalho_1.loc[i, "Severidade"] = "OK"
        elif linha_delta >= 40 and "Severity 4" in issue_sev:
            cabecalho_1.loc[i, "Severidade"] = "OK"
        else:
            if i not in indices_delta: # Evita sobrepor o "VERIFICAR" dos nulos
                cabecalho_1.loc[i, "Severidade"] = "Verificar Severidade"

    # --- 3. EXIBIÇÃO E DOWNLOAD ---
    st.success("Arquivo processado com sucesso!")
    
    # Define aqui EXATAMENTE as colunas que você quer no Excel final
    # (Removi a 'delta_float' e quaisquer outras auxiliares)
    colunas_exibir = [
        "Image Filename","Issue Severity","Issue Longitude","Issue Latitude",
        "Issue Type Name","Issue Component Name","Issue Temp Min","Issue Temp Max",
        "Issue Temp Avg","Issue Temp Delta","Issue Field Type","Issue Field",
        "Severidade", "Localização", "Posição"
    ]
    
    df_excel = cabecalho_1[colunas_exibir]

    # Mostra uma prévia na tela para conferência
    st.subheader("Prévia do Relatório")
    st.dataframe(df_excel)

    #Planilha que será exportada

    colunas_export = [
        "Image Filename","Issue Severity","Issue Longitude","Issue Latitude",
        "Issue Type Name","Issue Component Name","Issue Temp Min","Issue Temp Max",
        "Issue Temp Avg","Issue Temp Delta","Issue Field Type","Issue Field"
    ]

    df_export = cabecalho_1[colunas_export]

    # Transformação para Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Enviamos para o Excel apenas o dataframe filtrado
        df_export.to_excel(writer, index=False, sheet_name='Relatorio_Filtrado')
    
    st.download_button(
        label="📥 Baixar Relatório em Excel (.xlsx)",
        data=output.getvalue(),
        file_name="Relatorio_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )