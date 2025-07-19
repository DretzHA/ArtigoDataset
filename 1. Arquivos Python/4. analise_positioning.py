import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.image as mpimg
import math

'''Arquivo para processar e analisar o erro do ângulo azimute'''
# Caminho base para os datasets
# base_path = '0. Dataset Original'
base_path = '0. Dataset com Mascara Virtual'

# Escolher Cenário - calibration | static | mobility
cenario = 'mobility'  # Cenário a ser analisado

# Variável para definir se os gráficos e resultados serão feitos por cada tipo de ppe_id ou pela média
por_ppe_id = True  # True para resultados por ppe_id, False para resultados pela média

# Variável para escolher se arquivos específicos serão considerados
considerar_arquivos = {
    "ORT": False,
    "SYLABS": False,
    "UBLOX": False,
    "4T": False,
    "3T": False,
    "OUTROS": True
}

# Variáveis para definir quais gráficos serão plotados
plotar_graficos = {
    "grafico_espacial_erro_distancia": False,
    "grafico_barras_erro_medio": False  # Nova variável de controle
}

# Caminho para a imagem de fundo
img_path = '1. Arquivos Python/99. Imagens/background_v2.png'
img = mpimg.imread(img_path)

# Mapeamento do cenário para as pastas correspondentes
cenario_to_folder = {
    'calibration': '0. Calibration',
    'static': '1. Static',
    'mobility': '2. Mobility'
}

# Mapeamento das âncoras
anchor_mapping = {
    'ble-pd-0C4314F46CC2': 1,
    'ble-pd-0C4314F46B3F': 2,
    'ble-pd-0C4314F46B26': 3,
    'ble-pd-0C4314F469CC': 4,
    'ble-pd-C299A0EB1D6C': 5,
    'ble-pd-639AA0EB1D6C': 6,
    'ble-pd-D299A0EB1D6C': 7    
}

# Coordenadas das âncoras (valores padrão)
anchor_coords = {
    1: {'x': -1.00, 'y': 7.83},  # A01
    2: {'x': -0.96, 'y': 1.22},  # A02
    3: {'x': -5.81, 'y': 7.85},  # A03
    4: {'x': -3.50, 'y': 4.60},  # A04
    5: {'x': -5.76, 'y': 4.64},  # A05
    6: {'x': -0.98, 'y': 4.54},  # A06
    7: {'x': -5.85, 'y': 1.21},  # A07
}

# Atualizar coordenadas das âncoras se ORT estiver habilitado
if considerar_arquivos["ORT"]:
    anchor_coords.update({
        1: {'x': -0.84, 'y': 0.54},  # A01
        2: {'x': -7.14, 'y': 7.74},  # A02
        3: {'x': -1.14, 'y': 7.74},  # A03
        4: {'x': -7.74, 'y': 0.84},  # A04
    })

# Função para filtrar arquivos com base na variável considerar_arquivos
def filtrar_arquivos(data_files):
    # Filtrar arquivos específicos
    if considerar_arquivos["ORT"] and not considerar_arquivos["4T"]:
        data_files = [f for f in data_files if f.startswith('ORT')]
    elif not considerar_arquivos["ORT"] and considerar_arquivos["4T"]:
        data_files = [f for f in data_files if '4T' in f and not f.startswith('ORT')]
    else:
        if not considerar_arquivos["ORT"]:
            data_files = [f for f in data_files if not f.startswith('ORT')]
        if not considerar_arquivos["SYLABS"]:
            data_files = [f for f in data_files if 'SYLABS' not in f]
        if not considerar_arquivos["UBLOX"]:
            data_files = [f for f in data_files if 'UBLOX' not in f]
        if not considerar_arquivos["4T"]:
            data_files = [f for f in data_files if '4T' not in f]
        if not considerar_arquivos["3T"]:
            data_files = [f for f in data_files if '3T' not in f]
    
    # Excluir arquivos "OUTROS" se considerar_arquivos["OUTROS"] for False
    if not considerar_arquivos["OUTROS"]:
        data_files = [f for f in data_files if (
            f.startswith('ORT') or 
            'SYLABS' in f or 
            'UBLOX' in f or 
            '4T' in f or 
            '3T' in f
        )]
    
    return data_files

# Função para normalizar os ppeIDs
def normalizar_ppe_ids(data_df):
    ppe_id_map = {
        'ble-pd-B43A31EF7B26': 'Capacete',
        'ble-pd-588E816309D5': 'Camisa',
        'ble-pd-B43A31EF7B34': 'Camisa',
        'ble-pd-B43A31EF7527': 'Camisa',
        'ble-pd-B43A31EB228D': 'Bota',
        'ble-pd-B43A31EB2289': 'Calça',
    }
    if cenario == 'static' or cenario == 'mobility':
        if 'ppeID' in data_df.columns:
            data_df['ppeID'] = data_df['ppeID'].replace(ppe_id_map)
        elif 'ppe_id' in data_df.columns:
            data_df['ppe_id'] = data_df['ppe_id'].replace(ppe_id_map)
    return data_df

