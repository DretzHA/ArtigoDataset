import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

'''Arquivo para processar e analisar o erro do ângulo azimute'''

# Escolher Cenário - calibration | static | mobility
cenario = 'static'  # Cenário a ser analisado

# Variável para definir se os gráficos e resultados serão feitos por cada tipo de ppe_id ou pela média
por_ppe_id = True  # True para resultados por ppe_id, False para resultados pela média

# Variável para escolher se arquivos específicos serão considerados
considerar_arquivos = {
    "ORT": True,
    "SYLABS": False,
    "UBLOX": False,
    "4T": False,
    "3T": False,
    "OUTROS": False
}

# Variáveis para definir quais gráficos serão plotados
plotar_graficos = {
    "erro_azimute_por_ancora": True,
    "erro_azimute_por_arquivo": True,
    "heatmap_erro_azimute": True
}

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

# Caminho base para os datasets
base_path = '0. Dataset'

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

# Função para calcular o ângulo real (vazia para edição posterior)
def calcular_angulo_real(data_df, anchor_coords):
    pass

# Função para calcular o erro do ângulo azimute (vazia para edição posterior)
def calcular_erro_azimute(data_df, anchor_coords):
    pass

# Função para calcular o erro do ângulo azimute por cenário
def calcular_erro_azimute_por_cenario(cenario):
    # Construir o caminho da pasta correspondente ao cenário
    cenario_folder = cenario_to_folder[cenario]
    cenario_path = os.path.join(base_path, cenario_folder)

    # Caminho da pasta Data IQ
    data_path = os.path.join(cenario_path, 'Data IQ')
    data_files = sorted([f for f in os.listdir(data_path) if f.endswith('.csv')])
    data_files = filtrar_arquivos(data_files)

    results = []
    for file_name in data_files:
        data_file_path = os.path.join(data_path, file_name)
        data_df = pd.read_csv(data_file_path)

        # Normalizar os ppeIDs
        data_df = normalizar_ppe_ids(data_df)

        # Calcular o ângulo real e o erro do azimute
        calcular_angulo_real(data_df, anchor_mapping)
        calcular_erro_azimute(data_df, anchor_mapping)

        # Processar resultados
        for ppe_id in data_df['ppeID'].unique():
            data_filtered = data_df[data_df['ppeID'] == ppe_id]
            for anchor, anchor_id in anchor_mapping.items():
                erro_azimute = data_filtered[f'Erro_Azim_{anchor_id}'].mean()
                results.append({
                    'file_name': file_name,
                    'ppe_id': ppe_id,
                    'anchor': anchor,
                    'erro_azimute': erro_azimute
                })

    results_df = pd.DataFrame(results)
    return results_df

# Função para gerar gráficos com base no controle por_ppe_id
def gerar_graficos(results_df):
    if por_ppe_id:
        # Gerar gráficos por ppe_id
        for ppe_id in results_df['ppe_id'].unique():
            ppe_results = results_df[results_df['ppe_id'] == ppe_id]
            erro_data = ppe_results.groupby('anchor')['erro_azimute'].mean()
            title = f'Erro do Ângulo Azimute por Âncora - PPE_ID: {ppe_id}'
            erro_data.plot(kind='bar', figsize=(10, 6), title=title)
            plt.xlabel('Âncora')
            plt.ylabel('Erro Médio do Ângulo Azimute (graus)')
            plt.show()
    else:
        # Gerar gráficos pela média
        erro_data = results_df.groupby('anchor')['erro_azimute'].mean()
        title = 'Erro Médio do Ângulo Azimute por Âncora'
        erro_data.plot(kind='bar', figsize=(10, 6), title=title)
        plt.xlabel('Âncora')
        plt.ylabel('Erro Médio do Ângulo Azimute (graus)')
        plt.show()

# Função para gerar heatmap do erro do ângulo azimute
def gerar_heatmap(results_df):
    heatmap_data = results_df.pivot_table(
        values='erro_azimute',
        index='file_name',
        columns='anchor',
        aggfunc='mean'
    )
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Erro Médio (graus)'})
    plt.title('Heatmap do Erro do Ângulo Azimute por Arquivo e Âncora')
    plt.xlabel('Âncora')
    plt.ylabel('Arquivo')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Verificar se o cenário é válido
if cenario not in cenario_to_folder:
    raise ValueError(f"Cenário inválido: {cenario}. Escolha entre: {', '.join(cenario_to_folder.keys())}")

# Calcular o erro do ângulo azimute
results_erro_azimute_df = calcular_erro_azimute_por_cenario(cenario)

# Gerar gráficos
if plotar_graficos["erro_azimute_por_ancora"]:
    gerar_graficos(results_erro_azimute_df)

if plotar_graficos["heatmap_erro_azimute"]:
    gerar_heatmap(results_erro_azimute_df)