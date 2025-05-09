import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns

'''Arquivo para processar e analisar a perda dos pacotes do Dataset'''

# Escolher Cenário - calibration | static | mobility
cenario = 'calibration'

# Total esperado de pacotes
total_esperado = 181

# Variável para definir se os gráficos e resultados serão feitos por cada tipo de ppe_id ou pela média
por_ppe_id = True  # True para resultados por ppe_id, False para resultados pela média

# Variável para escolher se arquivos específicos serão considerados
considerar_arquivos = {
    "ORT": False,
    "SYLABS": False,
    "UBLOX": False,
    "4T": False,
    "3T": True,
    "OUTROS": False
}

# Variáveis para definir quais gráficos serão plotados
plotar_graficos = {
    "nao_processados_por_ancora": True,
    "nao_recebidos_por_ancora": True,
    "nao_processados_por_arquivo": True,
    "nao_recebidos_por_arquivo": True,
    "heatmap_nao_processados": True,
    "heatmap_nao_recebidos": True,
    "grafico_espacial_nao_processados": True,
    "grafico_espacial_nao_recebidos": True
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

# Caminho base para os datasets
base_path = '0. Dataset'

# Função para filtrar arquivos com base na variável considerar_arquivos
def filtrar_arquivos(data_files):
    # Filtrar arquivos específicos
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
        ppe_ids = data_df['ppeID'].unique()

        for ppe_id in ppe_ids:
            data_filtered = data_df[data_df['ppeID'] == ppe_id]
            for anchor, rssi_index in anchor_mapping.items():
                rssi_column = f'RSSI_{rssi_index}'
                rssi_count = data_filtered[rssi_column].notnull().sum()
                results.append({
                    'file_name': file_name,
                    'ppe_id': ppe_id,
                    'anchor': anchor,
                    'nao_processados_count': rssi_count
                })

    for result in results:
        result['nao_processados_loss_percentage'] = max(0, ((total_esperado - result['nao_processados_count']) / total_esperado) * 100)

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
        ppe_ids = periodic_sync_df['ppe_id'].unique()

        for ppe_id in ppe_ids:
            periodic_sync_filtered = periodic_sync_df[periodic_sync_df['ppe_id'] == ppe_id]
            for anchor in anchor_mapping.keys():
                periodic_sync_count = periodic_sync_filtered[periodic_sync_filtered['anchor_id'] == anchor].shape[0]
                results.append({
                    'file_name': file_name,
                    'ppe_id': ppe_id,
                    'anchor': anchor,
                    'nao_recebidos_count': periodic_sync_count
                })

    for result in results:
        result['nao_recebidos_loss_percentage'] = max(0, ((total_esperado - result['nao_recebidos_count']) / total_esperado) * 100)

    results_df = pd.DataFrame(results)
    results_df['anchor'] = results_df['anchor'].map(anchor_mapping)
    return results_df

# Função para gerar gráficos com base no controle por_ppe_id
def gerar_graficos(results_df, tipo='nao_processados'):
    if por_ppe_id:
        # Gerar gráficos por ppe_id
        for ppe_id in results_df['ppe_id'].unique():
            ppe_results = results_df[results_df['ppe_id'] == ppe_id]
            if tipo == 'nao_processados':
                loss_data = ppe_results.groupby('anchor')['nao_processados_loss_percentage'].mean()
                title = f'Perda de Pacotes por Âncora (Não Processados) - PPE_ID: {ppe_id}'
            elif tipo == 'nao_recebidos':
                loss_data = ppe_results.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
                title = f'Perda de Pacotes por Âncora (Não Recebidos) - PPE_ID: {ppe_id}'
            loss_data.plot(kind='bar', figsize=(10, 6), title=title)
            plt.xlabel('Âncora')
            plt.ylabel('Porcentagem de Perda (%)')
            plt.show()
    else:
        # Gerar gráficos pela média
        if tipo == 'nao_processados':
            loss_data = results_df.groupby('anchor')['nao_processados_loss_percentage'].mean()
            title = 'Perda de Pacotes por Âncora (Não Processados) - Média'
        elif tipo == 'nao_recebidos':
            loss_data = results_df.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
            title = 'Perda de Pacotes por Âncora (Não Recebidos) - Média'
        loss_data.plot(kind='bar', figsize=(10, 6), title=title)
        plt.xlabel('Âncora')
        plt.ylabel('Porcentagem de Perda (%)')
        plt.show()

# Função para gerar gráficos espaciais com base no controle por_ppe_id
def gerar_grafico_espacial(results_df, data_path, tipo='nao_processados'):
    if por_ppe_id:
        # Gerar gráficos espaciais por ppe_id
        for ppe_id in results_df['ppe_id'].unique():
            ppe_results = results_df[results_df['ppe_id'] == ppe_id]
            print(f'Gerando gráfico espacial para PPE_ID: {ppe_id}')
            gerar_grafico_espacial_por_ppe(ppe_results, data_path, tipo, ppe_id)
    else:
        # Gerar gráficos espaciais pela média
        gerar_grafico_espacial_por_ppe(results_df, data_path, tipo)

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
                # Obter a posição do teste
                file_name = row['file_name']
                data_file_path = os.path.join(data_path, file_name)
                data_df = pd.read_csv(data_file_path)
                test_position = data_df[data_df['ppeID'] == row['ppe_id']][['X_real', 'Y_real']].iloc[0]
                x_real, y_real = test_position['X_real'], test_position['Y_real']
                
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
            plt.suptitle(f'Gráfico Espacial - PPE_ID: {ppe_id}', fontsize=16)
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
if plotar_graficos["nao_processados_por_ancora"] and plotar_graficos["nao_recebidos_por_ancora"]:
    if por_ppe_id:
        for ppe_id in results_nao_processados_df['ppe_id'].unique():
            fig, ax = plt.subplots(figsize=(12, 6))
            ppe_results_nao_processados = results_nao_processados_df[results_nao_processados_df['ppe_id'] == ppe_id]
            ppe_results_nao_recebidos = results_nao_recebidos_df[results_nao_recebidos_df['ppe_id'] == ppe_id]

            # Gráfico de Não Processados
            loss_data_nao_processados = ppe_results_nao_processados.groupby('anchor')['nao_processados_loss_percentage'].mean()
            ax.bar(loss_data_nao_processados.index - 0.2, loss_data_nao_processados, width=0.4, label='Não Processados', color='blue')

            # Gráfico de Não Recebidos
            loss_data_nao_recebidos = ppe_results_nao_recebidos.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
            ax.bar(loss_data_nao_recebidos.index + 0.2, loss_data_nao_recebidos, width=0.4, label='Não Recebidos', color='orange')

            # Configurações do gráfico
            ax.set_xlabel('Âncora')
            ax.set_ylabel('Porcentagem de Perda (%)')
            ax.set_title(f'Perda de Pacotes por Âncora (Não Processados e Não Recebidos) - PPE_ID: {ppe_id}')
            ax.set_xticks(loss_data_nao_processados.index)
            ax.legend()

            # Ajustar layout
            plt.tight_layout()
            plt.show()
    else:
        fig, ax = plt.subplots(figsize=(12, 6))

        # Gráfico de Não Processados
        loss_data_nao_processados = results_nao_processados_df.groupby('anchor')['nao_processados_loss_percentage'].mean()
        ax.bar(loss_data_nao_processados.index - 0.2, loss_data_nao_processados, width=0.4, label='Não Processados', color='blue')

        # Gráfico de Não Recebidos
        loss_data_nao_recebidos = results_nao_recebidos_df.groupby('anchor')['nao_recebidos_loss_percentage'].mean()
        ax.bar(loss_data_nao_recebidos.index + 0.2, loss_data_nao_recebidos, width=0.4, label='Não Recebidos', color='orange')

        # Configurações do gráfico
        ax.set_xlabel('Âncora')
        ax.set_ylabel('Porcentagem de Perda (%)')
        ax.set_title('Perda de Pacotes por Âncora (Não Processados e Não Recebidos) - Média')
        ax.set_xticks(loss_data_nao_processados.index)
        ax.legend()

        # Ajustar layout
        plt.tight_layout()
        plt.show()

# Gerar gráficos separadamente, caso apenas um deles esteja ativado
elif plotar_graficos["nao_processados_por_ancora"]:
    gerar_graficos(results_nao_processados_df, tipo='nao_processados')

elif plotar_graficos["nao_recebidos_por_ancora"]:
    gerar_graficos(results_nao_recebidos_df, tipo='nao_recebidos')

# Gráfico de barras para perda de pacotes por arquivo e âncora (Não Processados)
if plotar_graficos["nao_processados_por_arquivo"]:
    nao_processados_loss_data = results_nao_processados_df.pivot_table(
        values='nao_processados_loss_percentage',
        index='file_name',
        columns='anchor',
        aggfunc='mean'
    )
    nao_processados_loss_data.plot(
        kind='bar', figsize=(12, 8), title='Perda de Pacotes (Não Processados) por Arquivo e Âncora'
    )
    plt.xlabel('Arquivo')
    plt.ylabel('Porcentagem de Perda (%)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

# Gráfico de barras para perda de pacotes por arquivo e âncora (Não Recebidos)
if plotar_graficos["nao_recebidos_por_arquivo"]:
    nao_recebidos_loss_data = results_nao_recebidos_df.pivot_table(
        values='nao_recebidos_loss_percentage',
        index='file_name',
        columns='anchor',
        aggfunc='mean'
    )
    nao_recebidos_loss_data.plot(
        kind='bar', figsize=(12, 8), title='Perda de Pacotes (Não Recebidos) por Arquivo e Âncora'
    )
    plt.xlabel('Arquivo')
    plt.ylabel('Porcentagem de Perda (%)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

'''Heatmap de Perda de Pacotes'''
# Criar uma tabela pivot para o heatmap de Não Processados (por arquivo de teste)
if plotar_graficos["heatmap_nao_processados"]:
    heatmap_nao_processados = results_nao_processados_df.pivot_table(
        values='nao_processados_loss_percentage',
        index='file_name',
        columns='anchor',
        aggfunc='mean'
    )

    # Criar o heatmap para Não Processados
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_nao_processados, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Porcentagem de Perda (%)'})
    plt.title('Heatmap de Perda de Pacotes (Não Processados) por Arquivo de Teste')
    plt.xlabel('Âncora')
    plt.ylabel('Arquivo de Teste')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Criar uma tabela pivot para o heatmap de Não Recebidos (por arquivo de teste)
if plotar_graficos["heatmap_nao_recebidos"]:
    heatmap_periodic_sync = results_nao_recebidos_df.pivot_table(
        values='nao_recebidos_loss_percentage',
        index='file_name',
        columns='anchor',
        aggfunc='mean'
    )

    # Criar o heatmap para Não Recebidos
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_periodic_sync, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Porcentagem de Perda (%)'})
    plt.title('Heatmap de Perda de Pacotes (Não Recebidos) por Arquivo de Teste')
    plt.xlabel('Âncora')
    plt.ylabel('Arquivo de Teste')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

'''Gráfico espacial'''
# Gráfico espacial para Não Processados
if plotar_graficos["grafico_espacial_nao_processados"]:
    gerar_grafico_espacial(results_nao_processados_df, data_path, tipo='nao_processados')

# Gráfico espacial para Não Recebidos
if plotar_graficos["grafico_espacial_nao_recebidos"]:
    gerar_grafico_espacial(results_nao_recebidos_df, data_path, tipo='nao_recebidos')

