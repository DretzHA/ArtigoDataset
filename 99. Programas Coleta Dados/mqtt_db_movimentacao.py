import os
import json
import asyncio
import asyncpg
import pandas as pd
import paho.mqtt.client as mqtt
import threading
import time
import numpy as np
from dotenv import load_dotenv
from datetime import timedelta
import mqtt_get_real_positions as get_real_positions

# Global variables
data_anchors = []
data_positions = []
data_timeouts = []
is_collecting = True  # Data collection starts immediately
exit_program = False
conn_pool = None
real_x = np.nan
real_y = np.nan
real_z = np.nan

# Predefined list of (X, Y) positions
coordinates_list = [
    (-1.14, 0.39), #C1P1
    # (-2.34, 0.39), #C1P2
    # (-3.54, 0.39), #C1P3
    # (-4.74, 0.39), #C1P4
    # (-5.94, 0.39), #C1P5
    # (-7.14, 0.84), #C4P1
    # (-7.14, 2.04), #C4P2
    # (-7.14, 3.24), #C4P3
    # (-7.14, 4.44), #C4P4
    # (-5.94, 4.44), #C2P5
    # (-4.74, 4.44), #C2P4
    # (-3.54, 4.44), #C2P3
    # (-2.34, 4.44), #C2P2
    # (-1.14, 4.44), #C2P1
    # (-2.34, 4.44), #C2P2
    # (-3.54, 4.44), #C2P3
    # (-4.74, 4.44), #C2P4
    # (-5.94, 4.44), #C2P5
    # (-7.14, 4.44), #C4P4
    # (-7.14, 5.64), #C4P5
    # (-7.14, 6.84), #C4P6
    # (-5.94, 6.84), #C3P5
    # (-4.74, 6.84), #C3P4
    # (-3.54, 6.84), #C3P3
    # (-2.34, 6.84), #C3P2
    (-1.14, 6.84)  #C3P1

]  # Example positions, replace with your actual coordinates - ROTA M - Saindo Ancora 02

# coordinates_list = coordinates_list[::-1] #order contraria
# Timestamp logging DataFrame
timestamp_data = pd.DataFrame(columns=["Timestamp", "Point", "X", "Y"])
current_point = 1  # Counter for the Point column

# Global lock for synchronizing access to shared data structures
real_coordinates_lock = threading.Lock()
timestamp_lock = threading.Lock()

# Database setup
async def create_pool():
    global conn_pool
    if conn_pool is None:
        conn_pool = await asyncpg.create_pool()

async def start_test_in_db(test_name, description):
    async with conn_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "DELETE FROM sigivest.test_annotations WHERE test_name = $1",
                test_name,
            )
            result = await connection.fetchrow(
                """
                INSERT INTO sigivest.test_annotations (test_name, description, start_time)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                RETURNING *;
                """,
                test_name,
                description,
            )
    return result

