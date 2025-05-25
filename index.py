# index.py (Additions/Modifications)

# Pure OpenCV and numpy implementation - no matplotlib dependency
import numpy as np
import os
import multiprocessing
from functools import partial
import imageio # Added for video creation
import cv2

def group_and_draw_circles(img: np.ndarray, x_pct: float, y_pct: float, r: int) -> np.ndarray:
    """
    Processes an image by neglecting edge regions and grouping non-white pixels into clusters based on circle overlap.
    Args:
        img (np.ndarray): Input OpenCV image (grayscale or BGR).
        x_pct (float): Percentage of width to neglect on left and right edges (0-100).
        y_pct (float): Percentage of height to neglect on top and bottom edges (0-100).
        r (int): Radius of circles to draw and cluster.
    Returns:
        np.ndarray: Output image with drawn circles at cluster centroids.
    """
    #print("這有在跑嗎?")
    # Make a copy for output
    output = img.copy()
    h, w = img.shape[:2]
    # Compute margins in pixels
    dx = int(w * x_pct / 100.0)
    dy = int(h * y_pct / 100.0)
    x0, x1 = dx, w - dx
    y0, y1 = dy, h - dy
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Neglect percentages too large, resulting in empty region.")

    # Create a binary mask of non-white pixels
    if img.ndim == 3:
        # Color image: any channel not white
        mask = np.any(img != 255, axis=2)
    else:
        # Grayscale
        mask = img < 255

    # Crop the mask to neglect edges
    mask_crop = mask[y0:y1, x0:x1]
    # Build full-size mask with neglected edges zeroed
    mask_full = np.zeros_like(mask)
    mask_full[y0:y1, x0:x1] = mask_crop

    # Dilate to merge circles of radius r
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1, 2*r+1))
    mask_dilated = cv2.dilate(mask_full.astype(np.uint8), kernel)

    # Find connected components in the dilated mask
    num_labels, labels = cv2.connectedComponents(mask_dilated)

    # Ensure output is BGR for drawing colored circles
    if output.ndim == 2:
        output = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)

    # For each component (excluding background), compute centroid and draw circle
    for label in range(1, num_labels):
        ys, xs = np.where((labels == label) & mask_full)
        if xs.size == 0:
            continue
        cx = int(xs.mean())
        cy = int(ys.mean())
        cv2.circle(output, (cx, cy), r, (0, 0, 255), 2)

    # Save a debug PNG of the output image for inspection
    # debug_dir = "debug_pngs"
    # os.makedirs(debug_dir, exist_ok=True)
    # debug_path = os.path.join(debug_dir, "grouped_circles_debug.png")
    # cv2.imwrite(debug_path, output)
    # print(f"Debug PNG saved to {debug_path}")

    return output



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
    # Suppress print for CLI video generation, can be re-enabled if needed for GUI
    # print(f"Total number of frames: {total_frames}")

    return frame_radius, frame_angle

# NEW HELPER FUNCTION to process sensor data for drawing
def _process_sensor_data(frame_radii_data, frame_angles_data, sensor_trans):
    """
    Process sensor data and return global coordinates for all sensors.
    Returns a list of (x_coords, y_coords) for each sensor.
    """
    sensor_coords = []
    
    for sensor_idx in range(4):
        sensor_global_x_coords = []
        sensor_global_y_coords = []

        if sensor_idx < len(frame_radii_data) and \
           frame_radii_data[sensor_idx] and \
           sensor_idx < len(frame_angles_data) and \
           frame_angles_data[sensor_idx]:
        
            radii_for_sensor = frame_radii_data[sensor_idx]
            angles_deg_for_sensor_data = frame_angles_data[sensor_idx]
            tx, ty = sensor_trans[sensor_idx]

            for r, angle_deg in zip(radii_for_sensor, angles_deg_for_sensor_data):
                if r <= 15.0: # Distance threshold
                    angle_rad = np.deg2rad(angle_deg)
                    x_local = r * np.sin(angle_rad) 
                    y_local = r * np.cos(angle_rad)
                    x_global = x_local + tx
                    y_global = y_local + ty
                    sensor_global_x_coords.append(x_global)
                    sensor_global_y_coords.append(y_global)
        
        sensor_coords.append((sensor_global_x_coords, sensor_global_y_coords))
    
    return sensor_coords

def _world_to_pixel(x_world, y_world, canvas_w_px, canvas_h_px, plot_x_half, plot_y_half):
    """
    Convert world coordinates to pixel coordinates.
    """
    # Normalize world coordinates to [0, 1]
    x_norm = (x_world + plot_x_half) / (2 * plot_x_half)
    y_norm = (y_world + plot_y_half) / (2 * plot_y_half)
    
    # Convert to pixel coordinates (note: y is flipped for image coordinates)
    x_pixel = int(x_norm * canvas_w_px)
    y_pixel = int((1 - y_norm) * canvas_h_px)  # Flip y-axis
    
    # Clamp to valid pixel range
    x_pixel = max(0, min(canvas_w_px - 1, x_pixel))
    y_pixel = max(0, min(canvas_h_px - 1, y_pixel))
    
    return x_pixel, y_pixel

