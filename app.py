import streamlit as st
import pandas as pd
import io

# Configuração da página (mudamos para "centered" para ficar mais elegante sem a barra lateral)
st.set_page_config(page_title="Extrator PNAD Contínua", layout="centered")

st.title("📊 Extrator de Microdados PNAD")
st.markdown("""
Esta ferramenta processa os arquivos brutos (.txt) do IBGE para o seu e-book.
**Configuração:** Peso Amostral bruto, processamento em blocos e salvamento dinâmico.
""")

st.divider() # Cria uma linha visual de separação

# 1. Definição das Variáveis (Dicionário Técnico)
variaveis_mapeamento = [
    {"nome": "Ano", "pos": 1, "len": 4, "desc": "Ano de referência"},
    {"nome": "Trimestre", "pos": 5, "len": 1, "desc": "Trimestre de referência"},
    {"nome": "UF", "pos": 6, "len": 2, "desc": "Unidade da Federação (Código numérico)"},
    {"nome": "Capital_", "pos": 8, "len": 2, "desc": "Capital (Código numérico)"},
    {"nome": "RM_RIDE_", "pos": 10, "len": 2, "desc": "Região Metropolitana ou RIDE"},
    {"nome": "Situacao_Domicilio_", "pos": 33, "len": 1, "desc": "Situação do domicílio"},
    {"nome": "Peso_Pessoa", "pos": 50, "len": 15, "desc": "Peso amostral da pessoa"},
    {"nome": "Moradores", "pos": 89, "len": 2, "desc": "Número de moradores"},
    {"nome": "Sexo_", "pos": 95, "len": 1, "desc": "Sexo"},
    {"nome": "Idade", "pos": 104, "len": 3, "desc": "Idade em anos"},
    {"nome": "Cor_Raca_", "pos": 107, "len": 1, "desc": "Cor ou raça"},
    {"nome": "Le_e_Escreve_", "pos": 108, "len": 1, "desc": "Sabe ler e escrever"},
    {"nome": "frequenta_escola_", "pos": 109, "len": 1, "desc": "Frequenta escola"},
    {"nome": "Dep_Adm_", "pos": 110, "len": 1, "desc": "Dependência administrativa"},
    {"nome": "Curso_Atual_", "pos": 113, "len": 2, "desc": "Curso que frequenta"},
    {"nome": "Curso_Mais_Elevado_", "pos": 125, "len": 2, "desc": "Curso mais elevado"},
    {"nome": "Tem_CNPJ_Principal_", "pos": 186, "len": 1, "desc": "Possui CNPJ no trabalho principal"},
    {"nome": "Tem_CNPJ_Secundario_", "pos": 266, "len": 1, "desc": "Possui CNPJ no trabalho secundário"},
    {"nome": "Nivel_Instrucao_", "pos": 405, "len": 1, "desc": "Nível de instrução"},
    {"nome": "Anos_Estudo", "pos": 406, "len": 2, "desc": "Anos de estudo (Código numérico)"},
    {"nome": "Condicao_Forca_", "pos": 409, "len": 1, "desc": "Condição na força de trabalho"},
    {"nome": "Condicao_Ocupacao_", "pos": 410, "len": 1, "desc": "Condição de ocupação"},
    {"nome": "Subocupacao_", "pos": 413, "len": 1, "desc": "Subocupação"},
    {"nome": "Posicao_Ocupacao_", "pos": 417, "len": 2, "desc": "Posição na ocupação (Código numérico)"},
    {"nome": "Grupo_Atv_Princ_", "pos": 419, "len": 2, "desc": "Grupo de Atividade Principal (Código numérico)"},
    {"nome": "Cont_INSS_", "pos": 423, "len": 1, "desc": "Contribui para INSS (Código numérico)"},
    {"nome": "Renda_Habitual_Principal", "pos": 427, "len": 8, "desc": "Renda habitual do trabalho principal"},
    {"nome": "Renda_Efetivo_Principal", "pos": 435, "len": 8, "desc": "Renda efetiva do trabalho principal"},
    {"nome": "Renda_Habitual_Total", "pos": 444, "len": 8, "desc": "Renda habitual de todos os trabalhos"},
    {"nome": "Renda_Efetivo_Total", "pos": 452, "len": 8, "desc": "Renda efetiva de todos os trabalhos"}
]

# Interface de Upload
st.subheader("📁 Seleção de Arquivo")
uploaded_file = st.file_uploader("Selecione o arquivo TXT da PNAD Contínua", type=["txt"])

@st.cache_data
def processar_dados(file):
    colspecs = [(v["pos"]-1, v["pos"]-1+v["len"]) for v in variaveis_mapeamento]
    nomes = [v["nome"] for v in variaveis_mapeamento]
    
    chunks = []
    # Usamos um chunksize de 30.000 para equilibrar velocidade e RAM
    for chunk in pd.read_fwf(file, colspecs=colspecs, names=nomes, dtype=str, chunksize=30000):
        chunk["Nome_Capital"] = chunk["Capital_"]
        
        # Conversão numérica sem divisão (conforme solicitado)
        if "Peso_Pessoa" in chunk.columns:
            chunk["Peso_Pessoa"] = pd.to_numeric(chunk["Peso_Pessoa"], errors='coerce')
        
        rendas = ["Renda_Habitual_Principal", "Renda_Efetivo_Principal", "Renda_Habitual_Total", "Renda_Efetivo_Total"]
        for r in rendas:
            if r in chunk.columns:
                chunk[r] = pd.to_numeric(chunk[r], errors='coerce')
        
        chunks.append(chunk)
    
    df_final = pd.concat(chunks, ignore_index=True)
    del chunks # Libera memória
    gc.collect() # Força a limpeza do sistema
    return df_final

if uploaded_file is not None:
    try:
        with st.status("Processando dados...", expanded=True) as status:
            st.write("Lendo microdados em blocos...")
            df = processar_dados(uploaded_file)
            st.write("Gerando nomes dinâmicos...")
            
            ano = df["Ano"].iloc[0]
            tri = df["Trimestre"].iloc[0]
            status.update(label=f"Concluído! PNADC {ano} T{tri}", state="complete")

        # Exibição
        st.subheader(f"🔍 Prévia: {ano} - Trimestre {tri}")
        st.dataframe(df.head(10))

        # Downloads
        st.divider()
        col1, col2 = st.columns(2)
        
        csv_name = f"PNADC_{ano}_T{tri}.csv"
        xlsx_name = f"Dicionario_PNADC_{ano}_T{tri}.xlsx"

        with col1:
            csv = df.to_csv(index=False, sep=";", decimal=",").encode('utf-8')
            st.download_button(f"Baixar Base ({csv_name})", csv, csv_name, "text/csv", use_container_width=True)

        with col2:
            output = io.BytesIO()
            df_dic = pd.DataFrame(variaveis_mapeamento)
            df_dic.loc[len(df_dic)] = ["Nome_Capital", 8, 2, "Capital (Descrição da Capital)"]
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_dic.to_excel(writer, index=False, sheet_name='Dicionário')
            st.download_button(f"Baixar Dicionário ({xlsx_name})", output.getvalue(), xlsx_name, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        st.warning("Se o erro for de 'Memory', tente rodar este script localmente em seu PC.")
else:
    st.info("Aguardando upload do arquivo para iniciar.")