def calcular_erro_2d(df, x_est_col, y_est_col, x_real_col, y_real_col):
    """Adiciona coluna de erro 2D ao DataFrame."""
    df['erro_2d'] = np.sqrt((df[x_est_col] - df[x_real_col])**2 + (df[y_est_col] - df[y_real_col])**2)
    return df

def calcular_erro_z(df, z_est_col, z_real_col):
    """Adiciona coluna de erro Z ao DataFrame."""
    df['erro_z'] = np.abs(df[z_est_col] - df[z_real_col])
    return df

def plotar_espacial(df, x_est_col, y_est_col, x_real_col, y_real_col, ppe_col, titulo, img):
    """Plota gráfico espacial das posições reais e estimadas, com linhas conectando real e estimado."""
    plt.figure(figsize=(10, 8))
    plt.imshow(img, extent=[0, -10.70, 8.8, 0], aspect='auto', alpha=0.5)
    for ppe in df[ppe_col].unique():
        subdf = df[df[ppe_col] == ppe]
        plt.scatter(subdf[x_real_col], subdf[y_real_col], label=f'Real Position', marker='o', s=30)
        plt.scatter(subdf[x_est_col], subdf[y_est_col], label=f'Estimated Position', marker='x', s=30)
        # Adiciona linhas conectando cada ponto real ao estimado
        for _, row in subdf.iterrows():
            plt.plot([row[x_real_col], row[x_est_col]], [row[y_real_col], row[y_est_col]], color='gray', alpha=0.5, linewidth=1)
    plt.xlabel('X (m)', fontsize=14)
    plt.ylabel('Y (m)', fontsize=14)
    #plt.title(titulo)
    plt.legend(fontsize=12, loc = 'upper right')
    ax = plt.gca()
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=14)
    #plt.grid(True)
    plt.savefig(f'/home/andrey/Desktop/mobility_1t_v2.eps', format='eps', dpi=20)
    plt.show()

# --- Laço principal de processamento ---
folder = os.path.join(base_path, cenario_to_folder[cenario])
data_path = os.path.join(folder, 'Data IQ')
data_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
data_files = filtrar_arquivos(data_files)

resultados = []
resultados_linha = []  # Novo: resultados por linha para comparação detalhada

for file in data_files:
    file_path = os.path.join(data_path, file)
    df = pd.read_csv(file_path)
    df = normalizar_ppe_ids(df)
    # Remover linhas onde x_real ou y_real são -100
    df = df[(df['X_real'] != -100) & (df['Y_real'] != -100)]
    # Detectar nomes das colunas
    x_est_col = 'X_sylabs'
    y_est_col = 'Y_sylabs'
    z_est_col = 'Z_sylabs'
    x_real_col = 'X_real'
    y_real_col = 'Y_real'
    z_real_col = 'Z_real'
    # Corrigir nomes se necessário
    for col in [x_est_col, y_est_col, z_est_col, x_real_col, y_real_col, z_real_col]:
        if col not in df.columns:
            raise ValueError(f'Coluna {col} não encontrada em {file}')
    # Normalizar nome do ppeID
    ppe_col = 'ppeID' if 'ppeID' in df.columns else 'ppe_id'
    df = calcular_erro_2d(df, x_est_col, y_est_col, x_real_col, y_real_col)
    df = calcular_erro_z(df, z_est_col, z_real_col)
    # Salvar resultados por linha para comparação detalhada
    for _, row in df.iterrows():
        resultados_linha.append({
            'arquivo': file,
            'ppeID': row[ppe_col],
            'x_real': row[x_real_col],
            'y_real': row[y_real_col],
            'erro_2d': row['erro_2d'],
            'erro_z': row['erro_z']
        })
    # Calcular erro médio por ppeID (mantém para outros usos)
    for ppe, subdf in df.groupby(ppe_col):
        erro_medio_2d = subdf['erro_2d'].mean()
        erro_medio_z = subdf['erro_z'].mean()
        x_real_mean = subdf[x_real_col].mean()
        y_real_mean = subdf[y_real_col].mean()
        resultados.append({
            'arquivo': file,
            'ppeID': ppe,
            'erro_medio_2d': erro_medio_2d,
            'erro_medio_z': erro_medio_z,
            'x_real': x_real_mean,
            'y_real': y_real_mean
        })
        # Plotar gráfico espacial se habilitado
        if plotar_graficos["grafico_espacial_erro_distancia"]:
            plotar_espacial(subdf, x_est_col, y_est_col, x_real_col, y_real_col, ppe_col,
                            f'{file} - {ppe}', img)

