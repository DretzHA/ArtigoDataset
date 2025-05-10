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
    "Elev_1", "Elev_2", "Elev_3", "Elev_4", "Elev_5", "Elev_6", "Elev_7",
    "X_sylabs", "Y_sylabs", "Z_sylabs", "X_real", "Y_real", "Z_real"
]

# Adicionar colunas de IQ (exemplo: iq_i_1, iq_q_1, ..., iq_i_7, iq_q_7)
for i in range(1, 8):
    input_columns.append(f"iq_i_{i}")
    input_columns.append(f"iq_q_{i}")

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

def process_file(input_file_path, reference_file_path):
    # Definir o número máximo de colunas esperadas no arquivo de entrada
    max_columns = 692  # Ajuste este valor conforme necessário

    # Ler o arquivo de entrada (TXT) com o número máximo de colunas esperado
    input_df = pd.read_csv(input_file_path, header=None, names=range(max_columns))
    # input_df = pd.read_csv(input_file_path, header=None)


    # Preencher valores ausentes com NaN
    input_df.fillna(float('nan'), inplace=True)

    # Índice inicial das colunas de IQ
    iq_start_index = 24  # Começa na coluna 24
    iq_block_size = 82   # Tamanho de cada bloco de IQ (82 elementos)

    # Criar listas para armazenar os valores processados de IQ
    iq_i_values = {i: [] for i in range(1, 5)}  # Para iq_i_1 a iq_i_4
    iq_q_values = {i: [] for i in range(1, 5)}  # Para iq_q_1 a iq_q_4

    # Processar cada linha individualmente
    for _, row in input_df.iterrows():
        current_start_index = iq_start_index  # Reiniciar o índice inicial para cada linha

        for i in range(1, 5):  # Para iq_i_1 a iq_i_4 e iq_q_1 a iq_q_4
            iq_i_indices = list(range(current_start_index, current_start_index + iq_block_size))
            iq_q_indices = list(range(current_start_index + iq_block_size, current_start_index + 2 * iq_block_size))

            if row[iq_i_indices].isnull().any() or row[iq_q_indices].isnull().any():
                # Se houver NaN, preencher com NaN e pular 2 colunas
                iq_i_values[i].append([float('nan')] * iq_block_size)
                iq_q_values[i].append([float('nan')] * iq_block_size)
                current_start_index += 2  # Pular 2 colunas
            else:
                # Caso contrário, processar normalmente
                iq_i_values[i].append(row[iq_i_indices].tolist())
                iq_q_values[i].append(row[iq_q_indices].tolist())
                current_start_index += 2 * iq_block_size  # Avançar para o próximo bloco

    # Adicionar as colunas processadas ao DataFrame
    for i in range(1, 5):
        input_df[f"iq_i_{i}"] = iq_i_values[i]
        input_df[f"iq_q_{i}"] = iq_q_values[i]

    # Remover as colunas originais do DataFrame
    cols_to_drop = []
    for i in range(4):  # Para os 4 blocos de IQ
        cols_to_drop.extend(list(range(iq_start_index + i * 2 * iq_block_size, iq_start_index + (i + 1) * 2 * iq_block_size)))
    input_df.drop(columns=cols_to_drop, inplace=True)

    # Preencher os valores de IQ para iq_i_5, iq_q_5, ..., iq_i_7, iq_q_7 com NaN
    for i in range(5, 8):  # Para iq_i_5 a iq_i_7 e iq_q_5 a iq_q_7
        input_df[f"iq_i_{i}"] = [float('nan')] * len(input_df)
        input_df[f"iq_q_{i}"] = [float('nan')] * len(input_df)

    # Remover as colunas com os títulos 680, 681, 682, 683, 684, 685
    colunas_para_remover = [680, 681, 682, 683, 684, 685]
    input_df = input_df.drop(columns=colunas_para_remover, errors='ignore')

    # Atribuir os nomes das colunas após o tratamento
    input_df.columns = input_columns

    # Ler o arquivo de referência (CSV)
    reference_df = pd.read_csv(reference_file_path)

    # Mapear o ppeID no arquivo de referência
    input_df['ppeID'] = input_df['ppeID'].map(ppeid_mapping)

    # Filtrar para manter apenas os ppeID encontrados no arquivo de referência
    valid_ppeIDs = reference_df['ppeID'].unique()
    input_df = input_df[input_df['ppeID'].isin(valid_ppeIDs)]

    # Adicionar ou substituir as colunas no arquivo de entrada
    for index, row in input_df.iterrows():
        ppe_id = row['ppeID']
        sequence_number = row['Sequence_number']

        # Filtrar o DataFrame de referência para encontrar os valores correspondentes
        match = reference_df[
            (reference_df['ppeID'] == ppe_id) &
            (reference_df['BeaconID'] == sequence_number)
        ]

        if not match.empty:
            # Adicionar os valores de Azim_5 e Azim_6
            input_df.at[index, 'Azim_7'] = match['Azim_7'].values[0]
            input_df.at[index, 'Azim_6'] = match['Azim_6'].values[0]

            # Substituir as colunas de coordenadas
            input_df.at[index, 'X_sylabs'] = match['X_sylabs'].values[0]
            input_df.at[index, 'Y_sylabs'] = match['Y_sylabs'].values[0]
            input_df.at[index, 'Z_sylabs'] = match['Z_sylabs'].values[0]
            input_df.at[index, 'X_real'] = match['X_real'].values[0]
            input_df.at[index, 'Y_real'] = match['Y_real'].values[0]
            input_df.at[index, 'Z_real'] = match['Z_real'].values[0]
        
    # Supondo que Azim_5 já exista no input_df
    colunas = list(input_df.columns)

    # Garante que Azim_6 e Azim_7 estão na lista apenas uma vez
    for col in ['Azim_6', 'Azim_7']:
        if col in colunas:
            colunas.remove(col)

    # Posição onde Azim_6 e Azim_7 devem ser inseridas (logo após Azim_5)
    pos = colunas.index('Azim_5') + 1

    # Insere Azim_6 e Azim_7 na posição correta
    colunas[pos:pos] = ['Azim_6', 'Azim_7']

    # Reordena o DataFrame
    input_df = input_df[colunas]

        
    return input_df

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

            try:
                # Processar o arquivo
                processed_df = process_file(input_file_path, reference_file_path)

                # Usar o nome do arquivo de referência para o arquivo de saída
                reference_file_name = os.path.basename(reference_file_path).replace(".csv", ".csv")
                output_file_path = os.path.join(output_folder, reference_file_name)

                # Salvar o arquivo processado no diretório de saída
                processed_df.to_csv(output_file_path, index=False)
                print(f"Arquivo processado e salvo: {output_file_path}")

            except pd.errors.ParserError as e:
                # Capturar erros de parsing e pular o arquivo
                print(f"Erro ao processar o arquivo {input_file_name}: {e}")
                continue

            except Exception as e:
                # Capturar outros erros e pular o arquivo
                print(f"Erro inesperado ao processar o arquivo {input_file_name}: {e}")
                continue

