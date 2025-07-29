import os
import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt


#### teste para ver angulo real
#Coordenadas das ancoras
# anchor_coords = {
#     1: {'x': -1.00, 'y': 7.83, 'z': 2.41},  # A01
#     2: {'x': -0.96, 'y': 1.22, 'z': 2.41},  # A02
#     3: {'x': -5.81, 'y': 7.85, 'z': 2.41},  # A03
#     4: {'x': -3.50, 'y': 4.60, 'z': 2.41},  # A04
#     5: {'x': -5.76, 'y': 4.64, 'z': 2.41},  # A05
#     6: {'x': -0.98, 'y': 4.54, 'z': 2.41},  # A06
#     7: {'x': -5.85, 'y': 1.21, 'z': 2.41},  # A07
# }

# test_coords = {
#     'C1P1': {'x': -1.14, 'y': 0.39, 'z': 1.61}, 
#     'C2P3': {'x': -3.54, 'y': 4.44, 'z': 1.61}, 
#     'C3P1': {'x': -1.14, 'y': 6.84, 'z': 1.61}, 
#     'C3P5': {'x': -5.94, 'y': 6.84, 'z': 1.61}, 
#     'A02': {'x': -0.96, 'y': 1.22, 'z': 1.61}, 
#     'A05': {'x': -5.76, 'y': 4.64, 'z': 1.61}, 
    
# }


# for test_id, tcoords in test_coords.items(): 
#     for anchor_id, acoords in anchor_coords.items():
#         xa = acoords['x']
#         ya = acoords['y']
#         za = acoords['z']
#         xr = tcoords['x']
#         yr = tcoords['y']
#         zr = tcoords['z']


#         dy = yr - ya
#         dx = xr - xa
#         dz = zr - za

#         dist = np.sqrt(dx**2 + dy**2 + dz**2)

#         real_angle = abs(np.arcsin(dz / dist))
#         print(f'Anchor: {anchor_id}, Teste Point: {test_id}, Angulo: {real_angle}, Distancia: {dist:.2f}')
#     print()


# Leitura do arquivo, transformação em DataFrame e contagem dos valores da coluna Azim_1
# file_path = '0. Dataset com Mascara Virtual/0. Calibration/Data IQ/CLB_A06_data.csv'
# df = pd.read_csv(file_path)
# quantidade_azim = df['Azim_7'].count()
# print(f'Quantidade de valores na coluna: {quantidade_azim}')









# for anchor_id, acoords in anchor_coords.items():
#     for test_id, tcoords in test_coords.items(): 
#         xa = acoords['x']
#         ya = acoords['y']
#         xt = tcoords['x']
#         yt = tcoords['y']

#         dy = yt - ya
#         dx = xt - xa

#         ladoh = 'direita' if xa > xt else 'esquerda'
#         ladov = 'cima' if ya > yt else 'baixo'
        
#         # Calcular o ângulo entre a âncora e o ponto de teste
#         if ladoh == 'direita':
#             if ladov == 'cima':
#                 angulo = 180 + math.degrees(math.atan2(dy, dx))
#             else:
#                 angulo = 180 - math.degrees(math.atan2(dy, dx))
#         elif ladoh == 'esquerda':
#             if ladov == 'cima':
#                 angulo = -math.degrees(math.atan2(dy, dx)) 
#             else:
#                 angulo = math.degrees(math.atan2(dy, dx))

#         print(f'Anchor: {anchor_id}, Teste Point: {test_id}, Angulo: {angulo}')

# def check_csv_files(folder_path):
#     for filename in os.listdir(folder_path):
#         if filename.endswith('.csv'):
#             file_path = os.path.join(folder_path, filename)
#             try:
#                 df = pd.read_csv(file_path)
#                 # Substituir -100 por NaN para facilitar o uso do ffill
#                 df['X_real'] = df['X_real'].replace(-100, pd.NA)
#                 df['Y_real'] = df['Y_real'].replace(-100, pd.NA)
#                 df['Z_real'] = df['Z_real'].replace(-100, pd.NA)
#                 # Preencher NaN com o último valor conhecido
#                 df['X_real'] = df['X_real'].fillna(method='ffill')
#                 df['Y_real'] = df['Y_real'].fillna(method='ffill')
#                 df['Z_real'] = df['Z_real'].fillna(method='ffill')
#                 # Salvar de volta se desejar:
#                 df.to_csv(file_path, index=False)
#             except Exception as e:
#                 print(f"Error reading {filename}: {e}")

