import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.image as mpimg
import math
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

'''Arquivo para processar e analisar o erro do ângulo azimute'''
# Caminho base para os datasets
# base_path = '0. Dataset Original'
base_path = '0. Dataset com Mascara Virtual'
#base_path = '0. Dataset Teste'

# Escolher Cenário - calibration | static | mobility
cenario = 'mobility'  # Cenário a ser analisado

# Variável para definir se os gráficos e resultados serão feitos por cada tipo de ppe_id ou pela média
por_ppe_id = True  # True para resultados por ppe_id, False para resultados pela média

# Variável para escolher se arquivos específicos serão considerados
considerar_arquivos = {
    "ORT": False,
    "SYLABS": False,
    "UBLOX": False,
    "4T": True,
    "3T": False,
    "OUTROS": False
}

# Variáveis para definir quais gráficos serão plotados
plotar_graficos = {
    "erro_direcao_por_ancora": False,
    "heatmap_erro_direcao": False,
    "grafico_espacial_erro_direcao": False
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

# Função para calcular o ângulo real (vazia para edição posterior)
def calcular_angulo_real(ppe_data, anchor_coords, file_name):
    # Extract real-world position
    for index, row in ppe_data.iterrows():
        x_real, y_real = row["X_real"], row["Y_real"]
        for anchor_id, coords in anchor_coords.items():
            if file_name.startswith('ORT'):
                if anchor_id in [5, 6, 7]:
                    real_angle = np.arctan2(coords['y'] - y_real, x_real - coords['x'])
                    ladoh = np.nan
                    ladov = np.nan
                elif anchor_id in [1, 2, 3, 4]:
                    # Novo cálculo: ângulo entre 0 e 90, 90° reto para a âncora, 0° extremidade
                    # Vetor da ancora até o ponto
                    dx = x_real - coords['x']
                    dy = y_real - coords['y']
                    
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
                real_angle = np.arctan2(coords['y'] - y_real, x_real - coords['x'])
                ladoh = np.nan
                ladov = np.nan
            
            ppe_data.at[index, f'Real_Dir_{anchor_id}'] = real_angle
            ppe_data.at[index, f'LadoH_{anchor_id}'] = ladoh
            ppe_data.at[index, f'LadoV_{anchor_id}'] = ladov
    
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
                    # if erro >=90:
                    #     breakpoint()
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
                                'erro_direcao': row[f'Erro_Dir_{anchor_id}'],
                            })
                    else: #mobility
                        results.append({
                                'file_name': file_name,
                                'ppe_id': ppe_id,
                                'anchor': anchor,
                                'erro_direcao': row[f'Erro_Dir_{anchor_id}'],
                            })
                        
    results_df = pd.DataFrame(results)
    results_df['anchor'] = results_df['anchor'].map(anchor_mapping)

    return results_df

# Função para gerar gráficos com base no controle por_ppe_id
def gerar_graficos(results_df):
    # Mapeamento descritivo para âncoras e EPIs
    # Gerar gráficos por ppe_id
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        erro_data = ppe_results.groupby('anchor')['erro_direcao'].mean()
        title = f'Direction Angle Error per Anchor - PPE: {ppe_id}'
        erro_data.plot(kind='bar', figsize=(10, 6), title=title)
        plt.xlabel('Anchor')
        plt.ylabel('Mean Direction Angle Error (degrees)')
        plt.xticks(rotation=45)
        #plt.show()

