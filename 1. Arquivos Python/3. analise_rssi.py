import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.image as mpimg


'''Arquivo para processar e analisar o erro do ângulo azimute'''
# Caminho base para os datasets
# base_path = '0. Dataset Original'
base_path = '0. Dataset com Mascara Virtual'

# Escolher Cenário - calibration | static | mobility
cenario = 'calibration'  # Cenário a ser analisado

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
    "erro_azimute_por_ancora": False,
    "erro_azimute_por_arquivo": False,
    "heatmap_erro_azimute": False,
    "grafico_espacial_erro_azimute": True
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

# Function to calculate the distance between real position and each anchor
def calcular_distancia(ppe_data, anchor_coords):
    for anchor_id, coords in anchor_coords.items():
        ppe_data[f'Dist_Anchor_{anchor_id}'] = np.sqrt(
            (ppe_data['X_real'] - coords['x'])**2 + (ppe_data['Y_real'] - coords['y'])**2 + 0.40**2
        )
        # Set distance to NaN if it exceeds 100
        ppe_data.loc[ppe_data[f'Dist_Anchor_{anchor_id}'] > 100, f'Dist_Anchor_{anchor_id}'] = np.nan
    return ppe_data

# Function to process files and calculate mean RSSI and distances
def processar_rssi_por_arquivo(cenario):
    # Build the path for the selected scenario
    cenario_folder = cenario_to_folder[cenario]
    cenario_path = os.path.join(base_path, cenario_folder)

    # Path to the Data IQ folder
    data_path = os.path.join(cenario_path, 'Data IQ')
    data_files = sorted([f for f in os.listdir(data_path) if f.endswith('.csv')])
    data_files = filtrar_arquivos(data_files)

    results = []
    all_data = []  # List to store data from all files
    for file_name in data_files:
        data_file_path = os.path.join(data_path, file_name)
        data_df = pd.read_csv(data_file_path)

        # Normalize ppeIDs
        data_df = normalizar_ppe_ids(data_df)

        # Calculate distances to each anchor
        data_df = calcular_distancia(data_df, anchor_coords)

        # Append the data with a file identifier
        data_df['file_name'] = file_name
        all_data.append(data_df)

        # Calculate mean RSSI and distances for each anchor
        for anchor_id in range(1, 8):  # Anchors 1 to 7
            if f'RSSI_{anchor_id}' in data_df.columns:
                mean_rssi = data_df[f'RSSI_{anchor_id}'].mean()
                mean_distance = data_df[f'Dist_Anchor_{anchor_id}'].mean()
                results.append({
                    'file_name': file_name,
                    'anchor_id': anchor_id,
                    'mean_rssi': mean_rssi,
                    'mean_distance': mean_distance,
                    'ppe_ids': data_df['ppeID'].unique().tolist()
                })

    # Combine all data into a single DataFrame
    combined_data_df = pd.concat(all_data, ignore_index=True)
    return pd.DataFrame(results), combined_data_df

# Function to generate combined plots for all RSSI points and means for each anchor
def gerar_graficos_rssi_todos_arquivos(results_df, combined_data_df):
    for anchor_id in results_df['anchor_id'].unique():
        anchor_data = results_df[results_df['anchor_id'] == anchor_id]

        plt.figure(figsize=(12, 8))

        # Plot all RSSI points from all files
        for i, row in combined_data_df.iterrows():
            if i % 5 == 0:  # Plot every 5th point
                if not pd.isna(row[f'Dist_Anchor_{anchor_id}']) and not pd.isna(row[f'RSSI_{anchor_id}']):
                    plt.scatter(
                    row[f'Dist_Anchor_{anchor_id}'], 
                    row[f'RSSI_{anchor_id}'], 
                    alpha=0.3, color='blue', label='All Points' if 'All Points' not in plt.gca().get_legend_handles_labels()[1] else ""
                    )

        # Plot mean RSSI values from results_df
        for _, row in anchor_data.iterrows():
            plt.scatter(
                row['mean_distance'], 
                row['mean_rssi'], 
                alpha=1.0, color='red', edgecolor='black', s=100, label='Mean' if 'Mean' not in plt.gca().get_legend_handles_labels()[1] else ""
            )

        plt.title(f'RSSI vs Distance - Anchor {anchor_id}')
        plt.xlabel('Distance to Anchor (meters)')
        plt.ylabel('RSSI (dBm)')
        plt.legend(title='Legend')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# Check if the scenario is valid
if cenario not in cenario_to_folder:
    raise ValueError(f"Cenário inválido: {cenario}. Escolha entre: {', '.join(cenario_to_folder.keys())}")

# Process RSSI data and generate plots for calibration or static scenarios
if cenario in ['calibration', 'static']:
    results_rssi_df, combined_data_df = processar_rssi_por_arquivo(cenario)
    gerar_graficos_rssi_todos_arquivos(results_rssi_df, combined_data_df)


