import os
import pandas as pd
import matplotlib.pyplot as plt

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

# Verificar se o cenário é válido
if cenario not in cenario_to_folder:
    raise ValueError(f"Cenário inválido: {cenario}. Escolha entre: {', '.join(cenario_to_folder.keys())}")

# Caminho base para os datasets
base_path = '/home/andrey/Desktop/ANDREY/Pesquisa/ArtigoDataset/0. Dataset'

# Construir o caminho da pasta correspondente ao cenário
cenario_folder = cenario_to_folder[cenario]
cenario_path = os.path.join(base_path, cenario_folder)

# Caminhos das pastas Data e PeriodicSync
data_path = os.path.join(cenario_path, 'Data')
periodic_sync_path = os.path.join(cenario_path, 'PeriodicSync')

# Listar arquivos nas pastas
data_files = sorted([f for f in os.listdir(data_path) if f.endswith('.csv')])
periodic_sync_files = sorted([f for f in os.listdir(periodic_sync_path) if f.endswith('.csv')])

# Verificar se os arquivos possuem os mesmos nomes
if data_files != periodic_sync_files:
    raise ValueError("Os arquivos nas pastas 'Data' e 'PeriodicSync' não correspondem.")

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

# # Exibir os resultados
# print(results_df)

# Substituir os nomes das âncoras pelos números correspondentes no DataFrame
results_df['anchor'] = results_df['anchor'].map(anchor_mapping)

# Gráfico de barras para perda de pacotes por âncora
results_df.groupby('anchor')[['rssi_loss_percentage', 'periodic_sync_loss_percentage']].mean().plot(
    kind='bar', figsize=(10, 6), title='Perda de Pacotes por Âncora'
)
plt.xlabel('Âncora')
plt.ylabel('Porcentagem de Perda (%)')
plt.show()

# Criar subplots para os dois gráficos
fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# Gráfico de linhas para perda de pacotes por arquivo (RSSI)
for anchor in results_df['anchor'].unique():
    anchor_data = results_df[results_df['anchor'] == anchor]
    axes[0].plot(anchor_data['file_name'], anchor_data['rssi_loss_percentage'], label=f'RSSI Loss - Anchor {anchor}')

axes[0].set_title('Perda de Pacotes (RSSI) por Arquivo e Âncora')
axes[0].set_ylabel('Porcentagem de Perda (%)')
axes[0].legend()
axes[0].grid(True)

# Gráfico de linhas para perda de pacotes por arquivo (PeriodicSync)
for anchor in results_df['anchor'].unique():
    anchor_data = results_df[results_df['anchor'] == anchor]
    axes[1].plot(anchor_data['file_name'], anchor_data['periodic_sync_loss_percentage'], label=f'PeriodicSync Loss - Anchor {anchor}')

axes[1].set_title('Perda de Pacotes (PeriodicSync) por Arquivo e Âncora')
axes[1].set_ylabel('Porcentagem de Perda (%)')
axes[1].set_xlabel('Arquivo')
axes[1].legend()
axes[1].grid(True)

# Ajustar layout e exibir os gráficos
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()