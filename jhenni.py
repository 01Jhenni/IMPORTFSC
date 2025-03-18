import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
import plotly.express as px

conn = sqlite3.connect("import_register.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    empresa TEXT,
                    tipo_nota TEXT,
                    erro TEXT,
                    arquivo_erro TEXT,
                    status TEXT DEFAULT 'Pendente')''')
conn.commit()

st.title("📑 Importação")
with st.form("registro_form"):
    empresa = st.text_input("Nome da Empresa")
    tipo_nota = st.selectbox("Tipo de Nota", ["NFE entrada", "NFE saída", "CTE entrada", "CTE saída", "CTE cancelado", "SPED", "NFS tomado", "NFS prestado", "Planilha", "NFCE saída"])
    erro = st.text_area("Erro (se houver)")
    arquivo = st.file_uploader("Anexar imagem do erro", type=["png", "jpeg", "jpg"])
    submit = st.form_submit_button("Registrar")
    if submit:
        data_atual = datetime.date.today().strftime("%d-%m-%Y")
        arquivo_path = ""
        
        if arquivo:
            pasta_arquivos = "arquivos_erros"
            os.makedirs(pasta_arquivos, exist_ok=True)
            arquivo_path = os.path.join(pasta_arquivos, f"{data_atual}_{arquivo.name}")
            with open(arquivo_path, "wb") as f:
                f.write(arquivo.read())
        
        status = 'OK' if not erro else 'Pendente'
        
        cursor.execute("INSERT INTO registros (data, empresa, tipo_nota, erro, arquivo_erro, status) VALUES (?, ?, ?, ?, ?, ?)",
                       (data_atual, empresa, tipo_nota, erro, arquivo_path, status))
        conn.commit()
        st.success("✅ Registro salvo com sucesso!")
st.subheader("📋 Registros Salvos")
registros = pd.read_sql_query("SELECT * FROM registros", conn)

if not registros.empty:
    for index, row in registros.iterrows():
        with st.expander(f"📌 {row['empresa']} - {row['tipo_nota']}"):
            st.write(f"**Erro:** {row['erro']}" if row['erro'] else "**Sem erro registrado.**")
            st.write(f"**Data:** {row['data']}")
            st.write(f"**Status:** {row['status']}")
            if row['arquivo_erro'] and os.path.exists(row['arquivo_erro']):
                st.markdown(f"[📷 Visualizar Imagem]({row['arquivo_erro']})", unsafe_allow_html=True)
                st.image(row['arquivo_erro'], caption="", use_container_width=True)
            if row['status'] == "Pendente":
                if st.button("✔ OK", key=row['id']):
                    cursor.execute("UPDATE registros SET status = 'Resolvido' WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.success(f"✅ Status do registro {row['id']} atualizado para 'Resolvido'.")
                    st.rerun()  

st.subheader("📈 Indicadores de Importação")
if not registros.empty:
    col1, col2 = st.columns(2)
# Registros por empresa
    empresa_count = registros["empresa"].value_counts().reset_index()
    empresa_count.columns = ["Empresa", "Total de Registros"]
    fig1 = px.pie(empresa_count, names="Empresa", values="Total de Registros", title="📌 Registros por Empresa")
    col1.plotly_chart(fig1)
# Tipos de notas
    tipo_nota_count = registros["tipo_nota"].value_counts().reset_index()
    tipo_nota_count.columns = ["Tipo de Nota", "Quantidade"]
    fig2 = px.pie(tipo_nota_count, names="Tipo de Nota", values="Quantidade", title="📌 Tipos de Nota Registradas")
    col2.plotly_chart(fig2)
# Empresas importadas
    importadas = registros["empresa"].nunique()
    total_registros = len(registros)
    df_empresas = pd.DataFrame({"Status": ["Importadas", "Não Importadas"], "Quantidade": [importadas, total_registros - importadas]})
    fig3 = px.pie(df_empresas, names="Status", values="Quantidade", title="📌 Empresas Importadas vs. Não Importadas")
    st.plotly_chart(fig3)
# Erros mais frequentes
    if registros["erro"].notna().sum() > 0:
        erro_count = registros["erro"].value_counts().reset_index().head(5)
        erro_count.columns = ["Erro", "Frequência"]
        st.subheader("🔴 Erros Mais Comuns")
        fig4 = px.pie(erro_count, names="Erro", values="Frequência", title="📌 Erros Mais Frequentes")
        st.plotly_chart(fig4)
