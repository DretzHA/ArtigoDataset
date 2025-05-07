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
input_columns = [
    "CreateTime", "ppeID", "idBeacon", "Sequence_number", "Channel",
    "RSSI_1", "RSSI_2", "RSSI_3", "RSSI_4", "RSSI_5", "RSSI_6", "RSSI_7",
    "Azim_1", "Azim_2", "Azim_3", "Azim_4", "Azim_5",
    "Elev_1", "Elev_2", "Elev_3", "Elev_4", "Elev_5", "Elev_6", "Elev_7"
]

# Adicionar colunas de IQ (exemplo: iq_i_1, iq_q_1, ..., iq_i_7, iq_q_7)
for i in range(1, 8):
    input_columns.append(f"iq_i_{i}")
    input_columns.append(f"iq_q_{i}")

# Adicionar colunas de coordenadas
input_columns += ["X_sylabs", "Y_sylabs", "Z_sylabs", "X_real", "Y_real", "Z_real"]


# Função para encontrar o arquivo de referência correspondente
def find_reference_file(input_file_name, reference_folder):
    # Extrair a parte comum do nome do arquivo de entrada (TXT)
    common_part_txt = input_file_name.replace("exported_", "").replace(".txt", "")
    
    # Procurar o arquivo de referência correspondente na pasta de referência
    for ref_file_name in os.listdir(reference_folder):
        # Extrair a parte comum do nome do arquivo de referência (CSV)
        common_part_csv = ref_file_name.split("_data")[0]
        
        # Comparar as partes comuns
        if common_part_txt == common_part_csv:
            return os.path.join(reference_folder, ref_file_name)
    
    # Retornar None se nenhum arquivo correspondente for encontrado
    return None

# Função para processar um único arquivo
def process_file(input_file_path, reference_file_path):
    # Ler o arquivo de entrada (TXT) e adicionar as colunas esperadas
    input_df = pd.read_csv(input_file_path, header=None)
    input_df.columns = input_columns

    # Converter colunas de IQ de strings para listas reais
    iq_columns = [col for col in input_columns if col.startswith('iq_')]
    for iq_col in iq_columns:
        input_df[iq_col] = input_df[iq_col].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
        )

    # Ler o arquivo de referência (CSV)
    reference_df = pd.read_csv(reference_file_path)

    # Mapear o ppeID no arquivo de referência
    input_df['ppeID'] = input_df['idPpe'].map(ppeid_mapping)

    # Adicionar ou substituir as colunas no arquivo de entrada
    for index, row in input_df.iterrows():
        ppe_id = row['idPpe']
        sequence_number = row['idBeacon']

        # Filtrar o DataFrame de referência para encontrar os valores correspondentes
        match = reference_df[
            (reference_df['ppeID'] == ppe_id) &
            (reference_df['idBeacon'] == sequence_number)
        ]

        if not match.empty:
            # Adicionar os valores de Azim_5 e Azim_6
            input_df.at[index, 'Azim_5'] = match['Azim_5'].values[0]
            input_df.at[index, 'Azim_6'] = match['Azim_6'].values[0]

            # Substituir as colunas de coordenadas
            input_df.at[index, 'X_sylabs'] = match['X_sylabs'].values[0]
            input_df.at[index, 'Y_sylabs'] = match['Y_sylabs'].values[0]
            input_df.at[index, 'Z_sylabs'] = match['Z_sylabs'].values[0]
            input_df.at[index, 'X_real'] = match['X_real'].values[0]
            input_df.at[index, 'Y_real'] = match['Y_real'].values[0]
            input_df.at[index, 'Z_real'] = match['Z_real'].values[0]

    return input_df

# Função para processar múltiplos arquivos
def process_multiple_files(input_folder, output_folder, reference_folder):
    # Iterar sobre todos os arquivos no diretório de entrada
    for input_file_name in os.listdir(input_folder):
        if input_file_name.endswith(".txt"):
            input_file_path = os.path.join(input_folder, input_file_name)

            # Encontrar o arquivo de referência correspondente
            reference_file_path = find_reference_file(input_file_name, reference_folder)
            if reference_file_path is None:
                print(f"Arquivo de referência não encontrado para: {input_file_name}")
                continue

            # Processar o arquivo
            processed_df = process_file(input_file_path, reference_file_path)

            # Salvar o arquivo processado no diretório de saída
            output_file_name = input_file_name.replace(".txt", ".csv")
            output_file_path = os.path.join(output_folder, output_file_name)
            processed_df.to_csv(output_file_path, index=False)
            print(f"Arquivo processado e salvo: {output_file_path}")

# Exemplo de uso
reference_folder = "0. Dataset/0. Calibration/Data"  # Substitua pelo caminho da pasta de entrada
output_folder = "0. Dataset/0. Calibration/Data IQ"  # Substitua pelo caminho da pasta de saída
input_folder = "0. Dataset/99. Dados DB/Com Amostras IQ/0. Calibration"  # Substitua pelo caminho da pasta de referência

process_multiple_files(input_folder, output_folder, reference_folder)