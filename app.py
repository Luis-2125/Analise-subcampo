import streamlit as st
import pandas as pd
import io
import re  # Import necessário para a limpeza de texto

st.set_page_config(page_title="SCOPSCAN", layout="wide")

st.title("Relatórios CSV ➡️ Excel")
st.info("Insira o arquivo 'export.csv' abaixo para processar os dados.")

nome_projeto = st.text_input(
    "Nome do Projeto", placeholder="Ex: UFV SANTA EUGÊNIA SOLAR 1.2")

uploaded_file = st.file_uploader("Arraste seu CSV aqui", type="csv")

if uploaded_file is not None:
    rel = pd.read_csv(uploaded_file, sep=None,
                      engine='python', encoding='utf-8-sig')

    list_cabecalho = [
        "Image Filename", "Issue Severity", "Issue Longitude", "Issue Latitude",
        "Issue Type Name", "Issue Component Name", "Issue Temp Min", "Issue Temp Max",
        "Issue Temp Avg", "Issue Temp Delta", "Issue Field Type", "Issue Field"
    ]

    cabecalho_1 = rel[list_cabecalho].copy()

    # 1. Definição da função de limpeza de coordenadas
    def limpar_coordenada_v3(valor):
        if pd.isna(valor) or str(valor).strip() == "" or str(valor).lower() == "nan":
            return valor

        # Remove todos os pontos e espaços para pegar apenas a sequência numérica
        str_val = str(valor).replace('.', '').strip()
        is_negative = str_val.startswith('-')

        # Filtra apenas os dígitos
        digits = "".join(filter(str.isdigit, str_val))

        if not digits:
            return valor

        # Regra de Negócio: Para coordenadas GPS padrão (Brasil),
        # a parte inteira tem 2 dígitos (Ex: -37.xxx ou -49.xxx).
        # Ajustamos para colocar o ponto após os dois primeiros dígitos.
        parte_inteira = digits[:2]
        parte_decimal = digits[2:]

        valor_final = f"{parte_inteira}.{parte_decimal}"

        # Retorna como float para o Excel reconhecer como número
        try:
            return float(f"-{valor_final}" if is_negative else valor_final)
        except:
            return valor

    # 2. Aplicação em ambas as colunas
    colunas_geo = ["Issue Longitude", "Issue Latitude"]
    for col in colunas_geo:
        if col in cabecalho_1.columns:
            cabecalho_1[col] = cabecalho_1[col].apply(limpar_coordenada_v3)
    # --- FUNÇÃO PADRÃO PARA TODAS AS TEMPERATURAS ---
