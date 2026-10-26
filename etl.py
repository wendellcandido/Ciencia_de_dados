import os
import pandas as pd
import sqlite3

def executar_etl():
    print("Iniciando o processo de ETL do Campeonato Brasileiro...")
    
    # Cria/conecta ao banco de dados SQLite local na raiz do projeto
    db_path = "brasileirao.db"
    conn = sqlite3.connect(db_path)
    
    # 1. Extração e Carga de Partidas
    caminho_partidas = os.path.join("data", "campeonato-brasileiro-full.csv")
    if os.path.exists(caminho_partidas):
        df_partidas = pd.read_csv(caminho_partidas)
        # Transformação: Criar a coluna 'ano' extraída da data para facilitar os filtros por temporada
        df_partidas['ano'] = pd.to_datetime(df_partidas['data'], format='%d/%m/%Y', errors='coerce').dt.year
        # Carga: Salva na tabela 'partidas' do SQLite
        df_partidas.to_sql("partidas", conn, if_exists="replace", index=False)
        print("-> Tabela 'partidas' carregada com sucesso!")
    else:
        print(f"Arquivo não encontrado: {caminho_partidas}")

    # 2. Extração e Carga de Cartões
    caminho_cartoes = os.path.join("data", "campeonato-brasileiro-cartoes.csv")
    if os.path.exists(caminho_cartoes):
        df_cartoes = pd.read_csv(caminho_cartoes)
        df_cartoes.to_sql("cartoes", conn, if_exists="replace", index=False)
        print("-> Tabela 'cartoes' carregada com sucesso!")
    else:
        print(f"Arquivo não encontrado: {caminho_cartoes}")

    # 3. Extração e Carga de Estatísticas (posse de bola, chutes, etc.)
    caminho_estatisticas = os.path.join("data", "campeonato-brasileiro-estatisticas-full.csv")
    if os.path.exists(caminho_estatisticas):
        df_estatisticas = pd.read_csv(caminho_estatisticas)
        df_estatisticas.to_sql("estatisticas", conn, if_exists="replace", index=False)
        print("-> Tabela 'estatisticas' carregada com sucesso!")
    else:
        print(f"Arquivo não encontrado: {caminho_estatisticas}")

    conn.close()
    print("Processo de ETL concluído! Banco de dados 'brasileirao.db' gerado na raiz.")

if __name__ == "__main__":
    executar_etl()