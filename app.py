import streamlit as st
import sqlite3
import pandas as pd

# Configuração da página web
st.set_page_config(page_title="Catálogo Kaizen", page_icon="🔧", layout="centered")

# Cabeçalho do sistema
st.title("🚗 Busca Rápida de Peças")
st.markdown("Preencha os dados do veículo para encontrar as peças de aplicação correta.")

# Criando 3 colunas para colocar os campos lado a lado
col1, col2, col3 = st.columns(3)

with col1:
    modelo_input = st.text_input("Modelo (ex: Gol)")
with col2:
    motor_input = st.text_input("Motor (ex: 1.0)")
with col3:
    # number_input garante que o usuário só digite números no ano
    ano_input = st.number_input("Ano", min_value=1990, max_value=2026, value=2012, step=1)

# O botão de busca
if st.button("Buscar Peças", type="primary"):

    # Só faz a busca se o usuário preencheu pelo menos o modelo e o motor
    if modelo_input and motor_input:

        # Conecta ao banco de dados
        conexao = sqlite3.connect('banco_kaizen.db')

        # A nossa query de busca
        query = '''
            SELECT p.categoria AS "Categoria", p.codigo AS "Código", p.marca AS "Marca"
            FROM veiculos v
            JOIN aplicacao a ON v.id = a.id_veiculo
            JOIN pecas p ON p.id = a.id_peca
            WHERE v.modelo LIKE ? 
              AND v.motor LIKE ? 
              AND ? BETWEEN v.ano_inicial AND v.ano_final
        '''

        # O Pandas executa a query e já guarda tudo em um DataFrame
        df_resultados = pd.read_sql_query(
            query,
            conexao,
            params=(f'%{modelo_input}%', f'%{motor_input}%', ano_input)
        )

        conexao.close()

        # Exibindo os resultados na tela
        if not df_resultados.empty:
            st.success(f"Peças encontradas para {modelo_input} {motor_input} ({ano_input}):")

            # Mostra o DataFrame como uma tabela interativa sem a coluna de índice
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma peça encontrada para os dados informados.")

    else:
        st.error("Por favor, preencha o Modelo e o Motor para realizar a busca.")