import pandas as pd
import streamlit as st
import os

# --- Configuração da página ---
st.set_page_config("Média Total - Sem Outliers", layout="wide")
st.title("Média Total entre Compra e Início (Sem Outliers)")
st.markdown("Análise geral do tempo médio entre a compra e o início do curso, com filtros dinâmicos e remoção de outliers via método IQR.")

# --- Caminho do HTML de saída ---
html_output_path = "output5/index.html"
os.makedirs("output5", exist_ok=True)

# --- Leitura dos dados ---
df_vagas = pd.read_csv("C:/Users/r.barcelos_g4educaca/Documents/cobertura_estoque/data/raw/vagas_fct.csv")
df_vagas["closed_at"] = pd.to_datetime(df_vagas["closed_at"], errors="coerce")
df_vagas["inicio_at"] = pd.to_datetime(df_vagas["inicio_at"], errors="coerce")
df_vagas["dias_entre_compra_e_inicio"] = (df_vagas["inicio_at"] - df_vagas["closed_at"]).dt.days
df_vagas["dias_entre_compra_e_inicio"] = df_vagas["dias_entre_compra_e_inicio"].clip(lower=0)

# --- Filtros dinâmicos ---
st.sidebar.header("Filtros")
aluno_ids = st.sidebar.multiselect("Filtrar por aluno_id", df_vagas["aluno_id"].dropna().unique())
turmas = st.sidebar.multiselect("Filtrar por turma", df_vagas["turma"].dropna().unique())
pipelines = st.sidebar.multiselect("Filtrar por pipeline_name", df_vagas["pipeline_name"].dropna().unique())

datas_validas = df_vagas["closed_at"].dropna()
data_min = datas_validas.min()
data_max = datas_validas.max()
intervalo_data = st.sidebar.date_input("Filtrar por intervalo de data (closed_at)", [data_min, data_max])

# --- Aplicar filtros ---
df_filtrado_geral = df_vagas.copy()
if aluno_ids:
    df_filtrado_geral = df_filtrado_geral[df_filtrado_geral["aluno_id"].isin(aluno_ids)]
if turmas:
    df_filtrado_geral = df_filtrado_geral[df_filtrado_geral["turma"].isin(turmas)]
if pipelines:
    df_filtrado_geral = df_filtrado_geral[df_filtrado_geral["pipeline_name"].isin(pipelines)]
if intervalo_data:
    data_ini, data_fim = pd.to_datetime(intervalo_data[0]), pd.to_datetime(intervalo_data[1])
    df_filtrado_geral = df_filtrado_geral[(df_filtrado_geral["closed_at"] >= data_ini) & (df_filtrado_geral["closed_at"] <= data_fim)]

# --- Separar registros sem inicio_at (abertos) ---
df_sem_inicio = df_filtrado_geral[df_filtrado_geral["inicio_at"].isna()].copy()
qtd_abertos_sem_inicio = len(df_sem_inicio)

# --- Aplicar IQR apenas em registros com inicio_at válido ---
df_validos = df_filtrado_geral[df_filtrado_geral["inicio_at"].notna()].copy()
q1 = df_validos["dias_entre_compra_e_inicio"].quantile(0.25)
q3 = df_validos["dias_entre_compra_e_inicio"].quantile(0.75)
iqr = q3 - q1
limite_inferior = max(q1 - 1.5 * iqr, 0)
limite_superior = q3 + 1.5 * iqr

# --- Separar outliers com base no IQR ---
df_sem_outliers = df_validos[
    (df_validos["dias_entre_compra_e_inicio"] >= limite_inferior) &
    (df_validos["dias_entre_compra_e_inicio"] <= limite_superior)
].copy()

df_outliers_iqr = df_validos[~df_validos.index.isin(df_sem_outliers.index)].copy()

# --- Consolidar outliers (IQR + sem inicio)
df_outliers = pd.concat([df_outliers_iqr, df_sem_inicio], ignore_index=True)

# --- Colunas desejadas ---
colunas_desejadas = ["aluno_id", "turma", "pipeline_name", "closed_at", "inicio_at", "dias_entre_compra_e_inicio"]

# --- Métricas ---
media_total = df_sem_outliers["dias_entre_compra_e_inicio"].mean()
qtd_sem_outliers = len(df_sem_outliers)
qtd_outliers = len(df_outliers)

