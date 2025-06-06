import os
import pandas as pd
import numpy as np
import math
import shutil
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Define input and output directories
input_folder = "0. Dataset Original/2. Mobility/Data IQ"  
output_folder = "0. Dataset com Mascara Virtual/2. Mobility/Data IQ"  

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

# Caminho para a imagem de fundo
img_path = '1. Arquivos Python/99. Imagens/background_v2.png'
img = mpimg.imread(img_path)

# Define the azimuth angle range for each anchor (Azim_1 to Azim_7) in degrees
azimuth_ranges_deg = {
    "Azim_1": (65, 180),    # Range de leitura para Azim_1
    "Azim_2": (-75, +90),   # Range para ignorar ângulos entre -75 e 90 no Azim_2
    "Azim_3": (0, 180),     # Range de leitura para Azim_3
    "Azim_4": None,          # Special condition for Azim_4
    "Azim_5": None,          # Special condition for Azim_5
    "Azim_6": None,          # Special condition for Azim_6
    "Azim_7": None          # Special condition for Azim_7
}

# Convert ranges to radians (skip Azim_6 since it has a special condition)
azimuth_ranges_rad = {
    key: (math.radians(min_angle), math.radians(max_angle))
    for key, value in azimuth_ranges_deg.items() if value is not None
    for min_angle, max_angle in [value]
}

# # Ensure the output folder exists
# os.makedirs(output_folder, exist_ok=True)

# # Iterate through all files in the input folder
# for filename in os.listdir(input_folder):
#     if filename.endswith(".csv"):  # Process only CSV files
#         input_path = os.path.join(input_folder, filename)
#         output_path = os.path.join(output_folder, filename)

#         # Check if the file name contains "ORT"
#         if "ORT" in filename:
#             # Load the CSV file into a DataFrame
#             df = pd.read_csv(input_path)
#             # Apply the mask only to Azim_6: abs(angle) > 70
#             if "Azim_6" in df.columns:
#                 df["Azim_6"] = df["Azim_6"].apply(
#                     lambda x: x if abs(x) > math.radians(70) else np.nan
#                 )
#                 # Save the modified DataFrame to the output folder
#                 df.to_csv(output_path, index=False)
#             continue

#         # Load the CSV file into a DataFrame
#         df = pd.read_csv(input_path)

#         # Apply the mask to azimuth columns
#         for i in range(1, 8):  # Columns Azim_1 to Azim_7
#             column_name = f"Azim_{i}"
#             if column_name in df.columns:
#                 if column_name == "Azim_2":
#                     min_angle, max_angle = azimuth_ranges_rad[column_name]
#                     # Special condition for Azim_2: reject angles between -75 and 90
#                     df[column_name] = df[column_name].apply(
#                         lambda x: x if not (math.radians(min_angle) <= x <= math.radians(max_angle)) else np.nan
#                     )
#                 elif column_name == "Azim_6":
#                     # Special condition for Azim_6: abs(angle) > 70
#                     df[column_name] = df[column_name].apply(
#                         lambda x: x if abs(x) > math.radians(70) else np.nan
#                     )
#                 elif column_name in azimuth_ranges_rad:
#                     # Apply range-based mask for other azimuths with defined ranges
#                     min_angle, max_angle = azimuth_ranges_rad[column_name]
#                     df[column_name] = df[column_name].apply(
#                         lambda x: x if min_angle <= x <= max_angle else np.nan
#                     )
#                 else:
#                     # Skip filtering for Azim_4, Azim_5, and Azim_7
#                     continue

#         # Save the modified DataFrame to the output folder
#         df.to_csv(output_path, index=False)

def plot_anchors_with_ranges(anchor_coords, azimuth_ranges_deg, img_path):
    img = mpimg.imread(img_path)
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img, extent=[0, -10.70, 8.8, 0])

    for anchor_id, coords in anchor_coords.items():
        x, y = coords['x'], coords['y']
        ax.scatter(x, y, color='red', marker='s', s=100)
        ax.text(x, y + 0.3, f'A{anchor_id}', fontsize=10, color='red', ha='center')

        col = f'Azim_{anchor_id}'
        from matplotlib.patches import Wedge

        if anchor_id == 6:
            # Plotar duas regiões: de -180 até -90 e de 90 até 180 (|ângulo| > 90)
            wedge1 = Wedge(
                (x, y), 2.5,
                -180, -70,
                facecolor='orange', alpha=0.2, edgecolor='orange'
            )
            wedge2 = Wedge(
                (x, y), 2.5,
                70, 180,
                facecolor='orange', alpha=0.2, edgecolor='orange'
            )
            ax.add_patch(wedge1)
            ax.add_patch(wedge2)
            continue

        if col not in azimuth_ranges_deg or azimuth_ranges_deg[col] is None:
            continue
        min_deg, max_deg = azimuth_ranges_deg[col]
        if anchor_id == 2:
            theta1 = -min_deg
            theta2 = -max_deg
        elif anchor_id in [1, 3]:
            theta1 = -max_deg
            theta2 = -min_deg
        else:
            continue  # Não plota range para outras âncoras

        wedge = Wedge(
            (x, y), 2.5,
            theta1, theta2,
            facecolor='orange', alpha=0.2, edgecolor='orange'
        )
        ax.add_patch(wedge)

    ax.set_xlim((0, -10.70))
    ax.set_ylim(8.8, 0)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    plt.title("Direction Ranges")
    plt.tight_layout()
    plt.show()

# Exemplo de uso:
plot_anchors_with_ranges(anchor_coords, azimuth_ranges_deg, img_path)
