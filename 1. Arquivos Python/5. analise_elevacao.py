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
cenario = 'static'  # Cenário a ser analisado

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
    "erro_direcao_por_ancora": True,
    "erro_direcao_por_arquivo": True,
    "heatmap_erro_direcao": True,
    "grafico_espacial_erro_direcao": True,
    "histograma_erro_elevacao": True  # Adicionado controle para histograma
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
    1: {'x': -1.00, 'y': 7.83, 'z': 2.41},  # A01
    2: {'x': -0.96, 'y': 1.22, 'z': 2.41},  # A02
    3: {'x': -5.81, 'y': 7.85, 'z': 2.41},  # A03
    4: {'x': -3.50, 'y': 4.60, 'z': 2.41},  # A04
    5: {'x': -5.76, 'y': 4.64, 'z': 2.41},  # A05
    6: {'x': -0.98, 'y': 4.54, 'z': 2.41},  # A06
    7: {'x': -5.85, 'y': 1.21, 'z': 2.41},  # A07
}

# Atualizar coordenadas das âncoras se ORT estiver habilitado
if considerar_arquivos["ORT"]:
    anchor_coords.update({
        1: {'x': -0.84, 'y': 0.54, 'z': 1.95},  # A01
        2: {'x': -7.14, 'y': 7.74, 'z': 1.95},  # A02
        3: {'x': -1.14, 'y': 7.74, 'z': 1.95},  # A03
        4: {'x': -7.74, 'y': 0.84, 'z': 1.95},  # A04
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

#Função para calcular o ângulo real (vazia para edição posterior)
def calcular_angulo_real(ppe_data, anchor_coords, file_name):
    # Extract real-world position
    for index, row in ppe_data.iterrows():
        x_real, y_real, z_real = row["X_real"], row["Y_real"], row["Z_real"]
        for anchor_id, coords in anchor_coords.items():
            dx = x_real - coords['x']
            dy = y_real - coords['y']
            dz = z_real - coords['z']
            dist = np.sqrt(dx**2 + dy**2 + dz**2)
            if file_name.startswith('ORT'):
                if anchor_id in [5, 6, 7]:
                    real_angle = abs(np.arcsin(dz / dist))

                elif anchor_id in [1, 2, 3, 4]:

                    real_angle= np.nan                    
            else:
                # Default formula
                real_angle = abs(np.arcsin(dz / dist))
            
            ppe_data.at[index, f'Real_Elev_{anchor_id}'] = real_angle
    
    return ppe_data

# Função para calcular o erro do ângulo azimute
def calcular_erro_direcao(ppe_data, file_name):
    # Para cada âncora, calcular o erro em graus entre Elev_{anchor_id} e Real_Elev_{anchor_id}
    for anchor_id in anchor_coords.keys():
        elev_col = f'Elev_{anchor_id}'
        real_elev_col = f'Real_Elev_{anchor_id}'
        erro_col = f'Erro_Elev_{anchor_id}'
        if elev_col in ppe_data.columns and real_elev_col in ppe_data.columns:
            # Calcula diferença em radianos, converte para graus
            erro = np.degrees(ppe_data[elev_col] - ppe_data[real_elev_col])
            ppe_data[erro_col] = abs(erro)
        else:
            # Se não existir, preenche com NaN
            ppe_data[erro_col] = np.nan
    return ppe_data

# Função para calcular o erro do ângulo azimute por cenário
def calcular_erro_direcao_por_cenario(cenario):
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

        # Iterar por ppe_id
        for ppe_id in data_df['ppeID'].unique():
            ppe_data = data_df[data_df['ppeID'] == ppe_id].copy()
            # Remover linhas onde X_real ou Y_real é igual a -100
            ppe_data = ppe_data[~((ppe_data['X_real'] == -100) | (ppe_data['Y_real'] == -100))]

            # Calcular o ângulo real e o erro do azimute
            ppe_data = calcular_angulo_real(ppe_data, anchor_coords, file_name)
            ppe_data = calcular_erro_direcao(ppe_data, file_name)

            # Salvar todos os erros de ângulo azimute
            for _, row in ppe_data.iterrows():
                for anchor, anchor_id in anchor_mapping.items():
                    if cenario in ['static', 'calibration']:
                        if 'X_real' in ppe_data.columns and 'Y_real' in ppe_data.columns:
                            x_real = ppe_data['X_real'].iloc[0]
                            y_real = ppe_data['Y_real'].iloc[0]
                            z_real = ppe_data['Z_real'].iloc[0]
                            anchor_x = anchor_coords[anchor_id]['x']
                            anchor_y = anchor_coords[anchor_id]['y']
                            anchor_z = anchor_coords[anchor_id]['z']
                            distancia = ((x_real - anchor_x) ** 2 + (y_real - anchor_y) ** 2 + (z_real - anchor_z) ** 2) ** 0.5
                        else:
                            distancia = None

                        if distancia is not None and distancia > 0.5:
                            results.append({
                                'file_name': file_name,
                                'ppe_id': ppe_id,
                                'anchor': anchor,
                                'erro_elevacao': row[f'Erro_Elev_{anchor_id}'],
                            })
                    else: #mobility
                        results.append({
                                'file_name': file_name,
                                'ppe_id': ppe_id,
                                'anchor': anchor,
                                'erro_elevacao': row[f'Erro_Elev_{anchor_id}'],
                            })
                        
    results_df = pd.DataFrame(results)
    results_df['anchor'] = results_df['anchor'].map(anchor_mapping)

    return results_df

results_erro_direcao_df = calcular_erro_direcao_por_cenario(cenario)
print()

def plotar_histogramas_erro_elevacao(results_df):
    """
    Plota histogramas do erro do azimute para cada ancora.
    """
    for anchor in sorted(results_df['anchor'].unique()):
        plt.figure(figsize=(8, 5))
        dados = results_df[results_df['anchor'] == anchor]['erro_elevacao'].dropna()
        plt.hist(dados, bins=200, color='orchid', edgecolor='black', alpha=0.8)
        plt.title(f'Histogram of Elevation Error - Anchor {anchor}')
        plt.xlabel('Elevation Error (degrees)')
        plt.ylabel('Count')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

# Gerar histograma do erro do azimute por ancora
if plotar_graficos.get("histograma_erro_elevacao", False):
    plotar_histogramas_erro_elevacao(results_erro_direcao_df)