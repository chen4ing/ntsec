# index.py (Additions/Modifications)

# Make sure these imports are present at the top of index.py
import matplotlib.pyplot as plt
import numpy as np
import os
import multiprocessing
from functools import partial
# ... any other existing imports ...

def parse_data_file(input_path, output_path):
    var_radius = [[] for _ in range(4)]
    var_angle = [[] for _ in range(4)]
    var_radius_frame = [[] for _ in range(4)]
    var_angle_frame = [[] for _ in range(4)]
    rows = []
    frame_radius=[]
    frame_angle=[]

    with open(input_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            values = list(map(float, line.split()))
            if len(values) != 8:
                continue  # Skip invalid lines
            for i in range(4):
                var_radius[i].append(values[i*2])
                current_angle = values[i*2+1]
                if i == 1 or i == 2:  # Sensor 1 (index 1) or Sensor 2 (index 2)
                    current_angle = (current_angle + 180) % 360
                var_angle[i].append(current_angle)
            rows.append(values)

    # Ensure var_angle[0] is not empty before proceeding
    if not var_angle[0]:
        # Handle case with no data or only invalid lines
        # Append an empty frame if var_radius_frame has any data (though unlikely here)
        if any(sf for sf in var_radius_frame): # Check if any sublist in var_radius_frame is non-empty
             frame_radius.append(var_radius_frame)
             frame_angle.append(var_angle_frame)
        return frame_radius, frame_angle


    for i, angle in enumerate(var_angle[0]):
        raw_angle_difference = 0
        if i > 0:
            # Calculate the raw difference from the previous angle of sensor 0
            raw_angle_difference = abs(angle - var_angle[0][i-1])

        # Frame splitting condition: use raw_angle_difference with the 300 threshold
        if raw_angle_difference > 300:
            # If the current var_radius_frame contains data, append it as a completed frame
            if var_radius_frame[0]: # Check if sensor 0 has data; implies frame is not empty
                frame_radius.append(var_radius_frame)
                frame_angle.append(var_angle_frame)
            
            # Reset var_radius_frame and var_angle_frame for the new frame
            var_radius_frame = [[] for _ in range(4)]
            var_angle_frame = [[] for _ in range(4)]
            
            # Add the current data point to the newly started frame
            for j in range(4):
                var_radius_frame[j].append(var_radius[j][i])
                var_angle_frame[j].append(var_angle[j][i])
        else:
            # Continue with the current frame: add the current data point
            for j in range(4):
                var_radius_frame[j].append(var_radius[j][i])
                var_angle_frame[j].append(var_angle[j][i])

    # After the loop, append the last frame's data if it exists
    # Check if the first sensor's list in the last var_radius_frame has data
    if var_radius_frame[0]:
        frame_radius.append(var_radius_frame)
        frame_angle.append(var_angle_frame)

    total_frames = len(frame_radius)
    print(f"Total number of frames: {total_frames}")

    return frame_radius, frame_angle

# MODIFIED process_chan_file:
# - Takes output_dir_png as an argument.
# - Generates filename including translation parameters.
# - Returns the path of the generated PNG.
def process_chan_file(filename, 
                      input_dir, 
                      output_dir_png, # GUI will specify this
                      canvas_w_px, 
                      canvas_h_px, 
                      plot_x_half, 
                      plot_y_half, 
                      sensor_trans, # This is the translations from GUI
                      colors_sensor,
                      fixed_dpi):
    
    current_input_path = os.path.join(input_dir, filename)
    print(f"Processing file: {current_input_path} with translations: {sensor_trans}")

    all_frames_radii, all_frames_angles = parse_data_file(current_input_path, 'dummy.html')

    if not all_frames_radii or not any(any(sensor_data for sensor_data in frame_data) for frame_data in all_frames_radii):
        print(f"No data to plot for {filename}.")
        return None # Return None if no data

    os.makedirs(output_dir_png, exist_ok=True)

    fig, ax = plt.subplots(figsize=(canvas_w_px / fixed_dpi, canvas_h_px / fixed_dpi), dpi=fixed_dpi)
    fig.patch.set_facecolor('white')

    for frame_idx in range(len(all_frames_radii)):
        current_frame_radii_data = all_frames_radii[frame_idx]
        current_frame_angles_data = all_frames_angles[frame_idx]

        for sensor_idx in range(4):
            sensor_global_x_coords = []
            sensor_global_y_coords = []

            if sensor_idx < len(current_frame_radii_data) and \
               current_frame_radii_data[sensor_idx] and \
               sensor_idx < len(current_frame_angles_data) and \
               current_frame_angles_data[sensor_idx]:
                
                radii_for_sensor = current_frame_radii_data[sensor_idx]
                angles_deg_for_sensor = current_frame_angles_data[sensor_idx]
                
                tx, ty = sensor_trans[sensor_idx]

                for r, angle_deg in zip(radii_for_sensor, angles_deg_for_sensor):
                    if r <= 15.0:
                        angle_rad = np.deg2rad(angle_deg)
                        x_local = r * np.sin(angle_rad) 
                        y_local = r * np.cos(angle_rad)
                        x_global = x_local + tx
                        y_global = y_local + ty
                        sensor_global_x_coords.append(x_global)
                        sensor_global_y_coords.append(y_global)
            
            if sensor_global_x_coords and sensor_global_y_coords:
                ax.scatter(sensor_global_x_coords, sensor_global_y_coords, s=1, color=colors_sensor[sensor_idx], marker='.')
    
    ax.set_xlim(-plot_x_half, plot_x_half)
    ax.set_ylim(-plot_y_half, plot_y_half)
    ax.axis('off') 
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

    base_filename = os.path.splitext(filename)[0]
    
    trans_str_parts = []
    for t_pair in sensor_trans:
        # Format to 2 decimal places, replace '.' with 'p' (point), '-' with 'm' (minus)
        trans_str_parts.append(f"{t_pair[0]:.2f}".replace('.', 'p').replace('-', 'm'))
        trans_str_parts.append(f"{t_pair[1]:.2f}".replace('.', 'p').replace('-', 'm'))
    trans_filename_part = "_".join(trans_str_parts)

    output_png_filename = os.path.join(output_dir_png, f'{base_filename}_params_{trans_filename_part}_canvas.png')
    
    try:
        plt.savefig(output_png_filename, dpi=fixed_dpi, facecolor=fig.get_facecolor()) 
        print(f"Canvas plot saved to {output_png_filename}")
    except Exception as e:
        print(f"Error saving plot {output_png_filename}: {e}")
        plt.close(fig)
        return None # Indicate failure
    
    plt.close(fig)
    return output_png_filename

# --- Add these constants and the new function before your `if __name__ == '__main__':` block ---

DEFAULT_CANVAS_WIDTH_PX = 1280
DEFAULT_CANVAS_HEIGHT_PX = 720
DEFAULT_DPI = 100
DEFAULT_SENSOR_COLORS = ['red', 'green', 'blue', 'purple']

# Calculate default plot limits (consistent with original script logic)
# The key idea was that 15 units of world space map to the canvas width.
UNITS_TO_COVER_WIDTH = 15.0
DEFAULT_PLOT_X_LIM_HALF = UNITS_TO_COVER_WIDTH / 2.0
DEFAULT_PLOT_Y_LIM_HALF = (DEFAULT_CANVAS_HEIGHT_PX * (UNITS_TO_COVER_WIDTH / DEFAULT_CANVAS_WIDTH_PX)) / 2.0


def run_processing_for_gui(translations, selected_file_option, output_directory, input_directory="."):
    """
    Callable function from GUI to process .chan files.
    Returns path to the generated image, or None.
    `selected_file_option` can be a filename, "__FIRST__", or "__ALL__".
    """
    os.makedirs(output_directory, exist_ok=True)

    canvas_w_px = DEFAULT_CANVAS_WIDTH_PX
    canvas_h_px = DEFAULT_CANVAS_HEIGHT_PX
    fixed_dpi = DEFAULT_DPI
    plot_x_half = DEFAULT_PLOT_X_LIM_HALF
    plot_y_half = DEFAULT_PLOT_Y_LIM_HALF
    sensor_colors = DEFAULT_SENSOR_COLORS

    try:
        chan_files = [f for f in os.listdir(input_directory) if f.endswith(".chan")]
    except FileNotFoundError:
        print(f"Error: Input directory not found: {input_directory}")
        return None
        
    if not chan_files:
        print(f"No .chan files found in the input directory: {os.path.abspath(input_directory)}")
        return None
    
    chan_files.sort() 

    # files_to_process = [] # This was the start of the old block
    # if process_first_file:
    #     if chan_files:
    #         files_to_process = chan_files[:1]
    # else:
    #     # For GUI, even if "process all" is implied by unchecking,
    #     # it's better to process one (e.g., the first) for responsiveness.
    #     # The user can run the main script for batch processing.
    #     # However, the request was "可選只做第一個chan file", implying "all" is the alternative.
    #     # Let's process all sequentially if "process_first_file" is False.
    #     # The GUI will display the last image generated in this case.
    #     files_to_process = chan_files
    #     if len(files_to_process) > 1:
    #          print(f"Processing all {len(files_to_process)} files sequentially. GUI will show the last image.")

    # NEW LOGIC for files_to_process
    files_to_process = []
    if selected_file_option == "__FIRST__":
        # chan_files is guaranteed non-empty here due to prior checks
        files_to_process = chan_files[:1]
    elif selected_file_option == "__ALL__":
        files_to_process = chan_files
        if len(files_to_process) > 1: # This message is good to keep
             print(f"Processing all {len(files_to_process)} files sequentially. GUI will show the last image.")
    elif selected_file_option in chan_files:
        files_to_process = [selected_file_option]
    else:
        # This case means selected_file_option is not __FIRST__, not __ALL__, and not in chan_files
        print(f"Error: Invalid file selection or file not found: '{selected_file_option}'.")
        print(f"Available files: {', '.join(chan_files) if chan_files else 'None'}")
        return None


    if not files_to_process: # Should be caught by the logic above, but as a safeguard
        print("No files selected for processing (this may indicate an issue if .chan files exist).")
        return None

    last_image_path = None
    for chan_file_name in files_to_process:
        current_image_path = process_chan_file(
            filename=chan_file_name,
            input_dir=input_directory,
            output_dir_png=output_directory,
            canvas_w_px=canvas_w_px,
            canvas_h_px=canvas_h_px,
            plot_x_half=plot_x_half,
            plot_y_half=plot_y_half,
            sensor_trans=translations,
            colors_sensor=sensor_colors,
            fixed_dpi=fixed_dpi
        )
        if current_image_path:
            last_image_path = current_image_path
            # The old 'if process_first_file: break' logic is removed.
            # If only one file is intended (specific file or "__FIRST__"),
            # files_to_process will have only one item, and the loop runs once.
            # OLD CODE REMOVED:
            # if process_first_file: # If only first was requested, and we got an image, break.
            #      break 
            
    return last_image_path

# --- Your existing `if __name__ == '__main__':` block ---
# Ensure it uses the new constants and potentially the modified process_chan_file signature
# if you want its direct execution to also benefit from new filename format.

if __name__ == '__main__':
    input_directory = '.' 
    output_png_directory = 'output_pngs_canvas' 
    os.makedirs(output_png_directory, exist_ok=True)

    canvas_width_px = DEFAULT_CANVAS_WIDTH_PX
    canvas_height_px = DEFAULT_CANVAS_HEIGHT_PX
    dpi = DEFAULT_DPI
    
    # Use the globally defined plot limits
    plot_x_lim_half = DEFAULT_PLOT_X_LIM_HALF
    plot_y_lim_half = DEFAULT_PLOT_Y_LIM_HALF
    
    initial_translations = [
        (-7.5, -3.7),
        (7.5, 0.0),
        (7.5, 0.0),
        (-7.5, 0.0)
    ]
    sensor_colors = DEFAULT_SENSOR_COLORS
    
    chan_files = [f for f in os.listdir(input_directory) if f.endswith(".chan")]
    chan_files.sort()

    if not chan_files:
        print("No .chan files found in the input directory.")
    else:
        worker_partial = partial(process_chan_file,
                                 input_dir=input_directory,
                                 output_dir_png=output_png_directory, # CLI uses its own output dir
                                 canvas_w_px=canvas_width_px,
                                 canvas_h_px=canvas_height_px,
                                 plot_x_half=plot_x_lim_half,
                                 plot_y_half=plot_y_lim_half,
                                 sensor_trans=initial_translations, # CLI uses initial translations
                                 colors_sensor=sensor_colors,
                                 fixed_dpi=dpi)
        
        num_processes_to_use = multiprocessing.cpu_count()
        print(f"Starting parallel processing of {len(chan_files)} files using up to {num_processes_to_use} processes...")

        with multiprocessing.Pool(processes=num_processes_to_use) as pool:
            results = pool.map(worker_partial, chan_files)
        
        processed_count = sum(1 for r in results if r is not None)
        print(f"Processing complete. {processed_count}/{len(chan_files)} files generated images.")

    print("Original script execution finished.")
