import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns

'''Arquivo para processar e analisar a perda dos pacotes do Dataset'''

#Escolher Cenário - calibration | static | mobility
cenario = 'calibration'

# Total esperado de pacotes
total_esperado = 181

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

# Coordenadas das âncoras
anchor_coords = {
    1: {'x': -1.00, 'y': 7.83},  # A01
    2: {'x': -0.96, 'y': 1.22},  # A02
    3: {'x': -5.81, 'y': 7.85},  # A03
    4: {'x': -3.50, 'y': 4.60},  # A04
    5: {'x': -5.76, 'y': 4.64},  # A05
    6: {'x': -0.98, 'y': 4.54},  # A06
    7: {'x': -5.85, 'y': 1.21},  # A07
}

# Caminho para a imagem de fundo
img_path = '1. Arquivos Python/99. Imagens/background_v2.png'
img = mpimg.imread(img_path)

# Verificar se o cenário é válido
if cenario not in cenario_to_folder:
    raise ValueError(f"Cenário inválido: {cenario}. Escolha entre: {', '.join(cenario_to_folder.keys())}")

# Caminho base para os datasets
base_path = '0. Dataset'

# Construir o caminho da pasta correspondente ao cenário
cenario_folder = cenario_to_folder[cenario]
cenario_path = os.path.join(base_path, cenario_folder)

# Caminhos das pastas Data e PeriodicSync
data_path = os.path.join(cenario_path, 'Data IQ')
periodic_sync_path = os.path.join(cenario_path, 'PeriodicSync')

# Listar arquivos nas pastas
data_files = sorted([f for f in os.listdir(data_path) if f.endswith('.csv')])
periodic_sync_files = sorted([f for f in os.listdir(periodic_sync_path) if f.endswith('.csv')])

# Filtrar arquivos que não começam com "ORT"
data_files = [f for f in data_files if not f.startswith('ORT')]
periodic_sync_files = [f for f in periodic_sync_files if not f.startswith('ORT')]

# Verificar se os arquivos possuem os mesmos nomes
if data_files != periodic_sync_files:
    raise ValueError("Os arquivos nas pastas 'Data IQ' e 'PeriodicSync' não correspondem.")

# Processar cada arquivo correspondente
results = []

for file_name in data_files:
    # Caminho completo dos arquivos
    data_file_path = os.path.join(data_path, file_name)
    periodic_sync_file_path = os.path.join(periodic_sync_path, file_name)
    
    # Ler os arquivos CSV
    data_df = pd.read_csv(data_file_path)
    periodic_sync_df = pd.read_csv(periodic_sync_file_path)
    
    # Obter os ppeIDs únicos
    ppe_ids = data_df['ppeID'].unique()
    
    for ppe_id in ppe_ids:
        # Filtrar os dados para o ppeID atual
        data_filtered = data_df[data_df['ppeID'] == ppe_id]
        periodic_sync_filtered = periodic_sync_df[periodic_sync_df['ppe_id'] == ppe_id]
        
        # Contar os dados de RSSI_{x} e PeriodicSync para cada âncora
        for anchor, rssi_index in anchor_mapping.items():
            # Contar os valores não nulos em RSSI_{x}
            rssi_column = f'RSSI_{rssi_index}'
            rssi_count = data_filtered[rssi_column].notnull().sum()
            
            # Contar as linhas no PeriodicSync com a âncora correspondente
            periodic_sync_count = periodic_sync_filtered[periodic_sync_filtered['anchor_id'] == anchor].shape[0]
            
            # Armazenar os resultados
            results.append({
                'file_name': file_name,
                'ppe_id': ppe_id,
                'anchor': anchor,
                'rssi_count': rssi_count,
                'periodic_sync_count': periodic_sync_count
            })

# Adicionar cálculo de perda de pacotes ao DataFrame
for result in results:
    result['rssi_loss_percentage'] = ((total_esperado - result['rssi_count']) / total_esperado) * 100
    result['periodic_sync_loss_percentage'] = ((total_esperado - result['periodic_sync_count']) / total_esperado) * 100

