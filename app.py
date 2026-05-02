import streamlit as st
import pandas as pd
import io

# Configuração da página (mudamos para "centered" para ficar mais elegante sem a barra lateral)
st.set_page_config(page_title="Extrator PNAD Contínua", layout="centered")

st.title("📊 Extrator de Microdados PNAD")
st.markdown("""
Esta ferramenta processa os arquivos brutos (.txt) do IBGE.
**Atualizações:** Lê arquivos pesados em blocos, mantém o Peso Amostral bruto, salva arquivos dinamicamente e agora possui **layout centralizado**.
""")

st.divider() # Cria uma linha visual de separação

# ---------------------------------------------------------
# UPLOAD NA TELA CENTRAL (Sem st.sidebar)
# ---------------------------------------------------------
st.subheader("📁 Seleção de Arquivo")
uploaded_file = st.file_uploader("Arraste e solte ou clique para selecionar o arquivo TXT da PNAD", type=["txt"])

st.divider() # Outra linha de separação

# 1. Definição das Variáveis
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

if uploaded_file is not None:
    st.info("🔄 Processando dados em blocos para economizar memória...")
    
    colspecs = [(v["pos"]-1, v["pos"]-1+v["len"]) for v in variaveis_mapeamento]
    nomes = [v["nome"] for v in variaveis_mapeamento]
    
    # Processamento em blocos menores (20k linhas) é mais seguro para a nuvem
    lista_chunks = []
    
    try:
        with st.spinner('Extraindo variáveis...'):
            # O parâmetro low_memory ajuda no gerenciamento de recursos
            for chunk in pd.read_fwf(uploaded_file, colspecs=colspecs, names=nomes, dtype=str, chunksize=20000):
                
                # Tratamentos imediatos para liberar memória
                chunk["Nome_Capital"] = chunk["Capital_"]
                if "Peso_Pessoa" in chunk.columns:
                    chunk["Peso_Pessoa"] = pd.to_numeric(chunk["Peso_Pessoa"], errors='coerce')
                
                # Manter apenas as colunas necessárias para diminuir o tamanho do DataFrame final
                lista_chunks.append(chunk)
                
            df = pd.concat(lista_chunks, ignore_index=True)
            # Limpa a lista da memória
            del lista_chunks
            
        st.success("✅ Processamento concluído!")
    
    # Nomes dinâmicos
    ano_arquivo = df["Ano"].iloc[0] if "Ano" in df.columns else "Ano"
    tri_arquivo = df["Trimestre"].iloc[0] if "Trimestre" in df.columns else "Tri"
    
    nome_csv_dinamico = f"PNADC_{ano_arquivo}_T{tri_arquivo}.csv"
    nome_dic_dinamico = f"Dicionario_PNADC_{ano_arquivo}_T{tri_arquivo}.xlsx"

    st.subheader(f"🔍 Prévia dos Dados: {ano_arquivo} - Trimestre {tri_arquivo}")
    st.dataframe(df.head())

    # Área de Download
    st.subheader("📥 Download dos Arquivos")
    col1, col2 = st.columns(2)

    with col1:
        csv = df.to_csv(index=False, sep=";", decimal=",").encode('utf-8')
        st.download_button(
            label=f"Baixar Base de Dados ({nome_csv_dinamico})",
            data=csv,
            file_name=nome_csv_dinamico,
            mime="text/csv",
            use_container_width=True # Ocupa todo o espaço da coluna para o botão ficar mais bonito
        )

    with col2:
        buffer = io.BytesIO()
        df_dic = pd.DataFrame(variaveis_mapeamento)
        df_dic.loc[len(df_dic)] = ["Nome_Capital", 8, 2, "Capital (Descrição da Capital)"]
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_dic.to_excel(writer, index=False, sheet_name='Dicionário')
        
        st.download_button(
            label=f"Baixar Dicionário ({nome_dic_dinamico})",
            data=buffer.getvalue(),
            file_name=nome_dic_dinamico,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    except Exception as e:
        st.error(f"Erro de processamento: {e}. O arquivo pode ser grande demais para a nuvem gratuita.")
else:
    st.warning("☝️ Faça o upload do arquivo TXT acima para iniciar o processamento.")
