import pandas as pd
import os
import ast

# Mapeamento de ppeID
ppeid_mapping = {
    "2c08d2cc-7a1c-9d34-25ea-6265acb43d72": "ble-pd-B43A31EF7B45",
    "1d5ab4ef-0f65-dd99-0b6e-312f5d6add59": "ble-pd-B43A31EF7B26",
    "9c071f5d-0b8f-e641-6d63-2e3e3c3d7179": "ble-pd-B43A31EB2289",
    "4ecede9a-77ff-0ac2-8fa7-335dd98ec107": "ble-pd-B43A31EB228D",
    "d500a44f-2051-d64b-3d63-8985cc792954": "ble-pd-B43A31EF7527"

}

# Definir as colunas esperadas no arquivo de referência
reference_columns = [
    "CreateTime", "idPpe", "idBeacon", "Sequence_number", "Channel",
    "RSSI_1", "RSSI_2", "RSSI_3", "RSSI_4", "RSSI_5", "RSSI_6", "RSSI_7",
    "Azim_1", "Azim_2", "Azim_3", "Azim_4", "Azim_5",
    "Elev_1", "Elev_2", "Elev_3", "Elev_4", "Elev_5", "Elev_6", "Elev_7"
]

# Adicionar colunas de IQ (exemplo: iq_i_1, iq_q_1, ..., iq_i_7, iq_q_7)
for i in range(1, 8):
    reference_columns.append(f"iq_i_{i}")
    reference_columns.append(f"iq_q_{i}")

# Adicionar colunas de coordenadas
reference_columns += ["sylabs_x", "sylabs_y", "sylabs_z", "real_x", "real_y", "real_z"]


# Função para encontrar o arquivo de referência correspondente
def find_reference_file(input_file_name, reference_folder):
    # Tentar diferentes comprimentos para a parte comum
    for num_segments in range(2, 5):  # Tentar de 2 a 4 segmentos
        common_part = "_".join(input_file_name.split("_")[:num_segments])
        
        # Procurar o arquivo de referência correspondente
        for ref_file_name in os.listdir(reference_folder):
            if common_part in ref_file_name:
                return os.path.join(reference_folder, ref_file_name)
    
    # Retornar None se nenhum arquivo correspondente for encontrado
    return None

# Função para processar um único arquivo
def process_file(input_file_path, reference_file_path):
    # Ler o arquivo 1 (entrada)
    df = pd.read_csv(input_file_path)

    # Ler o arquivo de referência e adicionar as colunas esperadas
    reference_df = pd.read_csv(reference_file_path, header=None)
    reference_df.columns = reference_columns

    # Converter colunas de IQ de strings para listas reais
    iq_columns = [col for col in reference_df.columns if col.startswith('iq_')]
    for iq_col in iq_columns:
        reference_df[iq_col] = reference_df[iq_col].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
        )

    # Mapear o ppeID no arquivo de referência
    reference_df['ppeID'] = reference_df['idPpe'].map(ppeid_mapping)

    # Substituir RSSI_1 e RSSI_2 no arquivo 1 com base no ppeID e sequence_number (BeaconID)
    for index, row in df.iterrows():
        ppe_id = row['ppeID']
        sequence_number = row['BeaconID']

        # Filtrar o DataFrame de referência para encontrar os valores correspondentes
        match = reference_df[
            (reference_df['ppeID'] == ppe_id) &
            (reference_df['idBeacon'] == sequence_number)
        ]

        if not match.empty:
            df.at[index, 'RSSI_1'] = match['RSSI_1'].values[0]
            df.at[index, 'RSSI_2'] = match['RSSI_2'].values[0]

            # Adicionar as colunas de IQ ao arquivo 1
            for iq_col in [col for col in reference_df.columns if col.startswith('iq_')]:
                if iq_col not in df.columns:
                    df[iq_col] = None  # Adicionar a coluna se não existir
                df.at[index, iq_col] = match[iq_col].values[0]

    return df

# Função para processar múltiplos arquivos
def process_multiple_files(input_folder, output_folder, reference_folder):
    # Iterar sobre todos os arquivos no diretório de entrada
    for input_file_name in os.listdir(input_folder):
        if input_file_name.endswith(".csv"):
            input_file_path = os.path.join(input_folder, input_file_name)

            # Encontrar o arquivo de referência correspondente
            reference_file_path = find_reference_file(input_file_name, reference_folder)
            if reference_file_path is None:
                print(f"Arquivo de referência não encontrado para: {input_file_name}")
                continue

            # Processar o arquivo
            processed_df = process_file(input_file_path, reference_file_path)

            # Salvar o arquivo processado no diretório de saída
            output_file_path = os.path.join(output_folder, input_file_name)
            processed_df.to_csv(output_file_path, index=False)
            print(f"Arquivo processado e salvo: {output_file_path}")

# Exemplo de uso
input_folder = "0. Dataset/0. Calibration/Data"  # Substitua pelo caminho da pasta de entrada
output_folder = "0. Dataset/0. Calibration/Data IQ"  # Substitua pelo caminho da pasta de saída
reference_folder = "0. Dataset/99. Dados DB/Com Amostras IQ"  # Substitua pelo caminho da pasta de referência

process_multiple_files(input_folder, output_folder, reference_folder)