async def end_test_in_db(test_name):
    async with conn_pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE sigivest.test_annotations
            SET end_time = CURRENT_TIMESTAMP
            WHERE test_name = $1;
            """,
            test_name,
        )

# MQTT Callbacks
def on_connection(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"Failed to connect: {rc}")

def on_message(client, userdata, message):
    global is_collecting, real_x, real_y, real_z
    if is_collecting:
        topic_parts = message.topic.split('/')
        if message.topic.startswith("silabs/aoa/angle_and_iq_report"):
            anchor_id = topic_parts[3]
            ppe_id = topic_parts[-1]
            angles_dict = json.loads(message.payload)
            with real_coordinates_lock:
                # Update message with NaN for real coordinates
                angles_dict.update(
                    {'receive_time': pd.Timestamp.now(), 'anchor_id': anchor_id, 'ppe_id': ppe_id,
                     'x_real': real_x, 'y_real': real_y, 'z_real': real_z}
                )
            data_anchors.append(angles_dict)
        elif message.topic.startswith("silabs/aoa/position"):
            ppe_id = topic_parts[-1]
            position_dict = json.loads(message.payload)
            position_dict.update(
                {'receive_time': pd.Timestamp.now(), 'ppe_id': ppe_id}
            )
            data_positions.append(position_dict)
        elif message.topic.startswith("silabs/data/periodic_sync_report"):
            ppe_id = topic_parts[-1]
            anchor_id = topic_parts[-2]
            timeouts_dict = json.loads(message.payload)
            create_time_unix = (
                pd.to_datetime(pd.Timestamp.now())  # Convert to datetime
                + timedelta(hours=3)  # Add 3 hours
                ).timestamp()  # Convert to Unix timestamp
            
            timeouts_dict.update(
                {'receive_time': create_time_unix, 'ppe_id': ppe_id, 'anchor_id': anchor_id}
            )
            data_timeouts.append(timeouts_dict)

# Unified input listener
async def handle_user_input():
    global timestamp_data, current_point, exit_program
    print("Type 'exit' to stop data collection and finalize the test. Press Enter to log the current timestamp.")
    while not exit_program:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input)
        if user_input.strip().lower() == 'exit':
            exit_program = True
        else:
            with timestamp_lock:
                if current_point <= len(coordinates_list):
                    # Fetch the corresponding (X, Y) position
                    x, y = coordinates_list[current_point - 1]  # 0-based index for list
                else:
                    # Stop if no more coordinates are available
                    print("No more coordinates available. Stopping the test.")
                    exit_program = True
                    break
                # Log the timestamp with (X, Y) coordinates
                current_time = time.time()  # Current time in Unix format
                new_entry = {"Timestamp": current_time, "Point": current_point, "X": x, "Y": y}
                timestamp_data = pd.concat([timestamp_data, pd.DataFrame([new_entry])], ignore_index=True)
                current_point += 1
            print(f"Logged: {new_entry}")

            # Stop if last coordinate has been assigned
            if current_point > len(coordinates_list):
                print("All positions logged. Exiting program.")
                exit_program = True

# Create DataFrame
def create_dataframe(df_anchors, df_positions):
    anchor_mapping = {
        'ble-pd-0C4314F469CC': 4,
        'ble-pd-0C4314F46B26': 3,
        'ble-pd-0C4314F46B3F': 2,
        'ble-pd-0C4314F46CC2': 1,
        'ble-pd-C299A0EB1D6C' : 5,
        'ble-pd-D299A0EB1D6C' : 7,
        'ble-pd-639AA0EB1D6C' : 6
    }
    rows = []
    df_merged = pd.merge(
        df_anchors, df_positions[['sequence', 'ppe_id', 'x', 'y', 'z']], on=['sequence', 'ppe_id'], how='left'
    )
    grouped = df_merged.groupby(['sequence', 'ppe_id'])
    for (sequence, ppe_id), group in grouped:
        create_time_unix = (
            pd.to_datetime(group['receive_time'].iloc[0])  # Convert to datetime
            + timedelta(hours=3)  # Add 3 hours
        ).timestamp()  # Convert to Unix timestamp
        
        row = {
            'CreateTime': create_time_unix,
            'ppeID': ppe_id,
            'BeaconID': sequence,
            'Channel': group['channel'].iloc[0],
            **{f'RSSI_{i+1}': np.nan for i in range(7)},
            **{f'Azim_{i+1}': np.nan for i in range(7)},
            **{f'Elev_{i+1}': np.nan for i in range(7)},
            'X_sylabs': group['x'].iloc[0],
            'Y_sylabs': group['y'].iloc[0],
            'Z_sylabs': group['z'].iloc[0],
            'X_real': group['x_real'].iloc[0],
            'Y_real': group['y_real'].iloc[0],
            'Z_real': group['z_real'].iloc[0]
        }
        for _, anchor_data in group.iterrows():
            anchor_id = anchor_data['anchor_id']
            if anchor_id in anchor_mapping:
                idx = anchor_mapping[anchor_id]
                row[f'RSSI_{idx}'] = anchor_data['rssi']
                row[f'Azim_{idx}'] = np.radians(anchor_data['azimuth'])
                row[f'Elev_{idx}'] = np.radians(anchor_data['elevation'])
        rows.append(row)
    return pd.DataFrame(rows)

# Main function
async def main():
    global is_collecting, exit_program, timestamp_data, current_point
    
    load_dotenv()
    await create_pool()

    test_name = input("Enter test name: ")
    description = 'ver tabela'
    
    print("Starting data collection...")
    test_record = await start_test_in_db(test_name, description)

    # Log the first timestamp
    with timestamp_lock:
        x, y = coordinates_list[current_point - 1]  # 0-based index for list
        current_time = time.time()
        new_entry = {"Timestamp": current_time, "Point": current_point, "X": x, "Y": y}
        timestamp_data = pd.concat([timestamp_data, pd.DataFrame([new_entry])], ignore_index=True)
        current_point += 1
    print(f"Logged start: {new_entry}")


    client = mqtt.Client(client_id="MQTT_Test_Manager", clean_session=True)
    client.on_connect = on_connection
    client.on_message = on_message
    client.connect("103.0.1.31")
    client.subscribe("silabs/aoa/angle_and_iq_report/+/#")
    client.subscribe("silabs/aoa/position/positioning-LabSC/#")
    client.subscribe("silabs/data/periodic_sync_report/+/#")
    client.loop_start()

    input_task = asyncio.create_task(handle_user_input())

    try:
        while not exit_program:
            await asyncio.sleep(1)
            # Auto-end if all coordinates have been assigned
            if current_point > len(coordinates_list):
                print("All predefined coordinates have been logged. Exiting program.")
                exit_program = True
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()

        await end_test_in_db(test_name)

        if data_anchors and data_positions:
            df_anchors = pd.DataFrame(data_anchors)
            df_positions = pd.DataFrame(data_positions)
            final_df = create_dataframe(df_anchors, df_positions)
            final_df = final_df.sort_values(by='CreateTime')
            # final_df.to_csv(f"Get Tests/{test_name}_data.csv", index=False)
            # print(f"Data saved to {test_name}_data.csv")
        
        if not timestamp_data.empty:
            print()
            # timestamp_data.to_csv(f"Get Tests/{test_name}_timestamps.csv", index=False)
            # print(f"Timestamps saved to {test_name}_timestamps.csv")

        get_real_positions.get_real_positions_movement(final_df, timestamp_data, test_name)
        df_timeouts = pd.DataFrame(data_timeouts)
        df_timeouts.to_csv(f"/home/andrey/Desktop/ANDREY/Pesquisa/BLE_IPS_sigivest/Datasets/Mobility/PeriodicSync/{test_name}_data.csv", index=False)
        print("Program exited.")

if __name__ == "__main__":
    asyncio.run(main())
