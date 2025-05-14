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

# Função para calcular o ângulo real (vazia para edição posterior)
def calcular_angulo_real(ppe_data, anchor_coords):

    # Extract real-world position
    for index, row in ppe_data.iterrows():
        x_real, y_real = row["X_real"], row["Y_real"]
        for anchor_id, coords in anchor_coords.items():
            real_azimuth = np.arctan2(coords['y'] - y_real, x_real - coords['x'])
            ppe_data.at[index, f'Real_Azim_{anchor_id}'] = real_azimuth

    # # Iterate through each anchor to calculate the real azimuth
    # for anchor_id, coords in anchor_coords.items():
    #     real_azimuth = np.arctan2(coords['y'] - y_real, x_real - coords['x'])
    #     # Save the calculated real azimuth in the dataframe
    #     ppe_data[f'Real_Azim_{anchor_id}'] = real_azimuth
    
    return ppe_data

# Função para calcular o erro do ângulo azimute
def calcular_erro_azimute(ppe_data):
    # Iterar sobre cada âncora para calcular o erro do ângulo azimute
    for anchor_id in anchor_coords.keys():
        # Calcular a diferença angular entre o ângulo real e o ângulo medido
        ppe_data[f'Erro_Azim_{anchor_id}'] = np.rad2deg(
            np.arctan2(
                np.sin(ppe_data[f'Real_Azim_{anchor_id}'] - ppe_data[f'Azim_{anchor_id}']),
                np.cos(ppe_data[f'Real_Azim_{anchor_id}'] - ppe_data[f'Azim_{anchor_id}'])
            )
        )
        # Garantir que o erro esteja no intervalo [-180, 180]
        ppe_data[f'Erro_Azim_{anchor_id}'] = (ppe_data[f'Erro_Azim_{anchor_id}'] + 180) % 360 - 180
        ppe_data[f'Erro_Azim_{anchor_id}'] = abs(ppe_data[f'Erro_Azim_{anchor_id}'])
    
    return ppe_data

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

        # Iterar por ppe_id
        for ppe_id in data_df['ppeID'].unique():
            ppe_data = data_df[data_df['ppeID'] == ppe_id].copy()

            # Calcular o ângulo real e o erro do azimute
            ppe_data = calcular_angulo_real(ppe_data, anchor_coords)
            ppe_data = calcular_erro_azimute(ppe_data)

            # Salvar todos os erros de ângulo azimute
            for _, row in ppe_data.iterrows():
                for anchor, anchor_id in anchor_mapping.items():
                    results.append({
                        'file_name': file_name,
                        'ppe_id': ppe_id,
                        'anchor': anchor,
                        'erro_azimute': row[f'Erro_Azim_{anchor_id}'],
                    })

    results_df = pd.DataFrame(results)
    results_df['anchor'] = results_df['anchor'].map(anchor_mapping)

    return results_df

# Função para gerar gráficos com base no controle por_ppe_id
def gerar_graficos(results_df):
    # Mapeamento descritivo para âncoras e EPIs
   
    if por_ppe_id:
        # Gerar gráficos por ppe_id
        for ppe_id in results_df['ppe_id'].unique():
            ppe_results = results_df[results_df['ppe_id'] == ppe_id]
            erro_data = ppe_results.groupby('anchor')['erro_azimute'].mean()
            title = f'Erro do Ângulo Azimute por Âncora - EPI: {ppe_id}'
            erro_data.plot(kind='bar', figsize=(10, 6), title=title)
            plt.xlabel('Âncora')
            plt.ylabel('Erro Médio do Ângulo Azimute (graus)')
            plt.xticks(rotation=45)
            plt.show()
    else:
        # Gerar gráficos pela média
        erro_data = results_df.groupby('anchor')['erro_azimute'].mean()
        title = 'Erro Médio do Ângulo Azimute por Âncora'
        erro_data.plot(kind='bar', figsize=(10, 6), title=title)
        plt.xlabel('Âncora')
        plt.ylabel('Erro Médio do Ângulo Azimute (graus)')
        plt.xticks(rotation=45)
        plt.show()

