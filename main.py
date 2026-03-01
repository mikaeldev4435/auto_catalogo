import sqlite3
import pandas as pd
import os

# ==========================================
# PARTE 1: CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================
print("Iniciando o sistema...")
conexao = sqlite3.connect('banco_kaizen.db')
cursor = conexao.cursor()

# Cria as tabelas se elas não existirem
cursor.execute('''
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modelo TEXT NOT NULL,
        motor TEXT NOT NULL,
        ano_inicial INTEGER,
        ano_final INTEGER
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pecas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT NOT NULL,
        codigo TEXT NOT NULL,
        marca TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS aplicacao (
        id_veiculo INTEGER,
        id_peca INTEGER,
        FOREIGN KEY(id_veiculo) REFERENCES veiculos(id),
        FOREIGN KEY(id_peca) REFERENCES pecas(id)
    )
''')
conexao.commit()


# ==========================================
# PARTE 2: SINCRONIZAÇÃO INTELIGENTE (CSV -> BANCO)
# ==========================================
print("Sincronizando banco de dados com o arquivo CSV...")

# Lê o arquivo CSV (agora ele vai ler toda vez que o programa abrir)
df_pecas = pd.read_csv('aplicacoes.csv',sep=';')

for index, linha in df_pecas.iterrows():

    # 1. Verifica ou Cadastra o Veículo
    cursor.execute('''
        SELECT id FROM veiculos 
        WHERE modelo = ? AND motor = ? AND ano_inicial = ? AND ano_final = ?
    ''', (linha['Modelo'], linha['Motor'], linha['Ano_Inicial'], linha['Ano_Final']))

    resultado_carro = cursor.fetchone()
    if resultado_carro:
        id_carro = resultado_carro[0]
    else:
        cursor.execute('''
            INSERT INTO veiculos (modelo, motor, ano_inicial, ano_final)
            VALUES (?, ?, ?, ?)
        ''', (linha['Modelo'], linha['Motor'], linha['Ano_Inicial'], linha['Ano_Final']))
        id_carro = cursor.lastrowid

    # 2. Verifica ou Cadastra a Peça (A novidade entra aqui!)
    # Vamos checar se o código e a marca da peça já estão no banco
    cursor.execute('''
        SELECT id FROM pecas WHERE codigo = ? AND marca = ?
    ''', (linha['Codigo'], linha['Marca']))

    resultado_peca = cursor.fetchone()
    if resultado_peca:
        id_peca = resultado_peca[0]  # Peça já existe, só pegamos o ID dela
    else:
        # É uma peça nova! Vamos cadastrar.
        cursor.execute('''
            INSERT INTO pecas (categoria, codigo, marca)
            VALUES (?, ?, ?)
        ''', (linha['Categoria'], linha['Codigo'], linha['Marca']))
        id_peca = cursor.lastrowid

    # 3. Verifica ou Cria a ponte na tabela Aplicação (Evita duplicidade do vínculo)
    cursor.execute('''
        SELECT * FROM aplicacao WHERE id_veiculo = ? AND id_peca = ?
    ''', (id_carro, id_peca))

    resultado_aplicacao = cursor.fetchone()
    if not resultado_aplicacao:
        # Só insere na tabela de aplicação se esse carro e essa peça ainda não estiverem ligados
        cursor.execute('''
            INSERT INTO aplicacao (id_veiculo, id_peca)
            VALUES (?, ?)
        ''', (id_carro, id_peca))

conexao.commit()
print("Banco de dados sincronizado e pronto para uso!\n")

# ==========================================
# PARTE 3: O SISTEMA DE BUSCA (A INTERFACE)
# ==========================================
# Criamos um loop (while True) para o sistema não fechar após a primeira busca
while True:
    print("\n" + "=" * 50)
    print("   SISTEMA DE BUSCA RÁPIDA DE PEÇAS   ")
    print("   (Digite 'sair' no modelo para fechar) ")
    print("=" * 50)

    # Coleta os dados do cliente
    modelo_input = input("Digite o modelo do carro (ex: Gol): ")

    # Se digitar 'sair', o sistema encerra
    if modelo_input.lower() == 'sair':
        print("Encerrando o sistema. Bom trabalho na Kaizen!")
        break

    motor_input = input("Digite o motor (ex: 1.0): ")
    ano_input = input("Digite o ano (ex: 2012): ")

    # Faz a busca no banco cruzando as tabelas
    query = '''
        SELECT p.categoria, p.codigo, p.marca 
        FROM veiculos v
        JOIN aplicacao a ON v.id = a.id_veiculo
        JOIN pecas p ON p.id = a.id_peca
        WHERE v.modelo LIKE ? 
          AND v.motor LIKE ? 
          AND ? BETWEEN v.ano_inicial AND v.ano_final
    '''

    cursor.execute(query, (f'%{modelo_input}%', f'%{motor_input}%', int(ano_input)))
    resultados = cursor.fetchall()

    print(f"\n--- Resultado para: {modelo_input} {motor_input} ({ano_input}) ---")

    if resultados:
        for peca in resultados:
            categoria, codigo, marca = peca
            print(f"✔️ {categoria}: {codigo} ({marca})")
    else:
        print("❌ Nenhuma peça encontrada para esse veículo.")

# Quando sair do loop, fechamos a conexão com o banco
cursor.close()
conexao.close()