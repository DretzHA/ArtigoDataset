import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

'''Arquivo para processar e analisar a perda dos pacotes do Dataset'''

# Caminho base para os datasets
#base_path = '0. Dataset Original'
#base_path = '0. Dataset com Mascara Virtual'
base_path = '0. Dataset Teste'

# Escolher Cenário - calibration | static | mobility
cenario = 'static'  # Cenário a ser analisado

# Total esperado de pacotes
total_esperado = 181

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
    "nao_processados_e_recebidos": False,
    "heatmap_nao_processados": False,
    "heatmap_nao_recebidos": False,
    "grafico_espacial_nao_processados": True,
    "grafico_espacial_nao_recebidos": True,
    "histograma": False
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

# Caminho para a imagem de fundo
img_path = '1. Arquivos Python/99. Imagens/background_v2.png'
img = mpimg.imread(img_path)

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

# Função para calcular a perda de pacotes "Não Processados"
def calcular_perda_nao_processados(cenario):
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

        ppe_ids = data_df['ppeID'].unique()

        # Determinar o total esperado para o cenário mobility
        if cenario == 'mobility':
            min_time = data_df['CreateTime'].min()
            max_time = data_df['CreateTime'].max()
            total_esperado = round(max_time - min_time)
        else:
            total_esperado = 181  # Valor fixo para calibration e static

        for ppe_id in ppe_ids:
            data_filtered = data_df[data_df['ppeID'] == ppe_id]
            for anchor, index in anchor_mapping.items():
                # Obter a posição do teste (assumindo que todos os registros do mesmo arquivo/ppe_id têm a mesma posição)
                if cenario in ['static', 'calibration']:
                    if 'X_real' in data_filtered.columns and 'Y_real' in data_filtered.columns:
                        x_real = data_filtered['X_real'].iloc[0]
                        y_real = data_filtered['Y_real'].iloc[0]
                        anchor_x = anchor_coords[index]['x']
                        anchor_y = anchor_coords[index]['y']
                        distancia = ((x_real - anchor_x) ** 2 + (y_real - anchor_y) ** 2) ** 0.5
                    else:
                        distancia = None

                    if distancia is not None and distancia > 0.5:
                        azim_column = f'Azim_{index}'
                        azim_count = data_filtered[azim_column].notnull().sum()
                        results.append({
                            'file_name': file_name,
                            'ppe_id': ppe_id,
                            'anchor': anchor,
                            'nao_processados_count': azim_count,
                            'total_esperado': total_esperado
                        })
                else:  # mobility
                    azim_column = f'Azim_{index}'
                    azim_count = data_filtered[azim_column].notnull().sum()
                    results.append({
                        'file_name': file_name,
                        'ppe_id': ppe_id,
                        'anchor': anchor,
                        'nao_processados_count': azim_count,
                        'total_esperado': total_esperado
                    })

    for result in results:
        result['nao_processados_loss_percentage'] = max(0, ((result['total_esperado'] - result['nao_processados_count']) / result['total_esperado']) * 100)

    results_df = pd.DataFrame(results)
    results_df['anchor'] = results_df['anchor'].map(anchor_mapping)
    return results_df

