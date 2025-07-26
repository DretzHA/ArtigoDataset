import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.image as mpimg
import math
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

# Variável para escolher se arquivos específicos serão considerados
considerar_arquivos = {
    "ORT": False,
    "SYLABS": False,
    "UBLOX": False,
    "4T": False,
    "3T": False,
    "OUTROS": True
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

# Parâmetros para boxplot
cenarios = ['calibration', 'static']
base_paths = {
    'calibration': '0. Dataset com Mascara Virtual',
    'static': '0. Dataset com Mascara Virtual'
}
cenario_to_folder = {
    'calibration': '0. Calibration',
    'static': '1. Static'
}

# Mapeamento de títulos das posições pela coordenada (x, y)
pos_titulos_coord = {
    (-1.14, 0.39): "C1P1",
    (-2.34, 0.39): "C1P2",
    (-3.54, 0.39): "C1P3",
    (-4.74, 0.39): "C1P4",
    (-5.94, 0.39): "C1P5",
    (-7.14, 0.84): "C4P1",
    (-7.14, 2.04): "C4P2",
    (-7.14, 3.24): "C4P3",
    (-7.14, 4.44): "C4P4",
    (-5.94, 4.44): "C2P5",
    (-4.74, 4.44): "C2P4",
    (-3.54, 4.44): "C2P3",
    (-2.34, 4.44): "C2P2",
    (-1.14, 4.44): "C2P1",
    (-7.14, 5.64): "C4P5",
    (-7.14, 6.84): "C4P6",
    (-5.94, 6.84): "C3P5",
    (-4.74, 6.84): "C3P4",
    (-3.54, 6.84): "C3P3",
    (-2.34, 6.84): "C3P2",
    (-1.14, 6.84): "C3P1"
}

# Lista para armazenar todos os dados
dados_boxplot = []

for cenario in cenarios:
    base_path = base_paths[cenario]
    cenario_folder = cenario_to_folder[cenario]
    cenario_path = os.path.join(base_path, cenario_folder)
    data_path = os.path.join(cenario_path, 'Data IQ')
    data_files = sorted([f for f in os.listdir(data_path) if f.endswith('.csv')])
    data_files = filtrar_arquivos(data_files)

    for file_name in data_files:
        data_file_path = os.path.join(data_path, file_name)
        data_df = pd.read_csv(data_file_path)
        data_df = normalizar_ppe_ids(data_df)
        # Filtrar OUTROS se necessário
        if not considerar_arquivos["OUTROS"]:
            continue
        # Para cada posição (linha), para cada ancora, salva Azim_i
        for idx, row in data_df.iterrows():
            x_val = float(row['X_real'])
            y_val = float(row['Y_real'])
            if (x_val, y_val) not in pos_titulos_coord:
                continue  # ignora pontos não mapeados
            ponto_nome = pos_titulos_coord[(x_val, y_val)]
            for i in range(1, 8):
                azim_col = f"Azim_{i}"
                if azim_col in data_df.columns:
                    azim_val = row[azim_col]
                    if not pd.isna(azim_val):
                        dados_boxplot.append({
                            'cenario': cenario,
                            'pos_id': ponto_nome,
                            'anchor': i,
                            'Azim': azim_val  # mantém em radianos
                        })

# Converte para DataFrame
df_box = pd.DataFrame(dados_boxplot)

# Gera grid de subplots: cada posição é um subplot, cada ancora é um boxplot dentro
posicoes = sorted(df_box['pos_id'].unique())
anchors = sorted(df_box['anchor'].unique())
n_rows = int(np.ceil(len(posicoes) / 10))
n_cols = min(10, len(posicoes))

fig, axes = plt.subplots(n_rows, n_cols, figsize=(2.5*n_cols, 2.5*n_rows), sharey=True)
axes = axes.flatten()

# Organiza os nomes dos pontos por linha desejada
linha_C1 = [v for v in pos_titulos_coord.values() if v.startswith("C1")]
linha_C2 = [v for v in pos_titulos_coord.values() if v.startswith("C2")]
linha_C3 = [v for v in pos_titulos_coord.values() if v.startswith("C3")]
linha_C4 = [v for v in pos_titulos_coord.values() if v.startswith("C4") and not v.endswith("C4P6")]
linha_C4P6 = [v for v in pos_titulos_coord.values() if v == "C4P6"]

# Junta na ordem desejada
posicoes_ordenadas = linha_C1 + linha_C2 + linha_C3 + linha_C4 + linha_C4P6

n_rows = 5
n_cols = max(len(linha_C1), len(linha_C2), len(linha_C3), len(linha_C4))

fig, axes = plt.subplots(n_rows, n_cols, figsize=(2.5*n_cols, 2.5*n_rows), sharey=True)
axes = axes.reshape(n_rows, n_cols)

def ajustar_angulo_rad(serie):
    """
    Ajusta os ângulos em radianos para evitar que o boxplot mostre valores próximos de -pi e pi como extremos.
    Garante que a diferença entre os valores seja sempre a menor possível (intervalo circular).
    """
    if len(serie) == 0:
        return serie
    # Converte para numpy array
    arr = np.array(serie)
    # Calcula o ângulo médio usando média circular
    angulo_medio = np.arctan2(np.mean(np.sin(arr)), np.mean(np.cos(arr)))
    # Ajusta todos os ângulos para ficarem próximos do ângulo médio
    arr_ajustado = ((arr - angulo_medio + np.pi) % (2 * np.pi)) - np.pi + angulo_medio
    return arr_ajustado

for row_idx, linha in enumerate([linha_C1, linha_C2, linha_C3, linha_C4, linha_C4P6]):
    for col_idx, pos in enumerate(linha):
        ax = axes[row_idx, col_idx]
        df_pos = df_box[df_box['pos_id'] == pos]
        titulo = pos
        for anchor in anchors:
            df_anchor = df_pos[df_pos['anchor'] == anchor]
            data_static = ajustar_angulo_rad(df_anchor[df_anchor['cenario'] == 'static']['Azim'])
            data_calib = ajustar_angulo_rad(df_anchor[df_anchor['cenario'] == 'calibration']['Azim'])
            box_data = [data_static, data_calib]
            ax.boxplot(
                box_data,
                positions=[anchor-0.2, anchor+0.2],
                widths=0.3,
                patch_artist=True,
                boxprops=dict(facecolor='orange', alpha=0.6) if len(data_static) > 0 else dict(facecolor='none'),
                medianprops=dict(color='black'),
                showfliers=True
            )
            if len(data_calib) > 0:
                ax.boxplot(
                    [data_calib],
                    positions=[anchor+0.2],
                    widths=0.3,
                    patch_artist=True,
                    boxprops=dict(facecolor='green', alpha=0.6),
                    medianprops=dict(color='black'),
                    showfliers=True
                )
        ax.set_title(titulo, fontsize=10)
        ax.set_xticks(anchors)
        ax.set_xticklabels([f"{a}" for a in anchors], fontsize=8)
        ax.set_ylim(-3.14, 3.14)
        if col_idx == 0:
            ax.set_ylabel("AoA [°]", fontsize=9)

# Remove subplots extras
for row in range(n_rows):
    for col in range(n_cols):
        pos = None
        if row == 0 and col < len(linha_C1):
            pos = linha_C1[col]
        elif row == 1 and col < len(linha_C2):
            pos = linha_C2[col]
        elif row == 2 and col < len(linha_C3):
            pos = linha_C3[col]
        elif row == 3 and col < len(linha_C4):
            pos = linha_C4[col]
        elif row == 4 and col < len(linha_C4P6):
            pos = linha_C4P6[col]
        if pos is None or pos not in posicoes_ordenadas:
            fig.delaxes(axes[row, col])

# Legenda manual
import matplotlib.patches as mpatches
orange_patch = mpatches.Patch(color='orange', label='static')
green_patch = mpatches.Patch(color='green', label='calibration')
fig.legend(handles=[orange_patch, green_patch], loc='upper left', fontsize=12)

plt.tight_layout()
plt.subplots_adjust(top=0.92)
plt.show()