# ... (segue o resto do seu código)

    # --- FUNÇÃO PADRÃO PARA TODAS AS TEMPERATURAS ---

    def formatar_temp_final(valor):
        if pd.isna(valor) or str(valor).strip() == "":
            return ""

        val_str = str(valor)

        # 1. Pega o conteúdo após a última vírgula (para os casos de Min e Max)
        if ',' in val_str:
            trecho = val_str.split(',')[-1].strip()
        else:
            trecho = val_str.strip()

        # 2. Extrai apenas o número (ignora 'C', '°', etc)
        match = re.search(r"[-+]?\d*\.?\d+", trecho)
        if match:
            try:
                numero = float(match.group())
                # Retorna com 2 casas decimais e o símbolo
                return f"{numero:.2f}°C"
            except:
                return trecho
        return trecho

    # Aplicando em todas as colunas de temperatura
    colunas_temp = ["Issue Temp Min", "Issue Temp Max",
                    "Issue Temp Avg", "Issue Temp Delta"]
    for col in colunas_temp:
        if col in cabecalho_1.columns:
            cabecalho_1[col] = cabecalho_1[col].apply(formatar_temp_final)
    # ------------------------------------------------------

    cabecalho_1["Severidade"] = "0"
    cabecalho_1["Localização"] = "OK"
    cabecalho_1["Posição"] = "OK"

    # ... (Resto do seu código de processamento de Severidade permanece igual) ...
    indices_longit = rel[rel['Issue Longitude'].isna()].index.tolist()
    indices_delta = rel[rel['Issue Temp Delta'].isna()].index.tolist()
    indices_coment = rel[rel['Issue Field'].isna()].index.tolist()

    cabecalho_1.loc[indices_coment, "Posição"] = "Verificar Posição"
    cabecalho_1.loc[indices_longit, "Localização"] = "Verificar Localização"
    cabecalho_1.loc[indices_delta, "Severidade"] = "Verificar Severidade"

    # __________________

   # --- 1. FUNÇÃO DE LIMPEZA (RETORNA None SE ESTIVER VAZIO) ---
    def limpar_para_float_v2(valor):
        if pd.isna(valor) or str(valor).strip() == "" or str(valor).lower() == "nan":
            return None  # Retorna None para identificar que não há dado

        val_str = str(valor)
        if ',' in val_str:
            val_str = val_str.split(',')[-1]

        match = re.search(r"[-+]?\d*\.?\d+", val_str)
        if match:
            return float(match.group())
        return None

    # Criamos colunas numéricas temporárias
    cabecalho_1["temp_min_num"] = cabecalho_1["Issue Temp Min"].apply(
        limpar_para_float_v2)
    cabecalho_1["temp_max_num"] = cabecalho_1["Issue Temp Max"].apply(
        limpar_para_float_v2)
    cabecalho_1["delta_num"] = cabecalho_1["Issue Temp Delta"].apply(
        limpar_para_float_v2)

    # --- 2. LÓGICA DE VALIDAÇÃO (SEVERIDADE, LOCALIZAÇÃO E POSIÇÃO) ---
    for i in range(len(cabecalho_1)):
        # --- DADOS PARA CÁLCULO ---
        linha_delta = cabecalho_1.loc[i, "delta_num"]
        # Issue Longitude e Issue Field já estão no DataFrame original
        valor_longitude = cabecalho_1.loc[i, "Issue Longitude"]
        valor_posicao = cabecalho_1.loc[i, "Issue Field"]

        issue_sev = str(cabecalho_1.loc[i, "Issue Severity"])
        damage_type = str(cabecalho_1.loc[i, "Issue Type Name"])

        # --- A. VALIDAÇÃO DE SEVERIDADE ---
        if pd.isna(linha_delta):
            cabecalho_1.loc[i, "Severidade"] = "Verificar Severidade"
        else:
            if damage_type in ["Damage", "Open String", "Open Circuit"]:
                cabecalho_1.loc[i, "Severidade"] = "OK"
            elif linha_delta < 5.0 and "Severity 1" in issue_sev:
                cabecalho_1.loc[i, "Severidade"] = "OK"
            elif 5.0 <= linha_delta < 20.0 and "Severity 2" in issue_sev:
                cabecalho_1.loc[i, "Severidade"] = "OK"
            elif 20.0 <= linha_delta < 40.0 and "Severity 3" in issue_sev:
                cabecalho_1.loc[i, "Severidade"] = "OK"
            elif linha_delta >= 40.0 and "Severity 4" in issue_sev:
                cabecalho_1.loc[i, "Severidade"] = "OK"
            else:
                cabecalho_1.loc[i, "Severidade"] = "Verificar Severidade"

        # --- B. VALIDAÇÃO DE LOCALIZAÇÃO (Coordenadas) ---
        # Se a longitude for nula ou zero (caso comum em erros de GPS)
        if pd.isna(valor_longitude) or valor_longitude == 0:
            cabecalho_1.loc[i, "Localização"] = "Verificar Localização"
        else:
            cabecalho_1.loc[i, "Localização"] = "OK"

        # --- C. VALIDAÇÃO DE POSIÇÃO (Comentário/Field) ---
        # Se o campo de posição estiver vazio ou for apenas espaços
        if pd.isna(valor_posicao) or str(valor_posicao).strip() == "":
            cabecalho_1.loc[i, "Posição"] = "Verificar Posição"
        else:
            cabecalho_1.loc[i, "Posição"] = "OK"

    # --- RESUMO DE ALERTAS NO STREAMLIT ---
    with st.expander("📊 Resumo do Processamento"):
        col1, col2, col3 = st.columns(3)

        erros_sev = cabecalho_1["Severidade"].value_counts().get(
            "Verificar Severidade", 0)
        erros_loc = cabecalho_1["Localização"].value_counts().get(
            "Verificar Localização", 0)
        erros_pos = cabecalho_1["Posição"].value_counts().get(
            "Verificar Posição", 0)

        col1.metric("Severidade para Revisar", erros_sev,
                    delta=erros_sev, delta_color="inverse")
        col2.metric("Falhas de Localização", erros_loc)
        col3.metric("Falhas de Posição", erros_pos)

    # --- 3. FORMATAÇÃO PARA EXIBIÇÃO ---
    def formatar_para_relatorio(num):
        if pd.isna(num):
            return ""  # Deixa a célula vazia no Excel se não houver dado
        return f"{num:.2f}°C"

    cabecalho_1["Issue Temp Min"] = cabecalho_1["temp_min_num"].apply(
        formatar_para_relatorio)
    cabecalho_1["Issue Temp Max"] = cabecalho_1["temp_max_num"].apply(
        formatar_para_relatorio)
    cabecalho_1["Issue Temp Delta"] = cabecalho_1["delta_num"].apply(
        formatar_para_relatorio)

    # --- 4. GRÁFICO DE DISTRIBUIÇÃO POR TIPO ---
    st.divider()  # Adiciona uma linha divisória
    st.subheader("📊 Distribuição de Issues por Tipo")

    # Contabiliza a quantidade de cada tipo de erro
    df_counts = cabecalho_1["Issue Type Name"].value_counts().reset_index()
    df_counts.columns = ["Tipo de Issue", "Quantidade"]

    # Criação do gráfico de barras
    # O Streamlit usa o índice como o eixo X (categorias)
    st.bar_chart(df_counts.set_index("Tipo de Issue"))

    # Opcional: Mostrar uma tabela resumida ao lado se preferir
    if st.checkbox("Mostrar tabela de contagem"):
        st.table(df_counts)

    # --- EXPORTAÇÃO PARA EXCEL ---
    st.success("Arquivo processado com sucesso!")

    # Mensagens de atenção caso existam erros
    if erros_sev > 0 or erros_loc > 0 or erros_pos > 0:
        st.warning(
            f"🚨 Foram encontrados problemas em {erros_sev + erros_loc + erros_pos} linhas. Verifique a prévia abaixo ou o arquivo Excel gerado.")
    else:
        st.success("✅ Todos os dados parecem estar em conformidade!")

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

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        linha_inicio = 3
        df_export.to_excel(writer, index=False, sheet_name='Relatorio',
                           startrow=linha_inicio + 1, header=False)

        workbook = writer.book
        worksheet = writer.sheets['Relatorio']

        fmt_centro = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter'})
        fmt_header = workbook.add_format(
            {'bold': True, 'align': 'center', 'bg_color': '#D7E4BC'})

        # Formato para o Título do Projeto
        merge_format = workbook.add_format(
            {'bold': True, 'font_size': 40, 'align': 'left', 'valign': 'vcenter'})

        # Escrever Cabeçalhos e Formatar Colunas
        for col_num, value in enumerate(df_export.columns.values):
            worksheet.write(linha_inicio, col_num, value, fmt_header)

            # Ajuste de largura automático
            max_len = max(df_export[value].astype(
                str).map(len).max(), len(value)) + 5
            worksheet.set_column(col_num, col_num, max_len, fmt_centro)

        # Inserir Logo e Nome do Projeto
        try:
            worksheet.insert_image(
                'A1', 'logo.png', {'x_scale': 0.25, 'y_scale': 0.1})
        except:
            st.warning(
                "Arquivo 'logo.png' não encontrado para o cabeçalho do Excel.")

        worksheet.write('H2', nome_projeto, merge_format)
        worksheet.hide_gridlines(2)

    st.download_button(
        label="📥 Baixar Relatório em Excel (.xlsx)",
        data=output.getvalue(),
        file_name=f"Relatorio_{nome_projeto.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
