import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Verificação", layout="wide")

st.title("Relatórios CSV ➡️ Excel")
st.info("Insira o arquivo 'export.csv' abaixo para processar os dados.")

# --- NOVO: CAMPO DE INPUT PARA O CABEÇALHO ---
nome_projeto = st.text_input(
    "Nome do Projeto", placeholder="Ex: UFV SANTA EUGÊNIA SOLAR 1.2")

# --- 1. UPLOAD DO ARQUIVO ---
uploaded_file = st.file_uploader("Arraste seu CSV aqui", type="csv")

if uploaded_file is not None:
    # Lendo o arquivo subido
    rel = pd.read_csv(uploaded_file, sep=None,
                      engine='python', encoding='utf-8-sig')

    # --- 2. SEU CÓDIGO DE FILTRAGEM (Mantido igual) ---
    list_cabecalho = [
        "Image Filename", "Issue Severity", "Issue Longitude", "Issue Latitude",
        "Issue Type Name", "Issue Component Name", "Issue Temp Min", "Issue Temp Max",
        "Issue Temp Avg", "Issue Temp Delta", "Issue Field Type", "Issue Field"
    ]

    cabecalho_1 = rel[list_cabecalho].copy()
    cabecalho_1["Severidade"] = "0"
    cabecalho_1["Localização"] = "OK"
    cabecalho_1["Posição"] = "OK"

    indices_longit = rel[rel['Issue Longitude'].isna()].index.tolist()
    indices_delta = rel[rel['Issue Temp Delta'].isna()].index.tolist()
    indices_coment = rel[rel['Issue Field'].isna()].index.tolist()

    cabecalho_1.loc[indices_coment, "Posição"] = "Verificar Posição"
    cabecalho_1.loc[indices_longit, "Localização"] = "Verificar Localização"
    cabecalho_1.loc[indices_delta, "Severidade"] = "Verificar Severidade"

    def tratar_delta(valor):
        try:
            val_str = str(valor)
            return float(val_str[:-1]) if val_str.endswith(('C', 'F', 'K')) else float(val_str)
        except:
            return 0.0

    cabecalho_1["delta_float"] = cabecalho_1["Issue Temp Delta"].apply(
        tratar_delta)

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
            cabecalho_1.loc[i, "Severidade"] = "OK"
        elif linha_delta >= 40 and "Severity 4" in issue_sev:
            cabecalho_1.loc[i, "Severidade"] = "OK"
        else:
            if i not in indices_delta:
                cabecalho_1.loc[i, "Severidade"] = "Verificar Severidade"

    # --- 3. EXIBIÇÃO E DOWNLOAD ---
    st.success("Arquivo processado com sucesso!")

    # visualização prévia

    colunas_exibir = [
        "Image Filename", "Issue Severity", "Issue Longitude", "Issue Latitude",
        "Issue Type Name", "Issue Component Name", "Issue Temp Min", "Issue Temp Max",
        "Issue Temp Avg", "Issue Temp Delta", "Issue Field Type", "Issue Field",
        "Severidade", "Localização", "Posição"
    ]

    df_excel = cabecalho_1[colunas_exibir]

    # Mostra uma prévia na tela para conferência
    st.subheader("Prévia do Relatório")
    st.dataframe(df_excel)

    colunas_export = [
        "Image Filename", "Issue Severity", "Issue Longitude", "Issue Latitude",
        "Issue Type Name", "Issue Component Name", "Issue Temp Min", "Issue Temp Max",
        "Issue Temp Avg", "Issue Temp Delta", "Issue Field Type", "Issue Field"
    ]
    df_export = cabecalho_1[colunas_export]

    # Transformação para Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False,
                           sheet_name='Relatorio_Filtrado', startrow=4)

        workbook = writer.book
        worksheet = writer.sheets['Relatorio_Filtrado']

        # Criar um formato para o texto (Negrito e tamanho maior)
        merge_format = workbook.add_format({
            'bold': True,
            'font_size': 40,
            'align': 'left',
            'valign': 'vcenter'
        })

        # --- AJUSTE DA LOGO E TEXTO AO LADO ---
        # Inserir a imagem na célula A1
        worksheet.insert_image(
            'A1', 'logo.png', {'x_scale': 0.25, 'y_scale': 0.1})

        # Escrever o conteúdo do input ao lado (ex: na célula C2 ou D2 dependendo do tamanho da logo)
        # O write('C2', ...) coloca o texto na linha 2, coluna C.
        worksheet.write('H2', nome_projeto, merge_format)

        # --- NOVO: AJUSTE AUTOMÁTICO DE LARGURA DE COLUNAS ---
        # Itera sobre cada coluna do dataframe para encontrar o tamanho máximo do conteúdo
        for i, col in enumerate(df_export.columns):
            # Calcula o tamanho do cabeçalho
            column_len = len(str(col))

            # Calcula o tamanho do maior item na coluna (limite de 100 linhas para performance)
            max_item_len = df_export[col].astype(str).str.len().max()

            # Define a largura (o maior entre o cabeçalho e o conteúdo, com uma folga de +2)
            width = max(column_len, max_item_len) + 2

            # Aplica o ajuste (i é o índice da coluna)
            worksheet.set_column(i, i, width)

    st.download_button(
        label="📥 Baixar Relatório em Excel (.xlsx)",
        data=output.getvalue(),
        file_name="Relatorio_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