def _get_color_bgr(color_name):
    """
    Convert color name to BGR tuple for OpenCV.
    """
    color_map = {
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'purple': (128, 0, 128),
        'black': (0, 0, 0),
        'white': (255, 255, 255)
    }
    return color_map.get(color_name, (0, 0, 0))  # Default to black

# NEW FUNCTION to generate an OpenCV image for one frame
def frame2opencvIMG(frame_radii_data, 
                    frame_angles_data, 
                    canvas_w_px, 
                    canvas_h_px, 
                    plot_x_half, 
                    plot_y_half, 
                    sensor_trans, 
                    colors_sensor, 
                    fixed_dpi):
    """
    Generates an image (NumPy array) for a single frame's data using pure OpenCV.
    """
    # Create white background image
    image = np.full((canvas_h_px, canvas_w_px, 3), 255, dtype=np.uint8)
    
    # Process sensor data to get coordinates
    sensor_coords = _process_sensor_data(frame_radii_data, frame_angles_data, sensor_trans)
    
    # Draw points for each sensor
    for sensor_idx, (x_coords, y_coords) in enumerate(sensor_coords):
        if x_coords and y_coords:
            color_bgr = _get_color_bgr(colors_sensor[sensor_idx])
            
            for x_world, y_world in zip(x_coords, y_coords):
                x_pixel, y_pixel = _world_to_pixel(x_world, y_world, canvas_w_px, canvas_h_px, plot_x_half, plot_y_half)
                # Draw a small circle for each point (radius=1 for small dots)
                cv2.circle(image, (x_pixel, y_pixel), 1, color_bgr, -1)
    
    return group_and_draw_circles(image, 5.0, 5.0, 20)

# MODIFIED process_chan_file:
# - Takes output_dir_png as an argument.
# - Generates filename including translation parameters.
# - Returns the path of the generated PNG or a list of image arrays for video.
# - Added 'mode' argument: 'png' or 'video_frames'
def process_chan_file(filename, 
                      input_dir, 
                      output_dir, # Generic output directory
                      canvas_w_px, 
                      canvas_h_px, 
                      plot_x_half, 
                      plot_y_half, 
                      sensor_trans, 
                      colors_sensor,
                      fixed_dpi,
                      mode='png'): # 'png' or 'video_frames'
    
    current_input_path = os.path.join(input_dir, filename)
    # Suppress print for CLI video generation
    # print(f"Processing file: {current_input_path} with translations: {sensor_trans}")

    all_frames_radii, all_frames_angles = parse_data_file(current_input_path, 'dummy.html')

    if not all_frames_radii or not any(any(sensor_data for sensor_data in frame_data) for frame_data in all_frames_radii):
        print(f"No data to plot for {filename}.")
        return None 

    os.makedirs(output_dir, exist_ok=True)

    base_filename = os.path.splitext(filename)[0]
    
    trans_str_parts = []
    for t_pair in sensor_trans:
        trans_str_parts.append(f"{t_pair[0]:.2f}".replace('.', 'p').replace('-', 'm'))
        trans_str_parts.append(f"{t_pair[1]:.2f}".replace('.', 'p').replace('-', 'm'))
    trans_filename_part = "_".join(trans_str_parts)

    if mode == 'png':
        # Create white background image
        image = np.full((canvas_h_px, canvas_w_px, 3), 255, dtype=np.uint8)
        
        # Process all frames and overlay them on the same image
        for frame_idx in range(len(all_frames_radii)):
            current_frame_radii_data = all_frames_radii[frame_idx]
            current_frame_angles_data = all_frames_angles[frame_idx]

            # Process sensor data to get coordinates
            sensor_coords = _process_sensor_data(current_frame_radii_data, current_frame_angles_data, sensor_trans)
            
            # Draw points for each sensor
            for sensor_idx, (x_coords, y_coords) in enumerate(sensor_coords):
                if x_coords and y_coords:
                    color_bgr = _get_color_bgr(colors_sensor[sensor_idx])
                    
                    for x_world, y_world in zip(x_coords, y_coords):
                        x_pixel, y_pixel = _world_to_pixel(x_world, y_world, canvas_w_px, canvas_h_px, plot_x_half, plot_y_half)
                        # Draw a small circle for each point (radius=1 for small dots)
                        cv2.circle(image, (x_pixel, y_pixel), 1, color_bgr, -1)
        
        output_png_filename = os.path.join(output_dir, f'{base_filename}_params_{trans_filename_part}_canvas.png')
        
        try:
            cv2.imwrite(output_png_filename, image)
            print(f"Canvas plot saved to {output_png_filename}")
        except Exception as e:
            print(f"Error saving plot {output_png_filename}: {e}")
            return None
        
        return output_png_filename
    
    elif mode == 'video_frames':
        image_frames = []
        total_data_frames = len(all_frames_radii)
        print(f"Generating {total_data_frames} frames for video from {filename}...")

        for frame_idx in range(total_data_frames):
            current_frame_radii_data = all_frames_radii[frame_idx]
            current_frame_angles_data = all_frames_angles[frame_idx]
            
            # Call frame2opencvIMG to get the image for the current frame
            image = frame2opencvIMG(current_frame_radii_data,
                                    current_frame_angles_data,
                                    canvas_w_px,
                                    canvas_h_px,
                                    plot_x_half,
                                    plot_y_half,
                                    sensor_trans,
                                    colors_sensor,
                                    fixed_dpi)
            image_frames.append(image)
            
            # Progress indicator
            print(f"  Processed frame {frame_idx + 1}/{total_data_frames}", end='\\r')
        print("\\nVideo frames generated.") # Original had \\n, keeping consistent for now. Consider changing to \n.
        return image_frames

