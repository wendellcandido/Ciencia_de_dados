import streamlit as st
import pandas as pd
import sqlite3

# Configuração da página do Streamlit (estilo dashboard limpo e moderno)
st.set_page_config(page_title="BrasileiraoAnalytics", page_icon="⚽", layout="wide")

st.title("⚽ BrasileiraoAnalytics - Dashboard de Futebol")
st.markdown("Painel interativo de análise de dados do Campeonato Brasileiro (ETL + Streamlit + SQLite).")

# Conexão com o banco de dados SQLite
@st.cache_resource
def conectar_banco():
    return sqlite3.connect("brasileirao.db", check_same_thread=False)

conn = conectar_banco()

# Buscar anos disponíveis no banco
anos_df = pd.read_sql("SELECT DISTINCT ano FROM partidas WHERE ano IS NOT NULL ORDER BY ano DESC", conn)
anos = anos_df['ano'].tolist()

if not anos:
    st.error("Nenhum dado encontrado. Execute o script `etl.py` primeiro!")
else:
    # Barra lateral (Sidebar) para controles
    st.sidebar.header("⚙️ Painel de Controle")
    ano_selecionado = st.sidebar.selectbox("Selecione a Temporada (Ano)", anos)

    # Carregar times que jogaram no ano selecionado
    query_times = f"""
        SELECT DISTINCT mandante FROM partidas WHERE ano = {ano_selecionado}
        UNION
        SELECT DISTINCT visitante FROM partidas WHERE ano = {ano_selecionado}
    """
    times_df = pd.read_sql(query_times, conn)
    lista_times = sorted(times_df['mandante'].dropna().tolist())

    time_escolhido = st.sidebar.selectbox("Selecione o Time do Coração", lista_times)

    if time_escolhido:
        st.header(f"📊 Desempenho do {time_escolhido} em {ano_selecionado}")

        # Calcular classificação e pontos de todos os times do ano selecionado
        query_todas = f"SELECT mandante, visitante, mandante_Placar, visitante_Placar, vencedor FROM partidas WHERE ano = {ano_selecionado}"
        df_todas = pd.read_sql(query_todas, conn)

        tabela_pontos = {}
        for _, row in df_todas.iterrows():
            m, v = row['mandante'], row['visitante']
            pm, pv = row['mandante_Placar'], row['visitante_Placar']
            
            for t in [m, v]:
                if t not in tabela_pontos:
                    tabela_pontos[t] = {'Pontos': 0, 'Jogos': 0, 'Vitorias': 0, 'Empates': 0, 'Derrotas': 0, 'GP': 0, 'GC': 0}
            
            tabela_pontos[m]['Jogos'] += 1
            tabela_pontos[v]['Jogos'] += 1
            tabela_pontos[m]['GP'] += pm
            tabela_pontos[m]['GC'] += pv
            tabela_pontos[v]['GP'] += pv
            tabela_pontos[v]['GC'] += pm

            if pm > pv:
                tabela_pontos[m]['Pontos'] += 3
                tabela_pontos[m]['Vitorias'] += 1
                tabela_pontos[v]['Derrotas'] += 1
            elif pv > pm:
                tabela_pontos[v]['Pontos'] += 3
                tabela_pontos[v]['Vitorias'] += 1
                tabela_pontos[m]['Derrotas'] += 1
            else:
                tabela_pontos[m]['Pontos'] += 1
                tabela_pontos[v]['Pontos'] += 1
                tabela_pontos[m]['Empates'] += 1
                tabela_pontos[v]['Empates'] += 1

        df_classificacao = pd.DataFrame.from_dict(tabela_pontos, orient='index').reset_index()
        df_classificacao.rename(columns={'index': 'Time'}, inplace=True)
        df_classificacao['SG'] = df_classificacao['GP'] - df_classificacao['GC']
        df_classificacao = df_classificacao.sort_values(by=['Pontos', 'Vitorias', 'SG'], ascending=False).reset_index(drop=True)
        df_classificacao['Posicao'] = df_classificacao.index + 1

        # Filtrar as métricas específicas do time escolhido
        info_time = df_classificacao[df_classificacao['Time'] == time_escolhido]

        # Exibir Cards de Métricas (Estilo Coinbase / Dashboards profissionais)
        col1, col2, col3, col4 = st.columns(4)
        if not info_time.empty:
            col1.metric("Pontuação Total", int(info_time['Pontos'].values[0]))
            col2.metric("Posição na Tabela", f"{int(info_time['Posicao'].values[0])}º")
            col3.metric("Jogos Disputados", int(info_time['Jogos'].values[0]))
            col4.metric("Saldo de Gols", int(info_time['SG'].values[0]))

        st.markdown("---")

        # Cartões recebidos pelo time
        query_cartoes = f"""
            SELECT c.cartao, COUNT(*) as qtd
            FROM cartoes c
            JOIN partidas p ON c.partida_id = p.ID
            WHERE p.ano = {ano_selecionado} AND c.clube = '{time_escolhido}'
            GROUP BY c.cartao
        """
        df_cartoes_time = pd.read_sql(query_cartoes, conn)
        
        st.subheader("🟨 Cartões Registrados")
        if not df_cartoes_time.empty:
            cols_cartoes = st.columns(len(df_cartoes_time))
            for i, row in df_cartoes_time.iterrows():
                cols_cartoes[i].metric(f"Cartão {row['cartao']}", int(row['qtd']))
        else:
            st.info("Sem registros de cartões para este time nesta temporada.")

        st.markdown("---")

        # Posse de bola média
        query_estat = f"""
            SELECT AVG(CAST(REPLACE(posse_de_bola, '%', '') AS REAL)) as media_posse
            FROM estatisticas e
            JOIN partidas p ON e.partida_id = p.ID
            WHERE p.ano = {ano_selecionado} AND e.clube = '{time_escolhido}' AND e.posse_de_bola IS NOT NULL
        """
        df_estat_time = pd.read_sql(query_estat, conn)
        media_posse = df_estat_time['media_posse'].values[0]

        if pd.notnull(media_posse):
            st.metric("Posse de Bola Média", f"{media_posse:.1f}%")

        st.markdown("---")

        # Histórico de Partidas (Adversários e Placares)
        st.subheader("📋 Histórico de Partidas, Adversários e Placares")
        
        query_partidas_time = f"""
            SELECT rodata, data, mandante, visitante, mandante_Placar, visitante_Placar
            FROM partidas 
            WHERE ano = {ano_selecionado} AND (mandante = '{time_escolhido}' OR visitante = '{time_escolhido}')
            ORDER BY rodata ASC
        """
        df_partidas_time = pd.read_sql(query_partidas_time, conn)

        historico_exibicao = []
        for _, row in df_partidas_time.iterrows():
            mandante = row['mandante']
            visitante = row['visitante']
            pm = row['mandante_Placar']
            pv = row['visitante_Placar']
            
            if mandante == time_escolhido:
                adversario = visitante
                placar = f"{pm} x {pv}"
                local = "Casa (Mandante)"
            else:
                adversario = mandante
                placar = f"{pv} x {pm}"
                local = "Fora (Visitante)"
                
            historico_exibicao.append({
                "Rodada": row['rodata'],
                "Data": row['data'],
                "Local": local,
                "Adversário": adversario,
                "Placar": placar
            })

        st.dataframe(pd.DataFrame(historico_exibicao), use_container_width=True)