# def update_mip_real_positions(folder_path):
#     time_lapse = 5
#     # Verifica altura conforme presença de "ORT" no nome do arquivo
#     altura = 1.81 if "ORT" in folder_path or any("ORT" in f for f in os.listdir(folder_path)) else 1.94
#     # Lista de tuplas: (start, end, x, y, z)
#     intervals = [
#         (0, 1, -1.14, 0.39, altura),
#         (1, 2, -2.34, 0.39, altura),
#         (2, 3, -3.54, 0.39, altura),
#         (3, 4, -4.74, 0.39, altura),
#         (4, 5, -5.94, 0.39, altura),
#         (5, 6, -7.14, 0.84, altura),
#         (6, 7, -7.14, 2.04, altura),
#         (7, 8, -7.14, 3.24, altura),
#         (8, 9, -7.14, 4.44, altura),
#         (9, 10, -5.94, 4.44, altura),
#         (10, 11, -4.74, 4.44, altura),
#         (11, 12, -3.54, 4.44, altura),
#         (12, 13, -2.34, 4.44, altura),
#         (13, 14, -1.14, 4.44, altura),
#         (14, 15, -2.34, 4.44, altura),
#         (15, 16, -3.54, 4.44, altura),
#         (16, 17, -4.74, 4.44, altura),
#         (17, 18, -5.94, 4.44, altura),
#         (18, 19, -7.14, 4.44, altura),
#         (19, 20, -7.14, 5.64, altura),
#         (20, 21, -7.14, 6.84, altura),
#         (21, 22, -5.94, 6.84, altura),
#         (22, 23, -4.74, 6.84, altura),
#         (23, 24, -3.54, 6.84, altura),
#         (24, 25, -2.34, 6.84, altura),
#         (25, float('inf'), -1.14, 6.84, altura),
#     ]

#     for filename in os.listdir(folder_path):
#         if "MIP" in filename and filename.endswith('.csv'):
#             file_path = os.path.join(folder_path, filename)
#             if "ORT" in filename:
#                 altura = 1.81
#             else:
#                 altura = 1.94
#             try:
#                 df = pd.read_csv(file_path)
#                 if 'CreateTime' not in df.columns:
#                     print(f"CreateTime column not found in {filename}")
#                     continue
#                 initial_time = df['CreateTime'].iloc[0]
#                 x_vals, y_vals, z_vals = [], [], []
#                 for t in df['CreateTime']:
#                     dif_sec = t - initial_time
#                     idx = int(dif_sec // time_lapse)
#                     for start, end, x, y, z in intervals:
#                         if start <= dif_sec / time_lapse < end:
#                             x_vals.append(x)
#                             y_vals.append(y)
#                             z_vals.append(altura)
#                             break
#                 df['X_real'] = x_vals
#                 df['Y_real'] = y_vals
#                 df['Z_real'] = z_vals
#                 df.to_csv(file_path, index=False)
#                 print(f"Updated {filename}")
#             except Exception as e:
#                 print(f"Error processing {filename}: {e}")

# Example usage:
# check_csv_files('0. Dataset com Mascara Virtual/1. Static/Data IQ')
# update_mip_real_positions('0. Dataset com Mascara Virtual/2. Mobility/Data IQ')



# def corrigir_altura_por_tag(folder_path, tag_col='ppeID'):
#     for filename in os.listdir(folder_path):
#         if "ORT" in filename:
#             tag_alturas = {
#                 'ble-pd-B43A31EF7B26': 1.81,
#                 'ble-pd-588E816309D5': 1.56,
#                 'ble-pd-B43A31EF7B34': 1.56,
#                 'ble-pd-B43A31EF7527': 1.56,
#                 'ble-pd-B43A31EB228D': 0.05,
#                 'ble-pd-B43A31EB2289': 0.98,
#             }
#         else:
#             tag_alturas = {
#                 'ble-pd-B43A31EF7B26': 1.94,
#                 'ble-pd-588E816309D5': 1.64,
#                 'ble-pd-B43A31EF7B34': 1.64,
#                 'ble-pd-B43A31EF7527': 1.64,
#                 'ble-pd-B43A31EB228D': 0.05,
#                 'ble-pd-B43A31EB2289': 1.00,
#             }
#         if filename.endswith('.csv'):
#             file_path = os.path.join(folder_path, filename)
#             try:
#                 df = pd.read_csv(file_path)
#                 if tag_col not in df.columns:
#                     print(f"Coluna '{tag_col}' não encontrada em {filename}")
#                     continue
#                 # Aplica o mapeamento de altura conforme a tag
#                 df['Z_real'] = df[tag_col].map(tag_alturas).fillna(df.get('Z_real', 0))
#                 df.to_csv(file_path, index=False)
#                 print(f"Altura corrigida em {filename}")
#             except Exception as e:
#                 print(f"Erro ao processar {filename}: {e}")

