import os
import pandas as pd
import numpy as np
import math
import shutil

# Define input and output directories
input_folder = "0. Dataset Original/2. Mobility/Data IQ"  
output_folder = "0. Dataset com Mascara Virtual/2. Mobility/Data IQ"  

# Define the azimuth angle range for each anchor (Azim_1 to Azim_7) in degrees
azimuth_ranges_deg = {
    "Azim_1": (75, 180),    # Replace with the specific range for Azim_1
    "Azim_2": (-180, -90),  # Replace with the specific range for Azim_2
    "Azim_3": (0, 180),     # Replace with the specific range for Azim_3
    "Azim_6": None          # Special condition for Azim_6
}

# Convert ranges to radians (skip Azim_6 since it has a special condition)
azimuth_ranges_rad = {
    key: (math.radians(min_angle), math.radians(max_angle))
    for key, value in azimuth_ranges_deg.items() if value is not None
    for min_angle, max_angle in [value]
}

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Iterate through all files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):  # Process only CSV files
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Check if the file name contains "ORT"
        if "ORT" in filename:
            # Copy the file directly to the output folder
            shutil.copy(input_path, output_path)
            continue

        # Load the CSV file into a DataFrame
        df = pd.read_csv(input_path)

        # Apply the mask to azimuth columns
        for i in range(1, 8):  # Columns Azim_1 to Azim_7
            column_name = f"Azim_{i}"
            if column_name in df.columns:
                if column_name == "Azim_2":
                    # Special condition for Azim_2: reject angles between -75 and 90
                    df[column_name] = df[column_name].apply(
                        lambda x: x if not (math.radians(-75) <= x <= math.radians(90)) else np.nan
                    )
                elif column_name == "Azim_6":
                    # Special condition for Azim_6: abs(angle) > 90
                    df[column_name] = df[column_name].apply(
                        lambda x: x if abs(x) > math.radians(90) else np.nan
                    )
                elif column_name in azimuth_ranges_rad:
                    # Apply range-based mask for other azimuths with defined ranges
                    min_angle, max_angle = azimuth_ranges_rad[column_name]
                    df[column_name] = df[column_name].apply(
                        lambda x: x if min_angle <= x <= max_angle else np.nan
                    )
                else:
                    # Skip filtering for Azim_4, Azim_5, and Azim_7
                    continue

        # Save the modified DataFrame to the output folder
        df.to_csv(output_path, index=False)
