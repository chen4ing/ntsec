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

# Import necessary libraries for plotting and file operations
import matplotlib.pyplot as plt
import numpy as np
import os
import multiprocessing
from functools import partial

# Worker function for processing a single .chan file
def process_chan_file(filename, 
                      input_dir, 
                      output_dir_png, 
                      canvas_w_px, 
                      canvas_h_px, 
                      plot_x_half, 
                      plot_y_half, 
                      sensor_trans, 
                      colors_sensor,
                      fixed_dpi):
    
    current_input_path = os.path.join(input_dir, filename)
    print(f"Processing file: {current_input_path}")

    all_frames_radii, all_frames_angles = parse_data_file(current_input_path, 'dummy.html')

    if not all_frames_radii:
        print(f"No data to plot for {filename}.")
        return

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
    output_png_filename = os.path.join(output_dir_png, f'{base_filename}_canvas.png')
    
    plt.savefig(output_png_filename, dpi=fixed_dpi, facecolor=fig.get_facecolor()) 
    print(f"Canvas plot saved to {output_png_filename}")
    
    plt.close(fig)

# Main execution block
if __name__ == '__main__':
    # Define the directory containing the .chan files and the output directory for PNGs
    input_directory = '.'
    output_png_directory = 'output_pngs_canvas'
    os.makedirs(output_png_directory, exist_ok=True)

    # Canvas dimensions and scaling parameters
    canvas_width_px = 1280
    canvas_height_px = 720
    units_per_pixel = 15.0 / canvas_width_px
    plot_x_extent = canvas_width_px * units_per_pixel
    plot_x_lim_half = plot_x_extent / 2.0
    plot_y_extent = canvas_height_px * units_per_pixel
    plot_y_lim_half = plot_y_extent / 2.0

    translations = [
        (-7.5, -5),
        (7.5, 0.0),
        (7.5, 0.0),
        (-7.5, 0.0)
    ]
    sensor_colors = ['red', 'green', 'blue', 'purple']
    dpi = 100 # DPI for plotting

    chan_files = [f for f in os.listdir(input_directory) if f.endswith(".chan")]

    if not chan_files:
        print("No .chan files found in the input directory.")
    else:
        worker_partial = partial(process_chan_file,
                                 input_dir=input_directory,
                                 output_dir_png=output_png_directory,
                                 canvas_w_px=canvas_width_px,
                                 canvas_h_px=canvas_height_px,
                                 plot_x_half=plot_x_lim_half,
                                 plot_y_half=plot_y_lim_half,
                                 sensor_trans=translations,
                                 colors_sensor=sensor_colors,
                                 fixed_dpi=dpi)
        
        num_processes_to_use = multiprocessing.cpu_count()
        print(f"Starting parallel processing of {len(chan_files)} files using up to {num_processes_to_use} processes...")

        with multiprocessing.Pool(processes=num_processes_to_use) as pool:
            pool.map(worker_partial, chan_files)

    print("Processing complete. All .chan files have been processed for canvas output.")