# --- Add these constants and the new function before your `if __name__ == '__main__':` block ---

DEFAULT_CANVAS_WIDTH_PX = 1280
DEFAULT_CANVAS_HEIGHT_PX = 720
DEFAULT_DPI = 100
DEFAULT_SENSOR_COLORS = ['red', 'green', 'blue', 'purple']

# Calculate default plot limits (consistent with original script logic)
# The key idea was that 15 units of world space map to the canvas width.
UNITS_TO_COVER_WIDTH = 6.7*2
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
        # GUI always generates PNGs (overlay)
        current_image_path = process_chan_file(
            filename=chan_file_name,
            input_dir=input_directory,
            output_dir=output_directory, # output_directory is output_dir_png for GUI
            canvas_w_px=canvas_w_px,
            canvas_h_px=canvas_h_px,
            plot_x_half=plot_x_half,
            plot_y_half=plot_y_half,
            sensor_trans=translations,
            colors_sensor=sensor_colors,
            fixed_dpi=fixed_dpi,
            mode='png' 
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

def create_video_from_frames(image_frames, output_video_path, fps=10):
    """
    Creates a video from a list of image frames.
    """
    if not image_frames:
        print("No frames to create video.")
        return None
    
    try:
        with imageio.get_writer(output_video_path, fps=fps) as writer:
            for frame in image_frames:
                writer.append_data(frame)
        print(f"Video saved to {output_video_path}")
        return output_video_path
    except Exception as e:
        print(f"Error creating video {output_video_path}: {e}")
        return None

# --- Your existing `if __name__ == '__main__':` block ---
# This block will now be minimal, as CLI logic moves to cli.py
# It can be used for testing or if you still want a default direct run behavior
# without CLI arguments.

if __name__ == '__main__':
    # This part is mostly for legacy direct execution or simple testing.
    # For CLI functionality, use cli.py
    print("Running index.py directly. This is for basic testing or legacy use.")
    print("For CLI options (-p, -v), please run cli.py.")

    # Example: Process the first .chan file found into a PNG in a default directory
    input_dir = '.'
    output_png_dir = 'output_pngs_canvas_direct_run'
    os.makedirs(output_png_dir, exist_ok=True)

    default_translations = [
        (-6.7, -2.7+1), (6.7, 1.0+1),
        (6.7, -2.7+1), (-6.7, 1.0+1)
    ]
    
    try:
        chan_files = [f for f in os.listdir(input_dir) if f.endswith(".chan")]
        chan_files.sort()
        if chan_files:
            first_file = chan_files[0]
            print(f"Processing first file found: {first_file} as an example.")
            process_chan_file(
                filename=first_file,
                input_dir=input_dir,
                output_dir=output_png_dir,
                canvas_w_px=DEFAULT_CANVAS_WIDTH_PX,
                canvas_h_px=DEFAULT_CANVAS_HEIGHT_PX,
                plot_x_half=DEFAULT_PLOT_X_LIM_HALF,
                plot_y_half=DEFAULT_PLOT_Y_LIM_HALF,
                sensor_trans=default_translations,
                colors_sensor=DEFAULT_SENSOR_COLORS,
                fixed_dpi=DEFAULT_DPI,
                mode='png'
            )
        else:
            print("No .chan files found in the current directory for direct run example.")
    except Exception as e:
        print(f"Error during direct run: {e}")

    print("Direct execution of index.py finished.")