# Função para calcular a perda de pacotes "Não Recebidos"
def calcular_perda_nao_recebidos(cenario):
    # Construir o caminho da pasta correspondente ao cenário
    cenario_folder = cenario_to_folder[cenario]
    cenario_path = os.path.join(base_path, cenario_folder)

    # Caminho da pasta PeriodicSync
    periodic_sync_path = os.path.join(cenario_path, 'PeriodicSync')
    periodic_sync_files = sorted([f for f in os.listdir(periodic_sync_path) if f.endswith('.csv')])
    periodic_sync_files = filtrar_arquivos(periodic_sync_files)

    results = []
    for file_name in periodic_sync_files:
        periodic_sync_file_path = os.path.join(periodic_sync_path, file_name)
        periodic_sync_df = pd.read_csv(periodic_sync_file_path)

        # Normalizar os ppeIDs
        periodic_sync_df = normalizar_ppe_ids(periodic_sync_df)

        ppe_ids = periodic_sync_df['ppe_id'].unique()

        for ppe_id in ppe_ids:
            periodic_sync_filtered = periodic_sync_df[periodic_sync_df['ppe_id'] == ppe_id]
            for anchor in anchor_mapping.keys():
                periodic_sync_count = periodic_sync_filtered[periodic_sync_filtered['anchor_id'] == anchor].shape[0]

                # Verificar se o filtro retorna algum resultado
                filtered_result = results_nao_processados_df[
                    (results_nao_processados_df['file_name'] == file_name) &
                    (results_nao_processados_df['ppe_id'] == ppe_id) &
                    (results_nao_processados_df['anchor'] == anchor_mapping[anchor])
                ]

                if not filtered_result.empty:
                    total_esperado = filtered_result['total_esperado'].iloc[0]
                else:
                    # Definir um valor padrão ou lidar com o caso de ausência de dados
                    total_esperado = 181 

                results.append({
                    'file_name': file_name,
                    'ppe_id': ppe_id,
                    'anchor': anchor,
                    'nao_recebidos_count': periodic_sync_count,
                    'total_esperado': total_esperado
                })

    for result in results:
        result['nao_recebidos_loss_percentage'] = max(0, ((result['total_esperado'] - result['nao_recebidos_count']) / result['total_esperado']) * 100)

    results_df = pd.DataFrame(results)
    results_df['anchor'] = results_df['anchor'].map(anchor_mapping)
    return results_df

# Função para gerar gráficos com base no controle por_ppe_id
def gerar_graficos(results_df, tipo='nao_processados'):
    # Gerar gráficos por ppe_id
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        if tipo == 'nao_processados':
            loss_data = ppe_results.groupby('anchor')['nao_processados_loss_percentage'].mean()
            title = f'Packet Loss per Anchor (Not Processed) - PPE_ID: {ppe_id}'
        elif tipo == 'nao_recebidos':
            loss_data = ppe_results.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
            title = f'Packet Loss per Anchor (Not Received) - PPE_ID: {ppe_id}'
        loss_data.plot(kind='bar', figsize=(10, 6), title=title)
        plt.xlabel('Anchor')
        plt.ylabel('Loss Percentage (%)')
        plt.show()