# Função para gerar heatmap do erro do ângulo azimute
def gerar_heatmap(results_df):
    # Mapeamento descritivo para âncoras
    
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        heatmap_data = ppe_results.pivot_table(
            values='erro_direcao',
            index='file_name',
            columns='anchor',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Mean Error (degrees)'})
        plt.title(f'Heatmap of Direction Angle Error by File and Anchor - PPE: {ppe_id}')
        plt.xlabel('Anchor')
        plt.ylabel('File')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

def plot_heatmap_ancora(results_df, data_path, radius=0.85, grid_res=120):
    anchors = list(anchor_coords.keys())
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        for anchor in anchors:
            fig, ax = plt.subplots(figsize=(12, 10))
            coords = anchor_coords[anchor]

            # Filtrar resultados para esta ancora e ppe_id
            anchor_results = ppe_results[ppe_results['anchor'] == anchor]
            # Calcular a média do erro de azimute para cada âncora e posição
            mean_results = anchor_results.groupby(['anchor', 'file_name', 'ppe_id']).agg({'erro_direcao': 'mean'}).reset_index()

            xs, ys, errors = [], [], []
            for _, row in mean_results.iterrows():
                file_name = row['file_name']
                data_file_path = os.path.join(data_path, file_name)
                data_df = pd.read_csv(data_file_path)
                data_df = normalizar_ppe_ids(data_df)
                try:
                    test_position = data_df[data_df['ppeID'] == row['ppe_id']][['X_real', 'Y_real']].iloc[0]
                    x_real, y_real = test_position['X_real'], test_position['Y_real']
                    xs.append(x_real)
                    ys.append(y_real)
                    errors.append(row['erro_direcao'])
                except Exception:
                    continue

            if len(xs) < 3:
                ax.set_title(f"Anchor A{anchor} (poucos pontos)")
                ax.imshow(img, extent=[0, -10.70, 8.8, 0], alpha=0.5)
                ax.scatter(coords['x'], coords['y'], color='red', marker='s', s=100, label=f'Anchor A{anchor}')
                plt.tight_layout()
                plt.suptitle(f'Heatmap Espacial por Âncora - PPE_ID: {ppe_id}', fontsize=16)
                plt.show()
                continue

            xs, ys, errors = np.array(xs), np.array(ys), np.array(errors)
            xi = np.linspace(xs.min(), xs.max(), grid_res)
            yi = np.linspace(ys.min(), ys.max(), grid_res)
            xi, yi = np.meshgrid(xi, yi)
            zi = griddata((xs, ys), errors, (xi, yi), method='linear')

            # Máscara para interpolar só perto dos pontos conhecidos
            tree = cKDTree(np.c_[xs, ys])
            dist, _ = tree.query(np.c_[xi.ravel(), yi.ravel()])
            mask = dist.reshape(xi.shape) <= radius
            zi_masked = np.where(mask, zi, np.nan)

            ax.imshow(img, extent=[0, -10.70, 8.8, 0], alpha=0.5)
            pcm = ax.pcolormesh(xi, yi, zi_masked, cmap='coolwarm', shading='auto', alpha=0.7, vmin=0, vmax=50)
            ax.scatter(xs, ys, c=errors, cmap='coolwarm', edgecolor='k', s=60, vmin=0, vmax=50)
            ax.scatter(coords['x'], coords['y'], color='red', marker='s', s=100, label=f'Anchor A{anchor}')
            ax.text(coords['x'], coords['y'] + 0.3, f'A{anchor}', fontsize=10, color='red', ha='center')
            #ax.set_title(f"Heatmap Anchor A{anchor} (Erro Azimute)")
            ax.set_xlabel("X-axis (meters)", fontsize=16)
            ax.set_ylabel("Y-axis (meters)", fontsize=16)
            # Ajustar a barra de cor para ocupar toda a altura do eixo e aumentar o tamanho da fonte e escala
            # Ajustar a altura do colorbar usando shrink e corrigir a formatação dos ticks
            cbar = fig.colorbar(pcm, ax=ax, orientation='vertical', pad=0.02, aspect=30, shrink=0.75)
            cbar.set_label('Azimuth Error (Degrees)', fontsize=16)
            cbar.ax.tick_params(labelsize=14)
            # Remover notação científica e garantir escala correta
            cbar.ax.yaxis.offsetText.set_visible(False)
            cbar.formatter.set_useOffset(False)
            cbar.formatter.set_scientific(False)
            cbar.update_ticks()
            plt.tight_layout()
            ax = plt.gca()
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            #plt.suptitle(f'Heatmap Espacial por Âncora - PPE_ID: {ppe_id}', fontsize=16)
            #plt.savefig(f'/home/andrey/Desktop/heatmap_az_0{anchor}_ort_{ppe_id}_v2.eps', format='eps', dpi=20)
            plt.show()


# Função para gerar gráfico espacial do erro médio 4 ângulo azimute
def gerar_grafico_espacial_erro_direcao(results_df, data_path):

    # Gerar gráficos espaciais por ppe_id
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        
        # Calcular a média do erro de azimute para cada âncora e posição
        mean_results = ppe_results.groupby(['anchor', 'file_name']).agg({'erro_direcao': 'mean'}).reset_index()
        
        # Número de subplots por figura
        subplots_per_figure = 4  # Ajuste conforme necessário
        num_figures = (len(anchor_coords) + subplots_per_figure - 1) // subplots_per_figure  # Número total de figuras

        # Iterar sobre as figuras
        for fig_idx in range(num_figures):
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            # Iterar sobre as âncoras para a figura atual
            for subplot_idx in range(subplots_per_figure):
                anchor_idx = fig_idx * subplots_per_figure + subplot_idx
                if anchor_idx >= len(anchor_coords):
                    break  # Não há mais âncoras para plotar
                
                anchor, coords = list(anchor_coords.items())[anchor_idx]
                ax = axes[subplot_idx]
                ax.imshow(img, extent=[0, -10.70, 8.8, 0])  # Ajustar os limites do eixo com base no sistema fornecido
                
                # Plotar a âncora
                ax.scatter(coords['x'], coords['y'], color='red', marker='s', s=100, label=f'Anchor A{anchor}')
                ax.text(coords['x'], coords['y'] + 0.3, f'A{anchor}', fontsize=10, color='red', ha='center')
                
                # Filtrar os resultados para the âncora atual
                anchor_results = mean_results[mean_results['anchor'] == anchor]
                
                # Plotar as posições dos testes e sobrepor os erros médios de azimute
                #for _, row in anchor_results.iterrows():
                for file_name in anchor_results['file_name'].unique():
                    data_file_path = os.path.join(data_path, file_name)
                    data_df = pd.read_csv(data_file_path)
                    # Normalizar os ppeIDs
                    data_df = normalizar_ppe_ids(data_df)
                    # Obter a posição média do teste
                    test_position = data_df[data_df['ppeID'] == ppe_id][['X_real', 'Y_real']].iloc[0]
                    x_real, y_real = test_position['X_real'], test_position['Y_real']
                    
                    # Obter o erro médio do ângulo azimute
                    erro_direcao = anchor_results[anchor_results['file_name'] == file_name]['erro_direcao'].iloc[0]
                    
                    # Plotar a posição do teste
                    ax.scatter(x_real, y_real, color='blue', marker='o', s=50, alpha=0.6)
                    
                    # Adicionar texto com o erro médio do ângulo azimute
                    ax.text(x_real, y_real - 0.2, f'{erro_direcao:.1f}°', fontsize=8, color='blue', ha='center')
                
                # Configurações do subplot
                ax.set_title(f"Anchor A{anchor}")
                ax.set_xlabel("X-axis (meters)")
                ax.set_ylabel("Y-axis (meters)")
            
            # Remover subplots extras (se houver)
            for subplot_idx in range(subplots_per_figure, len(axes)):
                fig.delaxes(axes[subplot_idx])
            
            # Ajustar layout e exibir a figura
            plt.tight_layout()
            if ppe_id:
                plt.suptitle(f'Spatial Plot - PPE: {ppe_id}', fontsize=12)
            plt.show()

from matplotlib.animation import PillowWriter

# Verificar se o cenário é válido
if cenario not in cenario_to_folder:
    raise ValueError(f"Cenário inválido: {cenario}. Escolha entre: {', '.join(cenario_to_folder.keys())}")

# Calcular o erro do ângulo azimute
results_erro_direcao_df = calcular_erro_direcao_por_cenario(cenario)

# Gerar gráficos
if plotar_graficos["erro_direcao_por_ancora"]:
    gerar_graficos(results_erro_direcao_df)

if plotar_graficos["heatmap_erro_direcao"]:
    gerar_heatmap(results_erro_direcao_df)

# Gerar gráfico espacial do erro médio do ângulo azimute
if plotar_graficos["grafico_espacial_erro_direcao"]:
    if cenario in ['calibration', 'static']:
        #gerar_grafico_espacial_erro_direcao(results_erro_direcao_df, os.path.join(base_path, cenario_to_folder[cenario], 'Data IQ'))
        # Chamar o heatmap de erro de azimute por ancora
        plot_heatmap_ancora(results_erro_direcao_df, os.path.join(base_path, cenario_to_folder[cenario], 'Data IQ'))
    elif cenario == 'mobility':
        for ppe_id in results_erro_direcao_df['ppe_id'].unique():
            ppe_results = results_erro_direcao_df[results_erro_direcao_df['ppe_id'] == ppe_id]
            
            for file_name in ppe_results['file_name'].unique():
                gif_frames = []  # Lista para armazenar os frames do GIF para o arquivo atual
                file_results = ppe_results[ppe_results['file_name'] == file_name]
                data_file_path = os.path.join(base_path, cenario_to_folder[cenario], 'Data IQ', file_name)
                data_df = pd.read_csv(data_file_path)
                data_df = normalizar_ppe_ids(data_df)
                data_df = calcular_angulo_real(data_df, anchor_coords, file_name)
                k=0
                # Iterar sobre cada linha do data_df para plotar as linhas de azimute real e medido
                for _, data_row in data_df[data_df['ppeID'] == ppe_id].iterrows():
                    k += 1
                    x_real, y_real = data_row['X_real'], data_row['Y_real']

                    fig, ax = plt.subplots(figsize=(10, 8))
                    ax.imshow(img, extent=[0, -10.70, 8.8, 0])  # Ajustar os limites do eixo com base no sistema fornecido
                
                    # Plotar âncoras
                    for anchor_id, coords in anchor_coords.items():
                        ax.scatter(coords['x'], coords['y'], color='red', marker='s', s=100, label=f'Anchor A{anchor_id}')
                        ax.text(coords['x'], coords['y'] + 0.3, f'A{anchor_id}', fontsize=10, color='red', ha='center')
                    
                    for anchor_id, coords in anchor_coords.items():
                        # Verificar se o valor medido do azimute existe antes de plotar
                        if not np.isnan(data_row.get(f'Azim_{anchor_id}', np.nan)):
                            # Linha do azimute real
                            real_azimuth_x = [x_real, coords['x']]
                            real_azimuth_y = [y_real, coords['y']]
                            ax.plot(
                                real_azimuth_x, real_azimuth_y, 
                                color='blue', linestyle='--', linewidth=2, alpha=0.8, 
                                label='Real Azimuth' if anchor_id == 1 else ""
                            )


                            # Linha do azimute medido saindo de cada âncora com comprimento arbitrário
                            '''Plotando usando angulo calculo par conferencia em arquivos com todas em pe'''
                            # real_azimuth = data_row[f'Real_Dir_{anchor_id}']
                            # azimuth_length = 10  # Comprimento arbitrário da linha do azimute
                            # measured_azimuth_x = [
                            #     coords['x'],
                            #     coords['x'] + azimuth_length * np.cos(data_row[f'Real_Dir_{anchor_id}'])
                            # ]
                            # measured_azimuth_y = [
                            #     coords['y'],
                            #     coords['y'] - azimuth_length * np.sin(data_row[f'Real_Dir_{anchor_id}'])
                            # ]
                            # ax.plot(
                            #     measured_azimuth_x, measured_azimuth_y, 
                            #     color='blue', linestyle='--', linewidth=2, alpha=0.8, 
                            #     label='Azimute Real' if anchor_id == 1 else ""
                            # )

                            # Para arquivos ORT e ancoras 1-4, usar lado e elevação
                            if file_name.startswith('ORT') and anchor_id in [1, 2, 3, 4]:
                                elev = data_row.get(f'Elev_{anchor_id}', np.nan)
                                real_azimuth = data_row[f'Real_Dir_{anchor_id}']
                                if not np.isnan(elev):
                                    # Determinar lado (esquerda/direita) a partir do azimute medido
                                    azim = data_row.get(f'Azim_{anchor_id}', np.nan)
                                    azim_mod = np.abs(np.rad2deg(azim))
                                    lado = 'esquerda' if azim_mod < 90 else 'direita'
                                    # Definir o sentido do vetor a partir da ancora
                                    azimuth_length = 10
                                    # Para lado esquerda, ângulo é elev; para direita, é -elev
                                    #angle = elev if lado == 'esquerda' else 180-elev
                                    if lado == 'direita':
                                        measured_azimuth_x = [
                                            coords['x'],
                                            coords['x'] - azimuth_length * np.cos(elev)
                                        ]
                                        # real_measured_azimuth_x = [
                                        #     coords['x'],
                                        #     coords['x'] - azimuth_length * np.cos(real_azimuth)
                                        # ]
                                    else:
                                        measured_azimuth_x = [
                                            coords['x'],
                                            coords['x'] + azimuth_length * np.cos(elev)
                                        ]
                                        # real_measured_azimuth_x = [
                                        #     coords['x'],
                                        #     coords['x'] + azimuth_length * np.cos(real_azimuth)
                                        # ]
                                    if anchor_id in [2,3]:
                                        measured_azimuth_y = [
                                            coords['y'],
                                            coords['y'] - azimuth_length * np.sin(elev)
                                        ]
                                        # real_measured_azimuth_y = [
                                        #     coords['y'],
                                        #     coords['y'] - azimuth_length * np.sin(real_azimuth)
                                        # ]
                                    else:
                                        measured_azimuth_y = [
                                            coords['y'],
                                            coords['y'] + azimuth_length * np.sin(elev)
                                        ]
                                        # real_measured_azimuth_y = [
                                        #     coords['y'],
                                        #     coords['y'] + azimuth_length * np.sin(real_azimuth)
                                        # ]
                                    ax.plot(
                                        measured_azimuth_x, measured_azimuth_y, 
                                        color='green', linestyle='-', linewidth=2, alpha=0.8, 
                                        label='Measured Azimuth' if anchor_id == 1 else ""
                                    )
                                    # ax.plot(
                                    # real_measured_azimuth_x, real_measured_azimuth_y, 
                                    # color='blue', linestyle='--', linewidth=2, alpha=0.8, 
                                    # label='Azimute Real' if anchor_id == 1 else ""
                                    # )
                            else:
                                # Linha do azimute medido saindo de cada âncora com comprimento arbitrário
                                azimuth_length = 10  # Comprimento arbitrário da linha do azimute
                                measured_azimuth_x = [
                                    coords['x'],
                                    coords['x'] + azimuth_length * np.cos(data_row[f'Azim_{anchor_id}'])
                                ]
                                measured_azimuth_y = [
                                    coords['y'],
                                    coords['y'] - azimuth_length * np.sin(data_row[f'Azim_{anchor_id}'])
                                ]
                                ax.plot(
                                    measured_azimuth_x, measured_azimuth_y, 
                                    color='green', linestyle='-', linewidth=2, alpha=0.8, 
                                    label='Measured Azimuth' if anchor_id == 1 else ""
                                )
                
                    # Configurar título e layout
                    #ax.set_title(f'Gráfico Espacial - PPE_ID: {ppe_id}, Arquivo: {file_name}, Posição: ({x_real:.2f}, {y_real:.2f})')
                    ax.set_xlabel("X-axis (meters)", fontsize=16)
                    ax.set_ylabel("Y-axis (meters)", fontsize=16)
                    ax.set_xlim((0, -10.70))   
                    ax.set_ylim(8.8, 0)     
                    ax.tick_params(axis='x', labelsize=16)
                    ax.tick_params(axis='y', labelsize=16)
                    handles, labels = ax.get_legend_handles_labels()
                    # Filtrar apenas as legendas de 'Measured Azimuth' e 'Real Azimuth'
                    legend_items = [(h, l) for h, l in zip(handles, labels) if l in ['Measured Azimuth', 'Real Azimuth']]
                    # if legend_items:
                    #     ax.legend(*zip(*legend_items), fontsize=14, loc='upper right')
                    # plt.tight_layout()
                    # print(file_name, k, ppe_id)
                    # if file_name == 'MOV_MID_4T_V1_data.csv' and ppe_id == 'Capacete':
                    #     #if k == 4 or k == 10 or k ==17 or k == 39 or k ==53 or k == 61:
                    #     if k ==53 or k == 61:
                    #         plt.savefig(f'/home/andrey/Desktop/lines_4t_{k}_v2.eps', format='eps', dpi=20)
                    # #Exibir cada figura gerada
                    plt.show()
                    # plt.close(fig)

                #     # Salvar o frame na lista
                #     fig.canvas.draw()
                #     frame = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
                #     frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                #     gif_frames.append(frame)
                #     plt.close(fig)

                # # Criar o GIF para o arquivo atual usando Pillow
                # from PIL import Image
                # gif_images = [Image.fromarray(frame) for frame in gif_frames]
                # gif_images[0].save(
                #     f'grafico_espacial_{file_name}.gif', 
                #     save_all=True, 
                #     append_images=gif_images[1:], 
                #     duration=500, 
                #     loop=0
                # )