# Função para gerar heatmap do erro do ângulo azimute
def gerar_heatmap(results_df):
    # Mapeamento descritivo para âncoras
    
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        heatmap_data = ppe_results.pivot_table(
            values='erro_azimute',
            index='file_name',
            columns='anchor',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Erro Médio (graus)'})
        plt.title(f'Heatmap do Erro do Ângulo Azimute por Arquivo e Âncora - EPI: {ppe_id}')
        plt.xlabel('Âncora')
        plt.ylabel('Arquivo')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

# Função para gerar gráfico espacial do erro médio do ângulo azimute
def gerar_grafico_espacial_erro_azimute(results_df, data_path):

    if por_ppe_id:
        # Gerar gráficos espaciais por ppe_id
        for ppe_id in results_df['ppe_id'].unique():
            ppe_results = results_df[results_df['ppe_id'] == ppe_id]
            
            # Calcular a média do erro de azimute para cada âncora e posição
            mean_results = ppe_results.groupby(['anchor', 'file_name']).agg({'erro_azimute': 'mean'}).reset_index()
            
            # Número de subplots por figura
            subplots_per_figure = 4  # Ajuste conforme necessário
            num_figures = (len(anchor_coords) + subplots_per_figure - 1) // subplots_per_figure  # Número total de figuras

            # Iterar sobre as figuras
            for fig_idx in range(num_figures):
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))  # 2x2 grid para cada figura
                axes = axes.flatten()  # Transformar em uma lista para fácil iteração
                
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
                    
                    # Filtrar os resultados para a âncora atual
                    anchor_results = mean_results[mean_results['anchor'] == anchor]
                    
                    # Plotar as posições dos testes e sobrepor os erros médios de azimute
                    for _, row in anchor_results.iterrows():
                        file_name = row['file_name']
                        data_file_path = os.path.join(data_path, file_name)
                        data_df = pd.read_csv(data_file_path)
                        # Normalizar os ppeIDs
                        data_df = normalizar_ppe_ids(data_df)
                        # Obter a posição média do teste
                        test_position = data_df[data_df['ppeID'] == ppe_id][['X_real', 'Y_real']].iloc[0]
                        x_real, y_real = test_position['X_real'], test_position['Y_real']
                        
                        # Obter o erro médio do ângulo azimute
                        erro_azimute = row['erro_azimute']
                        
                        # Plotar a posição do teste
                        ax.scatter(x_real, y_real, color='blue', marker='o', s=50, alpha=0.6)
                        
                        # Adicionar texto com o erro médio do ângulo azimute
                        ax.text(x_real, y_real - 0.2, f'{erro_azimute:.1f}°', fontsize=8, color='blue', ha='center')
                    
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
                    plt.suptitle(f'Gráfico Espacial - PPE_ID: {ppe_id}', fontsize=12)
                plt.show()

from matplotlib.animation import PillowWriter

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

# Gerar gráfico espacial do erro médio do ângulo azimute
if plotar_graficos["grafico_espacial_erro_azimute"]:
    if cenario in ['calibration', 'static']:
        gerar_grafico_espacial_erro_azimute(results_erro_azimute_df, os.path.join(base_path, cenario_to_folder[cenario], 'Data IQ'))
    elif cenario == 'mobility':
        for ppe_id in results_erro_azimute_df['ppe_id'].unique():
            ppe_results = results_erro_azimute_df[results_erro_azimute_df['ppe_id'] == ppe_id]
            
            for file_name in ppe_results['file_name'].unique():
                gif_frames = []  # Lista para armazenar os frames do GIF para o arquivo atual
                file_results = ppe_results[ppe_results['file_name'] == file_name]
                data_file_path = os.path.join(base_path, cenario_to_folder[cenario], 'Data IQ', file_name)
                data_df = pd.read_csv(data_file_path)
                data_df = normalizar_ppe_ids(data_df)
                data_df = calcular_angulo_real(data_df, anchor_coords)
                
                # Iterar sobre cada linha do data_df para plotar as linhas de azimute real e medido
                for _, data_row in data_df[data_df['ppeID'] == ppe_id].iterrows():
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
                                label='Azimute Real' if anchor_id == 1 else ""
                            )
                            
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
                                label='Azimute Medido' if anchor_id == 1 else ""
                            )
                    
                    # Configurar título e layout
                    ax.set_title(f'Gráfico Espacial - PPE_ID: {ppe_id}, Arquivo: {file_name}, Posição: ({x_real:.2f}, {y_real:.2f})')
                    ax.set_xlabel("X-axis (meters)")
                    ax.set_ylabel("Y-axis (meters)")
                    ax.set_xlim((0, -10.70))   
                    ax.set_ylim(8.8, 0)     
                    plt.tight_layout()
                    # plt.show()

                    # Salvar o frame na lista
                    fig.canvas.draw()
                    frame = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
                    frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                    gif_frames.append(frame)
                    plt.close(fig)

                # Criar o GIF para o arquivo atual usando Pillow
                from PIL import Image
                gif_images = [Image.fromarray(frame) for frame in gif_frames]
                gif_images[0].save(
                    f'grafico_espacial_{file_name}.gif', 
                    save_all=True, 
                    append_images=gif_images[1:], 
                    duration=500, 
                    loop=0
                )