def plot_heatmap_ancora(results_df, data_path, tipo='nao_processados', ppe_id=None, radius=0.85, grid_res=150):
    anchors = list(anchor_coords.keys())
    #tipo = 'nao_processados'

    # Define NLoS points and their affected anchors (by anchor index)
    nlos_points = [
        {'pos': (-8.34, 4.74), 'anchors': set(anchor_coords.keys())},  # All anchors
        {'pos': (8.64, 1.44), 'anchors': {3, 5}},  # A03, A05
        {'pos': (-8.64, 7.44), 'anchors': {2, 4, 5, 6, 7}},  # A02, A04, A05, A06, A07
    ]

    for anchor in anchors:
        fig, ax = plt.subplots(figsize=(12, 10))
        coords = anchor_coords[anchor]

        # Filtrar resultados para esta ancora
        anchor_results = results_df[results_df['anchor'] == anchor]
        xs, ys, losses, nlos_flags = [], [], [], []
        for _, row in anchor_results.iterrows():
            file_name = row['file_name']
            # Only apply NLoS coloring for files not starting with 'ORT'
            is_ort = file_name.startswith('ORT')
            data_file_path = os.path.join(data_path, file_name)
            data_df = pd.read_csv(data_file_path)
            data_df = normalizar_ppe_ids(data_df)
            try:
                test_position = data_df[data_df['ppeID'] == row['ppe_id']][['X_real', 'Y_real']].iloc[0]
                x_real, y_real = test_position['X_real'], test_position['Y_real']
                xs.append(x_real)
                ys.append(y_real)
                if tipo == 'nao_processados':
                    losses.append(row['nao_processados_loss_percentage'])
                    name = 'UA'
                else:
                    losses.append(row['nao_recebidos_loss_percentage'])
                    name = 'LP'

                # Check if this point is NLoS for this anchor (and not ORT)
                nlos = False
                if not is_ort:
                    for nlos_point in nlos_points:
                        px, py = nlos_point['pos']
                        # Use a small tolerance for float comparison
                        if abs(x_real - px) < 0.05 and abs(y_real - py) < 0.05:
                            if anchor in nlos_point['anchors']:
                                nlos = True
                                break
                nlos_flags.append(nlos)
            except Exception:
                continue

        if len(xs) < 3:
            ax.set_title(f"Anchor A{anchor} (poucos pontos)")
            ax.imshow(img, extent=[0, -10.70, 8.8, 0], alpha=0.5)
            ax.scatter(coords['x'], coords['y'], color='red', marker='s', s=100, label=f'Anchor A{anchor}')
            plt.tight_layout()
            if ppe_id:
                plt.suptitle(f'Heatmap Spatial por Âncora - PPE_ID: {ppe_id}', fontsize=16)
            plt.show()
            continue

        xs, ys, losses, nlos_flags = np.array(xs), np.array(ys), np.array(losses), np.array(nlos_flags)
        grid_res = 50
        xi = np.linspace(xs.min(), xs.max(), grid_res)
        yi = np.linspace(ys.min(), ys.max(), grid_res)
        xi, yi = np.meshgrid(xi, yi)
        zi = griddata((xs, ys), losses, (xi, yi), method='linear')

        # Máscara para interpolar só perto dos pontos conhecidos
        tree = cKDTree(np.c_[xs, ys])
        dist, _ = tree.query(np.c_[xi.ravel(), yi.ravel()])
        mask = dist.reshape(xi.shape) <= radius
        zi_masked = np.where(mask, zi, np.nan)

        ax.imshow(img, extent=[0, -10.70, 8.8, 0], alpha=0.5)
        pcm = ax.pcolormesh(xi, yi, zi_masked, cmap='coolwarm', shading='auto', alpha=0.7, vmin=0, vmax=50)

        # Plot LoS and NLoS points with different colors
        los_mask = ~nlos_flags
        nlos_mask = nlos_flags

        # LoS points (default color)
        ax.scatter(xs[los_mask], ys[los_mask], c=losses[los_mask], cmap='coolwarm', edgecolor='k', s=60, vmin=0, vmax=50, label='LoS')
        # NLoS points (use magenta)
        if np.any(nlos_mask):
            ax.scatter(xs[nlos_mask], ys[nlos_mask], c='lime', edgecolor='k', s=250, marker='*', label='NLoS')

        ax.scatter(coords['x'], coords['y'], color='red', marker='s', s=100, label=f'Anchor A{anchor}')
        ax.text(coords['x'], coords['y']-0.3, f'A{anchor}', fontsize=34, color='red', ha='center')
        ax.set_xlabel("X-axis (meters)", fontsize=34)
        ax.set_ylabel("Y-axis (meters)", fontsize=34)
        cbar = fig.colorbar(pcm, ax=ax, orientation='vertical', pad=0.02, aspect=30, shrink=0.75)
        cbar.set_label('Missing Packages (Percentage)', fontsize=34)
        cbar.ax.tick_params(labelsize=34)
        cbar.ax.yaxis.offsetText.set_visible(False)
        cbar.formatter.set_useOffset(False)
        cbar.formatter.set_scientific(False)
        cbar.update_ticks()
        plt.tight_layout()
        ax = plt.gca()
        ax.tick_params(axis='x', labelsize=34)
        ax.tick_params(axis='y', labelsize=34)
        # Add legend for LoS/NLoS
        handles, labels = ax.get_legend_handles_labels()
        # Remove duplicate anchor label if present
        unique = dict(zip(labels, handles))
        # Only add NLoS to the legend
        if np.any(nlos_mask):
            ax.legend([plt.Line2D([0], [0], marker='*', color='none', markerfacecolor='lime', markersize=18, markeredgecolor='k', linestyle='None')],
                  ['NLoS'], fontsize=30, loc='upper right')
        #plt.savefig(f'/home/andrey/Desktop/heatmap_{name}_0{anchor}_v2.eps', format='eps', dpi=50)
        #plt.show()

# Função para gerar gráficos espaciais com base no controle por_ppe_id
def gerar_grafico_espacial(results_df, data_path, tipo='nao_processados'):
    # Gerar gráficos espaciais por ppe_id
    for ppe_id in results_df['ppe_id'].unique():
        ppe_results = results_df[results_df['ppe_id'] == ppe_id]
        print(f'Gerando gráfico espacial para PPE_ID: {ppe_id}')
        #gerar_grafico_espacial_por_ppe(ppe_results, data_path, tipo, ppe_id)
        plot_heatmap_ancora(ppe_results, data_path, tipo, ppe_id=ppe_id)