# Plotar gráfico de barras do erro médio por arquivo e por ppeID, se habilitado
if plotar_graficos.get("grafico_barras_erro_medio", False):
    resultados_df = pd.DataFrame(resultados)
    # Agrupar por arquivo e ppeID e calcular média dos erros
    erro_medio_por_arquivo_ppe = resultados_df.groupby(['arquivo', 'ppeID'])[['erro_medio_2d', 'erro_medio_z']].mean().reset_index()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=erro_medio_por_arquivo_ppe, x='arquivo', y='erro_medio_2d', hue='ppeID')
    plt.ylabel('Erro Médio 2D (m)')
    plt.xlabel('Arquivo')
    plt.title('Erro Médio 2D por Arquivo e PPEID')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='PPEID')
    plt.tight_layout()
    plt.show()

    # Gráfico de barras do erro médio Z por arquivo (independente do ppeID)
    plt.figure(figsize=(12, 6))
    sns.barplot(data=erro_medio_por_arquivo_ppe, x='arquivo', y='erro_medio_z', hue='ppeID')
    plt.ylabel('Erro Médio Z (m)')
    plt.xlabel('Arquivo')
    plt.title('Erro Médio Z por Arquivo')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
 #   plt.show()

def filtrar_resultados_por_pontos(results_df, pontos_alvo):
    """
    Filtra os resultados para considerar apenas os pontos mais próximos das coordenadas fornecidas.
    pontos_alvo: lista de dicionários [{'x': float, 'y': float}, ...]
    Retorna um DataFrame apenas com os pontos mais próximos de cada coordenada alvo.
    """
    selecionados = []
    for ponto in pontos_alvo:
        menor_dist = float('inf')
        info_mais_proxima = None
        for idx, row in results_df.iterrows():
            x_real = row['x_real']
            y_real = row['y_real']
            dist = np.sqrt((x_real - ponto['x'])**2 + (y_real - ponto['y'])**2)
            if dist < menor_dist:
                menor_dist = dist
                info_mais_proxima = row.copy()
                info_mais_proxima['dist'] = dist
                info_mais_proxima['ponto_alvo_x'] = ponto['x']
                info_mais_proxima['ponto_alvo_y'] = ponto['y']
        if info_mais_proxima is not None:
            selecionados.append(info_mais_proxima)
    return pd.DataFrame(selecionados)

# Exemplo de uso:
pontos_alvo = [
    {'x': -1.14, 'y': 0.39},  # C1P1
    {'x': -2.34, 'y': 0.39},  # C1P2
    {'x': -3.54, 'y': 0.39},  # C1P3
    {'x': -4.74, 'y': 0.39},  # C1P4
    {'x': -5.94, 'y': 0.39},  # C1P5
    {'x': -7.14, 'y': 0.84},  # C4P1
    {'x': -7.14, 'y': 2.04},  # C4P2
    {'x': -7.14, 'y': 3.24},  # C4P3
    {'x': -7.14, 'y': 4.44},  # C4P4
    {'x': -5.94, 'y': 4.44},  # C2P5
    {'x': -4.74, 'y': 4.44},  # C2P4
    {'x': -3.54, 'y': 4.44},  # C2P3
    {'x': -2.34, 'y': 4.44},  # C2P2
    {'x': -1.14, 'y': 4.44},  # C2P1
    {'x': -2.34, 'y': 4.44},  # C2P2 (duplicado)
    {'x': -3.54, 'y': 4.44},  # C2P3 (duplicado)
    {'x': -4.74, 'y': 4.44},  # C2P4 (duplicado)
    {'x': -5.94, 'y': 4.44},  # C2P5 (duplicado)
    {'x': -7.14, 'y': 4.44},  # C4P4 (duplicado)
    {'x': -7.14, 'y': 5.64},  # C4P5
    {'x': -7.14, 'y': 6.84},  # C4P6
    {'x': -5.94, 'y': 6.84},  # C3P5
    {'x': -4.74, 'y': 6.84},  # C3P4
    {'x': -3.54, 'y': 6.84},  # C3P3
    {'x': -2.34, 'y': 6.84},  # C3P2
    {'x': -1.14, 'y': 6.84},  # C3P1
]

resultados_linha_df = pd.DataFrame(resultados_linha)
df_filtrado = filtrar_resultados_por_pontos(resultados_linha_df, pontos_alvo)

def comparar_erro_medio(df_erro, df_filtrado):
    """
    Compara o erro_2d médio entre df_erro e df_filtrado por arquivo e ppeID.
    Retorna a média geral da diferença dos erros.
    """
    media_erro_geral = df_erro.groupby(['arquivo', 'ppeID'])['erro_2d'].mean().reset_index()
    media_erro_filtrado = df_filtrado.groupby(['arquivo', 'ppeID'])['erro_2d'].mean().reset_index()

    comparacao = pd.merge(
        media_erro_geral, media_erro_filtrado,
        on=['arquivo', 'ppeID'],
        suffixes=('_geral', '_filtrado')
    )

    comparacao['diferenca'] = comparacao['erro_2d_geral'] - comparacao['erro_2d_filtrado']
    media_diferenca = comparacao['diferenca'].mean()
    print(f'Média geral da diferença dos erros 2D: {media_diferenca:.4f}')
    return media_diferenca

# Exemplo de uso:
comparar_erro_medio(resultados_linha_df, df_filtrado)