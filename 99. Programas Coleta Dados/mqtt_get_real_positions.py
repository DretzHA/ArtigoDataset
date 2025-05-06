import pandas as pd
import numpy as np


def get_real_positions_movement(data_df, timestamp_df, file_name):
    # Sample data for the data and timestamp dataframes
    # You would load your dataframes instead of defining them here
   # data_df = pd.read_csv('Get Tests/teste_movimentacao_data.csv')  # Assuming your data file is named data.csv
   # timestamp_df = pd.read_csv('Get Tests/teste_movimentacao_timestamps.csv')  # Assuming your timestamp file is named timestamp.csv

    # Add a constant Z coordinate from the data_df (you can modify this if needed)
    Z_real = 1.81  # Assuming Z_real is constant for all data rows

    # Convert timestamp to datetime for better time handling
    timestamp_df['Timestamp'] = pd.to_datetime(timestamp_df['Timestamp'], unit='s')

    # Create a column to store calculated real coordinates in the data_df
    data_df['X_real'] = np.nan
    data_df['Y_real'] = np.nan
    data_df['Z_real'] = np.nan

    # file_name = input("Enter the final file name: ")

    # Loop over each row in the data dataframe
    # for i, row in data_df.iterrows():
    #     # Get the CreateTime from the data
    #     create_time = row['CreateTime']
        
    #     # Find the nearest two points in the timestamp dataframe
    #     timestamp_before = timestamp_df[timestamp_df['Timestamp'] <= pd.to_datetime(create_time, unit='s')].iloc[-1]
    #     timestamps_after = timestamp_df[timestamp_df['Timestamp'] > pd.to_datetime(create_time, unit='s')]

    #     # Check if there's at least one timestamp after
    #     if not timestamps_after.empty:
    #         timestamp_after = timestamps_after.iloc[0]
    #     else:
    #         # Handle the case where there's no timestamp after
    #         print(f"No valid timestamp after {create_time}. Skipping row {i}.")
    #         continue  # Skip processing this row
        
    #     # Calculate the time difference between the two nearest timestamps (before and after)
    #     time_diff = (timestamp_after['Timestamp'] - timestamp_before['Timestamp']).total_seconds()
        
    #     # If time difference is 0 (no time difference), skip this data point
    #     if time_diff == 0:
    #         continue
        
    #     # Calculate the distance between the points in X and Y
    #     x_diff = timestamp_after['X'] - timestamp_before['X']
    #     y_diff = timestamp_after['Y'] - timestamp_before['Y']
        
    #     # Calculate the velocity in both X and Y direction
    #     velocity_x = x_diff / time_diff
    #     velocity_y = y_diff / time_diff
        
    #     # Calculate the time difference between the CreateTime and the timestamp_before
    #     elapsed_time = (pd.to_datetime(create_time, unit='s') - timestamp_before['Timestamp']).total_seconds()
        
    #     # Estimate the real X and Y coordinates based on velocity and time difference
    #     estimated_x = timestamp_before['X'] + velocity_x * elapsed_time
    #     estimated_y = timestamp_before['Y'] + velocity_y * elapsed_time
        
    #     # Set the calculated real coordinates in the data dataframe
    #     data_df.at[i, 'X_real'] = estimated_x
    #     data_df.at[i, 'Y_real'] = estimated_y
    #     data_df.at[i, 'Z_real'] = Z_real  # Assuming Z_real is constant

    # Save the updated data_df with real coordinates
    data_df.to_csv(f"/home/andrey/Desktop/ANDREY/Pesquisa/BLE_IPS_sigivest/Datasets/Mobility/Data/{file_name}_data.csv", index=False)


