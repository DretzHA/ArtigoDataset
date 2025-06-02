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
    "erro_direcao_por_ancora": True,
    "erro_direcao_por_arquivo": True,
    "heatmap_erro_direcao": True,
    "grafico_espacial_erro_direcao": True
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
                    real_angle = np.arccos(dz / dist)

                elif anchor_id in [1, 2, 3, 4]:

                    ladoh = 'direita' if coords['x'] > x_real else 'esquerda'
                    ladov = 'cima' if coords['y'] > y_real else 'baixo'

                    # Calcular o ângulo entre a âncora e o ponto de teste
                    if ladoh == 'direita':
                        if ladov == 'cima':
                            real_angle = math.pi + math.atan2(dy, dx)
                        else:
                            real_angle = math.pi - math.atan2(dy, dx)
                    elif ladoh == 'esquerda':
                        if ladov == 'cima':
                            real_angle = -math.atan2(dy, dx)
                        else:
                            real_angle = math.atan2(dy, dx)
                    
            else:
                # Default formula
                real_angle = np.arccos(dz / dist)
            
            ppe_data.at[index, f'Real_Elev_{anchor_id}'] = real_angle
    
    return ppe_data

# Função para calcular o erro do ângulo azimute
def calcular_erro_direcao(ppe_data, file_name):
    # Iterar sobre cada âncora para calcular o erro do ângulo azimute
    for anchor_id in anchor_coords.keys():
        if file_name.startswith('ORT'):
            if anchor_id in [5, 6, 7]:
                # Calcular erro linha a linha
                erros = []
                for idx, row in ppe_data.iterrows():
                    real_azim = row.get(f'Real_Dir_{anchor_id}', np.nan)
                    azim = row.get(f'Azim_{anchor_id}', np.nan)
                    if not np.isnan(real_azim) and not np.isnan(azim):
                        erro = np.rad2deg(
                            np.arctan2(
                                np.sin(real_azim - azim),
                                np.cos(real_azim - azim)
                            )
                        )
                        erro = (erro + 180) % 360 - 180
                        erro = abs(erro)
                    else:
                        erro = np.nan
                    erros.append(erro)
                ppe_data[f'Erro_Dir_{anchor_id}'] = erros
            elif anchor_id in [1, 2, 3, 4]:
                # Para ancoras 1,2,3,4, considerar o ângulo de elevação e o azimute linha a linha
                erros = []
                for idx, row in ppe_data.iterrows():
                    azim = row.get(f'Azim_{anchor_id}', np.nan)
                    elev = row.get(f'Elev_{anchor_id}', np.nan)
                    real_azim = row.get(f'Real_Dir_{anchor_id}', np.nan)
                    if not (np.isnan(elev) or np.isnan(azim) or np.isnan(real_azim)):
                        azim_mod = np.abs(np.rad2deg(azim))
                        # Determinar lado para cada ancora
                        lado_medido = 'esquerda' if azim_mod < 90 else 'direita'
                        lado_real = row.get(f'LadoH_{anchor_id}', np.nan)
                        #erro_lado = 0 if lado_medido == lado_real else 90
                        if lado_medido == lado_real:
                            # Calcular erro do ângulo de elevação
                            erro = np.abs(np.rad2deg(np.arctan2(
                                np.sin(real_azim - elev),
                                np.cos(real_azim - elev)
                            )))
                            erro = (erro + 180) % 360 - 180
                            erro = abs(erro)
                        
                        else:
                            erro = (90-math.degrees(row[f'Real_Dir_{anchor_id}']))+(90-math.degrees(elev))
                            erro = (erro + 180) % 360 - 180
                            erro = abs(erro)
                    else:
                        erro = np.nan
                    
                    erros.append(erro)
                ppe_data[f'Erro_Dir_{anchor_id}'] = erros
            else:
                ppe_data[f'Erro_Dir_{anchor_id}'] = np.nan
        else:
            # Calcular erro linha a linha para outros arquivos
            erros = []
            for idx, row in ppe_data.iterrows():
                real_azim = row.get(f'Real_Dir_{anchor_id}', np.nan)
                azim = row.get(f'Azim_{anchor_id}', np.nan)
                if not np.isnan(real_azim) and not np.isnan(azim):
                    erro = np.rad2deg(
                        np.arctan2(
                            np.sin(real_azim - azim),
                            np.cos(real_azim - azim)
                        )
                    )
                    erro = (erro + 180) % 360 - 180
                    erro = abs(erro)
                else:
                    erro = np.nan
                erros.append(erro)
            ppe_data[f'Erro_Dir_{anchor_id}'] = erros
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
                            anchor_x = anchor_coords[anchor_id]['x']
                            anchor_y = anchor_coords[anchor_id]['y']
                            distancia = ((x_real - anchor_x) ** 2 + (y_real - anchor_y) ** 2) ** 0.5
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