# Exemplo de uso
reference_folder = "0. Dataset/1. Static/Data"  # Substitua pelo caminho da pasta de entrada
output_folder = "0. Dataset/1. Static/Data IQ"  # Substitua pelo caminho da pasta de saída
input_folder = "0. Dataset/99. Dados DB/Com Amostras IQ/2. Mobility"  # Substitua pelo caminho da pasta de referência

#process_multiple_files(input_folder, output_folder, reference_folder)

# Adicionar Azim_6 e Azim_7 ao arquivo STC_C1P1_4T_data.csv na pasta Data IQ
specific_file_name = "STC_C1P1_4T_data.csv"

# Caminhos para o arquivo de referência e o arquivo processado
reference_file_path = os.path.join(reference_folder, specific_file_name)
output_file_path = os.path.join(output_folder, specific_file_name)

if os.path.exists(reference_file_path) and os.path.exists(output_file_path):
    # Ler os arquivos
    reference_df = pd.read_csv(reference_file_path)
    output_df = pd.read_csv(output_file_path)

    # Iterar sobre as linhas do arquivo processado
    for index, row in output_df.iterrows():
        ppe_id = row['ppeID']
        sequence_number = row['Sequence_number']

        # Filtrar o DataFrame de referência para encontrar os valores correspondentes
        match = reference_df[
            (reference_df['ppeID'] == ppe_id) &
            (reference_df['BeaconID'] == sequence_number)
        ]

        if not match.empty:
            # Adicionar os valores de Azim_6 e Azim_7
            output_df.at[index, 'Azim_6'] = match['Azim_6'].values[0]
            output_df.at[index, 'Azim_7'] = match['Azim_7'].values[0]

            # Substituir as colunas de coordenadas
            output_df.at[index, 'X_sylabs'] = match['X_sylabs'].values[0]
            output_df.at[index, 'Y_sylabs'] = match['Y_sylabs'].values[0]
            output_df.at[index, 'Z_sylabs'] = match['Z_sylabs'].values[0]
            output_df.at[index, 'X_real'] = match['X_real'].values[0]
            output_df.at[index, 'Y_real'] = match['Y_real'].values[0]
            output_df.at[index, 'Z_real'] = match['Z_real'].values[0]

    # Reordenar as colunas para que Azim_6 e Azim_7 fiquem ao lado de Azim_5
    colunas = list(output_df.columns)
    for col in ['Azim_6', 'Azim_7']:
        if col in colunas:
            colunas.remove(col)
    pos = colunas.index('Azim_5') + 1
    colunas[pos:pos] = ['Azim_6', 'Azim_7']
    output_df = output_df[colunas]

    # Salvar o arquivo atualizado
    output_df.to_csv(output_file_path, index=False)
    print(f"Colunas Azim_6, Azim_7 e coordenadas adicionadas e reordenadas em: {output_file_path}")
else:
    print(f"Arquivo de referência ou processado não encontrado para: {specific_file_name}")