# Função auxiliar para gerar gráficos espaciais
def gerar_grafico_espacial_por_ppe(results_df, data_path, tipo, ppe_id=None):
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
            anchor_results = results_df[results_df['anchor'] == anchor]
            
            # Plotar as posições dos testes e sobrepor as perdas de pacotes
            for _, row in anchor_results.iterrows():
                # Criar uma lista para salvar todas as posições de teste e reais
                test_positions = []

                # Obter a posição do teste
                file_name = row['file_name']
                data_file_path = os.path.join(data_path, file_name)
                data_df = pd.read_csv(data_file_path)
                data_df = normalizar_ppe_ids(data_df)
                test_position = data_df[data_df['ppeID'] == row['ppe_id']][['X_real', 'Y_real']].iloc[0]
                x_real, y_real = test_position['X_real'], test_position['Y_real']

                # Adicionar a posição à lista para debug
                test_positions.append({'file_name': file_name, 'ppe_id': row['ppe_id'], 'x_real': x_real, 'y_real': y_real})
                
                # Obter a perda de pacotes
                if tipo == 'nao_processados':
                    loss = row['nao_processados_loss_percentage']
                    color = 'blue'
                elif tipo == 'nao_recebidos':
                    loss = row['nao_recebidos_loss_percentage']
                    color = 'orange'             
                # Plotar a posição do teste
                ax.scatter(x_real, y_real, color=color, marker='o', s=50, alpha=0.6)
                
                # Adicionar texto com a perda de pacotes
                ax.text(x_real, y_real - 0.2, f'{loss:.1f}%', fontsize=8, color=color, ha='center')
            
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
            plt.suptitle(f'Spatial Plot - PPE_ID: {ppe_id}', fontsize=16)
        plt.show()

# Função para gerar gráficos espaciais para o cenário de mobilidade
def gerar_grafico_espacial_mobility(data_path, results_df, tipo='nao_processados'):
    data_files = sorted([f for f in os.listdir(data_path) if f.endswith('.csv')])
    data_files = filtrar_arquivos(data_files)

    # Ignorar arquivos com "MIP" no nome por enquanto
    data_files = [f for f in data_files if 'MIP' not in f]

    for ppe_id in results_df['ppe_id'].unique():
        for file_name in data_files:
            file_path = os.path.join(data_path, file_name)
            data_df = pd.read_csv(file_path)

            # Normalizar os ppeIDs
            data_df = normalizar_ppe_ids(data_df)

            # Filtrar os dados para o ppe_id atual
            data_df = data_df[data_df['ppeID'] == ppe_id]

            fig, ax = plt.subplots(figsize=(12, 10))
            ax.imshow(img, extent=[0, -10.70, 8.8, 0])  # Ajustar os limites do eixo com base no sistema fornecido

            # Iterar sobre cada linha do arquivo, plotando a cada 3 linhas
            for idx, row in data_df.iterrows():
                if idx % 1 == 0:  # Plotar apenas a cada 3 linhas
                    x_real, y_real = row['X_real'], row['Y_real']
                    # if x_real==-100 or x_real == 'nan':
                    #     print()
                    ax.scatter(x_real, y_real, color='green', marker='o', s=50, alpha=0.6)

                    # Contar âncoras com dados recebidos ou processados
                    if tipo == 'nao_processados':
                        count = sum(pd.notnull(row[f'Azim_{anchor_mapping[anchor]}']) for anchor in anchor_mapping)
                        color = 'blue'
                    elif tipo == 'nao_recebidos':
                        count = sum(row['anchor_id'] == anchor for anchor in anchor_mapping)
                        color = 'orange'

                    # Adicionar texto com a contagem de âncoras
                    ax.text(x_real, y_real - 0.2, f'{count}', fontsize=8, color=color, ha='center')

            # Configurações do gráfico
            ax.set_title(f'Spatial Plot - {tipo.replace("_", " ").title()} - PPE_ID: {ppe_id} - File: {file_name}')
            ax.set_xlabel('X-axis (meters)')
            ax.set_ylabel('Y-axis (meters)')
            plt.tight_layout()
            plt.show()