# corrigir_altura_por_tag('0. Dataset com Mascara Virtual/2. Mobility/Data IQ')

# # Caminho dos arquivos CSV
# base_dir = ""  # ajuste para o diretório correto
# arquivos_nao_processados = [
#     "nao_processados_clb_1t.csv",
#     "nao_processados_stc_1t.csv",
#     "nao_processados_stc_4t.csv"
# ]
# arquivos_nao_recebidos = [
#     "nao_recebidos_clb_1t.csv",
#     "nao_recebidos_stc_1t.csv",
#     "nao_recebidos_stc_4t.csv"
# ]

# # Lê todos os arquivos em DataFrames
# dfs_nao_processados = [pd.read_csv(os.path.join(base_dir, arq)) for arq in arquivos_nao_processados]
# dfs_nao_recebidos = [pd.read_csv(os.path.join(base_dir, arq)) for arq in arquivos_nao_recebidos]

# # Nomes para legenda
# labels_nao_processados = ["UA (L1 - CLB - 1T)", "UA (L1 - STC - 1T)", "UA (L1 - STC - 4T)"]
# labels_nao_recebidos = ["MP (L1 - CLB - 1T)", "MP (L1 - STC - 1T)", "MP (L1 - STC - 4T)"]

# # Agrupa por ancora e calcula a média da perda
# loss_np = [df.groupby('anchor')['nao_processados_loss_percentage'].mean() for df in dfs_nao_processados]
# loss_nr = [df.groupby('anchor')['nao_recebidos_loss_percentage'].mean() for df in dfs_nao_recebidos]

# # Descobre todas as âncoras presentes (para garantir alinhamento)
# all_anchors = sorted(set().union(*[l.index for l in loss_np + loss_nr]))

# # Monta matriz de valores para plot
# def get_loss_for_anchors(loss_list, anchors):
#     return [loss.reindex(anchors, fill_value=0).values for loss in loss_list]

# loss_np_vals = get_loss_for_anchors(loss_np, all_anchors)
# loss_nr_vals = get_loss_for_anchors(loss_nr, all_anchors)

# # Figura para Não Processados (NP)
# fig, ax = plt.subplots(figsize=(12, 6))
# bar_width = 0.18
# x = np.arange(len(all_anchors))
# colors = plt.cm.tab10.colors

# for i, vals in enumerate(loss_np_vals):
#     ax.bar(x + i*bar_width - bar_width, vals, width=bar_width, color=colors[i], label=labels_nao_processados[i])

# ax.set_xlabel('Anchor', fontsize=18)
# ax.set_ylabel('Loss Percentage (%)', fontsize=18)
# ax.set_xticks(x)
# ax.set_xticklabels(all_anchors, fontsize=18)
# ax.tick_params(axis='y', labelsize=18)
# plt.tight_layout()
# plt.grid(alpha=0.5, linestyle='--')
# ax.set_ylim(0, 35)
# ax.legend(fontsize=14)
# #plt.title("Packet Loss per Anchor - Not Processed")
# plt.show()

# # Figura para Não Recebidos (NR)
# fig, ax = plt.subplots(figsize=(12, 6))
# for i, vals in enumerate(loss_nr_vals):
#     ax.bar(x + i*bar_width - bar_width, vals, width=bar_width, color=colors[i+3], label=labels_nao_recebidos[i])

# ax.set_xlabel('Anchor', fontsize=18)
# ax.set_ylabel('Loss Percentage (%)', fontsize=18)
# ax.set_xticks(x)
# ax.set_xticklabels(all_anchors, fontsize=18)
# ax.tick_params(axis='y', labelsize=18)
# plt.tight_layout()
# plt.grid(alpha=0.5, linestyle='--')
# ax.set_ylim(0, 35)
# ax.legend(fontsize=14)
# #plt.title("Packet Loss per Anchor - Not Received")
# plt.show()



# Leitura do arquivo solicitado
file_path = '0. Dataset Teste/1. Static/Data IQ/STC_C3P4_data.csv'
df = pd.read_csv(file_path)

# Faz o describe das colunas Azim_1 a Azim_7 (convertendo para graus)
for i in range(1, 8):
    col_name = f'Azim_{i}'
    if col_name in df.columns:
        # Converte de radianos para graus
        df[col_name + '_graus'] = np.degrees(df[col_name])
        print(f'Describe para {col_name} (graus):')
        print(df[col_name + '_graus'].describe())
        print()
    else:
        print(f'Coluna {col_name} não encontrada.')