# Converter os resultados em um DataFrame
results_df = pd.DataFrame(results)

# Substituir os nomes das âncoras pelos números correspondentes no DataFrame
results_df['anchor'] = results_df['anchor'].map(anchor_mapping)

# Gráfico de barras para perda de pacotes por âncora (RSSI e PeriodicSync)
loss_data = results_df.groupby('anchor')[['rssi_loss_percentage', 'periodic_sync_loss_percentage']].mean()
loss_data.plot(
    kind='bar', figsize=(10, 6), title='Perda de Pacotes por Âncora'
)
plt.xlabel('Âncora')
plt.ylabel('Porcentagem de Perda (%)')
plt.show()

# Gráfico de barras para perda de pacotes por arquivo e âncora (RSSI)
rssi_loss_data = results_df.pivot_table(
    values='rssi_loss_percentage',
    index='file_name',
    columns='anchor',
    aggfunc='mean'
)
rssi_loss_data.plot(
    kind='bar', figsize=(12, 8), title='Perda de Pacotes (RSSI) por Arquivo e Âncora'
)
plt.xlabel('Arquivo')
plt.ylabel('Porcentagem de Perda (%)')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

# Gráfico de barras para perda de pacotes por arquivo e âncora (PeriodicSync)
periodic_sync_loss_data = results_df.pivot_table(
    values='periodic_sync_loss_percentage',
    index='file_name',
    columns='anchor',
    aggfunc='mean'
)
periodic_sync_loss_data.plot(
    kind='bar', figsize=(12, 8), title='Perda de Pacotes (PeriodicSync) por Arquivo e Âncora'
)
plt.xlabel('Arquivo')
plt.ylabel('Porcentagem de Perda (%)')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

'''Heatmap de Perda de Pacotes'''
# Criar uma tabela pivot para o heatmap de RSSI (por arquivo de teste)
heatmap_rssi = results_df.pivot_table(
    values='rssi_loss_percentage',
    index='file_name',
    columns='anchor',
    aggfunc='mean'
)

# Criar o heatmap para RSSI
plt.figure(figsize=(12, 8))
sns.heatmap(heatmap_rssi, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Porcentagem de Perda (%)'})
plt.title('Heatmap de Perda de Pacotes (RSSI) por Arquivo de Teste')
plt.xlabel('Âncora')
plt.ylabel('Arquivo de Teste')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# # Criar uma tabela pivot para o heatmap de PeriodicSync (por arquivo de teste)
# heatmap_periodic_sync = results_df.pivot_table(
#     values='periodic_sync_loss_percentage',
#     index='file_name',
#     columns='anchor',
#     aggfunc='mean'
# )

# # Criar o heatmap para PeriodicSync
# plt.figure(figsize=(12, 8))
# sns.heatmap(heatmap_periodic_sync, annot=True, cmap='coolwarm', fmt=".1f", cbar_kws={'label': 'Porcentagem de Perda (%)'})
# plt.title('Heatmap de Perda de Pacotes (PeriodicSync) por Arquivo de Teste')
# plt.xlabel('Âncora')
# plt.ylabel('Arquivo de Teste')
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()


'''Gráfico espacial'''


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
            
            # Obter a perda de pacotes do RSSI
            rssi_loss = row['rssi_loss_percentage']
            
            # Plotar a posição do teste
            ax.scatter(x_real, y_real, color='blue', marker='o', s=50, alpha=0.6)
            
            # Adicionar texto com a perda de pacotes do RSSI
            ax.text(x_real, y_real - 0.2, f' {rssi_loss:.1f}%', fontsize=8, color='blue', ha='center')
        
        # Configurações do subplot
        ax.set_title(f"Anchor A{anchor}")
        ax.set_xlabel("X-axis (meters)")
        ax.set_ylabel("Y-axis (meters)")
    
    # Remover subplots extras (se houver)
    for subplot_idx in range(subplots_per_figure, len(axes)):
        fig.delaxes(axes[subplot_idx])
    
    # Ajustar layout e exibir a figura
    plt.tight_layout()
    plt.show()