# Função para plotar histogramas dos resultados de perda para cada ancora
def plotar_histogramas_por_ancora(results_df, tipo='nao_processados'):
    """
    Plota histogramas dos resultados de perda para cada ancora.
    tipo: 'nao_processados' ou 'nao_recebidos'
    """
    if tipo == 'nao_processados':
        col = 'nao_processados_loss_percentage'
        titulo_tipo = 'Not Processed'
    else:
        col = 'nao_recebidos_loss_percentage'
        titulo_tipo = 'Not Received'
    for anchor in sorted(results_df['anchor'].unique()):
        plt.figure(figsize=(8, 5))
        dados = results_df[results_df['anchor'] == anchor][col].dropna()
        plt.hist(dados, bins=15, color='skyblue', edgecolor='black', alpha=0.8)
        plt.title(f'Histogram of Packet Loss ({titulo_tipo}) - Anchor {anchor}')
        plt.xlabel('Loss Percentage (%)')
        plt.ylabel('Count')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

# Verificar se o cenário é válido
if cenario not in cenario_to_folder:
    raise ValueError(f"Cenário inválido: {cenario}. Escolha entre: {', '.join(cenario_to_folder.keys())}")

# Definir o caminho da pasta Data IQ com base no cenário
cenario_folder = cenario_to_folder[cenario]
cenario_path = os.path.join(base_path, cenario_folder)
data_path = os.path.join(cenario_path, 'Data IQ')

# Calcular a perda de pacotes "Não Processados"
results_nao_processados_df = calcular_perda_nao_processados(cenario)
# Calcular a perda de pacotes "Não Recebidos"
results_nao_recebidos_df = calcular_perda_nao_recebidos(cenario)


# Gerar gráficos para perda de pacotes por âncora (Não Processados e Não Recebidos) no mesmo gráfico
if plotar_graficos["nao_processados_e_recebidos"]:
    for ppe_id in results_nao_processados_df['ppe_id'].unique():
        print(ppe_id)
        fig, ax = plt.subplots(figsize=(12, 6))
        ppe_results_nao_processados = results_nao_processados_df[results_nao_processados_df['ppe_id'] == ppe_id]
        ppe_results_nao_recebidos = results_nao_recebidos_df[results_nao_recebidos_df['ppe_id'] == ppe_id]

        # Gráfico de Não Processados
        loss_data_nao_processados = ppe_results_nao_processados.groupby('anchor')['nao_processados_loss_percentage'].mean()
        ax.bar(loss_data_nao_processados.index - 0.2, loss_data_nao_processados, width=0.4, label='UA', color='blue')

        # Gráfico de Não Recebidos
        loss_data_nao_recebidos = ppe_results_nao_recebidos.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
        ax.bar(loss_data_nao_recebidos.index + 0.2, loss_data_nao_recebidos, width=0.4, label='MP', color='orange')

        # Configurações do gráfico
        ax.set_xlabel('Anchor', fontsize=18)
        ax.set_ylabel('Loss Percentage (%)', fontsize=18)
        #ax.set_title(f'Packet Loss per Anchor (Not Processed & Not Received) - PPE_ID: {ppe_id}')
        ax.set_xticks(loss_data_nao_processados.index)
        ax.legend(fontsize=14)
        ax.tick_params(axis='x', labelsize=18)  # Increase fontsize of x-axis anchor numbers
        ax.tick_params(axis='y', labelsize=18)  # Increase fontsize of y-axis labels
         # Ajustar layout
        plt.tight_layout()
       # plt.savefig('/home/andrey/Desktop/stc_4t_cap_media_barra_v2.eps', format='eps', dpi=50)
        plt.grid(alpha=0.5, linestyle='--')
        ax.set_ylim(0, 35)
        plt.show()

    # # Figura adicional: todos os resultados dos não processados de todas as âncoras
    # # Figura adicional: todos os resultados dos não processados de todas as âncoras, cada barra com uma cor diferente
    # fig, ax = plt.subplots(figsize=(12, 6))
    # all_loss_nao_processados = results_nao_processados_df.groupby('anchor')['nao_processados_loss_percentage'].mean()
    # colors = plt.cm.tab10.colors  # Paleta de cores
    # bar_colors = [colors[i % len(colors)] for i in range(len(all_loss_nao_processados))]
    # ax.bar(all_loss_nao_processados.index, all_loss_nao_processados, color=bar_colors, width=0.6)
    # ax.set_xlabel('Anchor', fontsize=18)
    # ax.set_ylabel('Loss Percentage (%)', fontsize=18)
    # #ax.set_title('Packet Loss per Anchor (Not Processed) - All PPE_IDs', fontsize=18)
    # ax.set_xticks(all_loss_nao_processados.index)
    # ax.tick_params(axis='x', labelsize=18)
    # ax.tick_params(axis='y', labelsize=18)
    # plt.tight_layout()
    # plt.grid(alpha=0.5, linestyle='--')
    # ax.set_ylim(0, 35)
    # plt.show()

    # # Figura adicional: todos os resultados dos não recebidos de todas as âncoras, cada barra com uma cor diferente
    # fig, ax = plt.subplots(figsize=(12, 6))
    # all_loss_nao_recebidos = results_nao_recebidos_df.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
    # bar_colors = [colors[i % len(colors)] for i in range(len(all_loss_nao_recebidos))]
    # ax.bar(all_loss_nao_recebidos.index, all_loss_nao_recebidos, color=bar_colors, width=0.6)
    # ax.set_xlabel('Anchor', fontsize=18)
    # ax.set_ylabel('Loss Percentage (%)', fontsize=18)
    # #ax.set_title('Packet Loss per Anchor (Not Received) - All PPE_IDs', fontsize=18)
    # ax.set_xticks(all_loss_nao_recebidos.index)
    # ax.tick_params(axis='x', labelsize=18)
    # ax.tick_params(axis='y', labelsize=18)
    # plt.tight_layout()
    # plt.grid(alpha=0.5, linestyle='--')
    # ax.set_ylim(0, 35)
    # plt.show()