# --- Exibição no Streamlit ---
st.subheader(f"Média Total (sem outliers): `{media_total:.2f}` dias")
st.markdown(f"**Quantidade de registros sem outliers:** `{qtd_sem_outliers}`")
st.markdown(f"**Quantidade de registros considerados outliers:** `{qtd_outliers}`")
st.markdown(f"**Registros abertos (sem início):** `{qtd_abertos_sem_inicio}`")
st.markdown(f"**Limite mínimo (IQR):** `{limite_inferior}` dias")
st.markdown(f"**Limite máximo (IQR):** `{limite_superior}` dias")

with st.expander("Ver dados sem outliers"):
    st.dataframe(df_sem_outliers[colunas_desejadas], use_container_width=True)

with st.expander("Ver dados considerados outliers"):
    st.dataframe(df_outliers[colunas_desejadas], use_container_width=True)

# --- Exportação CSV ---
col1, col2 = st.columns(2)
with col1:
    csv_sem = df_sem_outliers[colunas_desejadas].to_csv(index=False).encode("utf-8")
    st.download_button("Baixar dados sem outliers", csv_sem, "sem_outliers.csv", "text/csv")
with col2:
    csv_out = df_outliers[colunas_desejadas].to_csv(index=False).encode("utf-8")
    st.download_button("Baixar outliers (inclui abertos)", csv_out, "outliers.csv", "text/csv")

# --- Tabela de filtros aplicados (simulação visual dos dropdowns) ---
filtros_tabela = """
<h3>Filtros aplicados:</h3>
<table border="1" cellpadding="6" cellspacing="0" style="background-color:white; color:black;">
"""
if aluno_ids:
    filtros_tabela += f"<tr><td><strong>aluno_id</strong></td><td>{', '.join(map(str, aluno_ids))}</td></tr>"
if turmas:
    filtros_tabela += f"<tr><td><strong>turma</strong></td><td>{', '.join(map(str, turmas))}</td></tr>"
if pipelines:
    filtros_tabela += f"<tr><td><strong>pipeline_name</strong></td><td>{', '.join(map(str, pipelines))}</td></tr>"
if intervalo_data:
    filtros_tabela += f"<tr><td><strong>Intervalo de data (closed_at)</strong></td><td>{intervalo_data[0]} até {intervalo_data[1]}</td></tr>"
filtros_tabela += "</table>"

# --- HTML final ---
html_dashboard = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>Média Total - Sem Outliers</title>
    <style>
        body {{
            background-color: #010c26;
            color: white;
            font-family: Arial, sans-serif;
            padding: 40px;
        }}
        h1 {{
            color: #ff5c52;
        }}
        .collapsible {{
            background-color: #ff5c52;
            color: white;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            margin-top: 20px;
        }}
        .content {{
            display: none;
            max-height: 400px;
            overflow-y: auto;
            padding: 10px;
            background-color: white;
            color: black;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #ff5c52;
            color: white;
        }}
    </style>
</head>
<body>
    <h1>Média Total entre Compra e Início</h1>
    <p>Dados com outliers removidos via IQR e registros abertos tratados como outliers.</p>
    {filtros_tabela}
    <h3>Média Total (sem outliers): {media_total:.2f} dias</h3>
    <p><strong>Quantidade sem outliers:</strong> {qtd_sem_outliers}</p>
    <p><strong>Quantidade de outliers:</strong> {qtd_outliers}</p>
    <p><strong>Registros abertos (sem início):</strong> {qtd_abertos_sem_inicio}</p>
    <p><strong>Limite mínimo (IQR):</strong> {limite_inferior}</p>
    <p><strong>Limite máximo (IQR):</strong> {limite_superior}</p>

    <button class="collapsible">Ver dados sem outliers</button>
    <div class="content">
        {df_sem_outliers[colunas_desejadas].to_html(index=False)}
    </div>

    <button class="collapsible">Ver dados considerados outliers (inclui abertos)</button>
    <div class="content">
        {df_outliers[colunas_desejadas].to_html(index=False)}
    </div>

    <script>
        var coll = document.getElementsByClassName("collapsible");
        for (var i = 0; i < coll.length; i++) {{
            coll[i].addEventListener("click", function() {{
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }});
        }}
    </script>
</body>
</html>
"""

# --- Salvar HTML
with open(html_output_path, "w", encoding="utf-8") as f:
    f.write(html_dashboard)

# --- Botão de download do HTML
with open(html_output_path, "rb") as f:
    st.download_button(
        label="Baixar versão HTML simples para Netlify",
        data=f,
        file_name="index.html",
        mime="text/html"
    )