'''Heatmap de Perda de Pacotes'''
# Criar uma tabela pivot para o heatmap de Não Processados (por arquivo de teste) para cada ppeID
if plotar_graficos["heatmap_nao_processados"]:
    for ppe_id in results_nao_processados_df['ppe_id'].unique():
        heatmap_nao_processados = results_nao_processados_df[results_nao_processados_df['ppe_id'] == ppe_id].pivot_table(
            values='nao_processados_loss_percentage',
            index='file_name',
            columns='anchor',
            aggfunc='mean'
        )

        # Criar o heatmap para Não Processados
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_nao_processados, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Loss Percentage (%)'})
        plt.title(f'Packet Loss Heatmap (Not Processed) by Test File - PPE_ID: {ppe_id}')
        plt.xlabel('Anchor')
        plt.ylabel('Test File')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

# Criar uma tabela pivot para o heatmap de Não Recebidos (por arquivo de teste) para cada ppeID
if plotar_graficos["heatmap_nao_recebidos"]:
    for ppe_id in results_nao_recebidos_df['ppe_id'].unique():
        heatmap_periodic_sync = results_nao_recebidos_df[results_nao_recebidos_df['ppe_id'] == ppe_id].pivot_table(
            values='nao_recebidos_loss_percentage',
            index='file_name',
            columns='anchor',
            aggfunc='mean'
        )

        # Criar o heatmap para Não Recebidos
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_periodic_sync, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Loss Percentage (%)'})
        plt.title(f'Packet Loss Heatmap (Not Received) by Test File - PPE_ID: {ppe_id}')
        plt.xlabel('Anchor')
        plt.ylabel('Test File')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

'''Gráfico espacial'''
# Gráfico espacial para Não Processados
if plotar_graficos["grafico_espacial_nao_processados"] and cenario in ['calibration', 'static']:
    gerar_grafico_espacial(results_nao_processados_df, data_path, tipo='nao_processados')

# Gráfico espacial para Não Recebidos
if plotar_graficos["grafico_espacial_nao_recebidos"] and cenario in ['calibration', 'static']:
    gerar_grafico_espacial(results_nao_recebidos_df, data_path, tipo='nao_recebidos')

# Gráfico espacial para Não Processados no cenário de mobilidade
if plotar_graficos["grafico_espacial_nao_processados"] and cenario == 'mobility':
    gerar_grafico_espacial_mobility(data_path, results_nao_processados_df, tipo='nao_processados')

# Plotar histogramas dos resultados "não processados" e "não recebidos" para cada âncora
if plotar_graficos["histograma"]:
    plotar_histogramas_por_ancora(results_nao_processados_df, tipo='nao_processados')
    plotar_histogramas_por_ancora(results_nao_recebidos_df, tipo='nao_recebidos')

