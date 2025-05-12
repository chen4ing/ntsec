import argparse
import os
import multiprocessing
from functools import partial
import sys

# Add the parent directory to sys.path to allow imports from index.py
# This assumes cli.py is in the same directory as index.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from index import (
        process_chan_file,
        create_video_from_frames,
        DEFAULT_CANVAS_WIDTH_PX,
        DEFAULT_CANVAS_HEIGHT_PX,
        DEFAULT_DPI,
        DEFAULT_SENSOR_COLORS,
        DEFAULT_PLOT_X_LIM_HALF,
        DEFAULT_PLOT_Y_LIM_HALF
    )
except ImportError as e:
    print(f"Error importing from index.py: {e}")
    print("Make sure index.py is in the same directory as cli.py or in the Python path.")
    sys.exit(1)

def parse_translations(trans_str):
    """Parses a translation string like 'x1,y1;x2,y2;...' into a list of tuples."""
    if not trans_str:
        return None
    try:
        pairs = trans_str.split(';')
        translations = []
        for pair in pairs:
            x_str, y_str = pair.split(',')
            translations.append((float(x_str), float(y_str)))
        if len(translations) != 4:
            raise ValueError("Exactly 4 translation pairs are required.")
        return translations
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid format for translations: {e}. Expected 'x1,y1;x2,y2;x3,y3;x4,y4'")

def main():
    parser = argparse.ArgumentParser(description="Process .chan files to generate PNGs or videos.")
    parser.add_argument('--input_dir', type=str, default=".",
                        help="Directory containing .chan files (default: current directory).")
    parser.add_argument('--output_dir', type=str, default=None,
                        help="Base directory for output files (default: 'output_pngs_cli' or 'output_videos_cli').")
    parser.add_argument('--file', type=str, default="__ALL__",
                        help="Which .chan file(s) to process. Can be a specific filename, '__ALL__', or '__FIRST__' (default: __ALL__).")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--png', action='store_true', help="Generate overlaid PNG images.")
    group.add_argument('-v', '--video', action='store_true', help="Generate videos (per frame, no overlay).")

    parser.add_argument('--fps', type=int, default=10, help="FPS for generated videos (default: 10).")
    parser.add_argument('--translations', type=parse_translations, default=None,
                        help="Sensor translations as a string: 'x1,y1;x2,y2;x3,y3;x4,y4'. Uses default if not provided.")

    args = parser.parse_args()

    # Determine input files
    try:
        all_chan_files = sorted([f for f in os.listdir(args.input_dir) if f.endswith(".chan")])
    except FileNotFoundError:
        print(f"Error: Input directory not found: {args.input_dir}")
        sys.exit(1)

    if not all_chan_files:
        print(f"No .chan files found in {os.path.abspath(args.input_dir)}")
        sys.exit(1)

    files_to_process = []
    if args.file == "__ALL__":
        files_to_process = all_chan_files
    elif args.file == "__FIRST__":
        if all_chan_files:
            files_to_process = all_chan_files[:1]
    elif args.file in all_chan_files:
        files_to_process = [args.file]
    else:
        print(f"Error: Specified file '{args.file}' not found in {args.input_dir} or is not a valid keyword (__ALL__, __FIRST__).")
        print(f"Available files: {', '.join(all_chan_files)}")
        sys.exit(1)

    if not files_to_process:
        print("No files selected for processing.")
        sys.exit(0)

    # Determine translations
    if args.translations:
        sensor_translations = args.translations
    else:
        sensor_translations = [ # Default translations from index.py or your preference
            (-6.7, -2.7+0.7), (6.7, 1.0+0.7),
            (6.7, -2.7+0.7), (-6.7, 1.0+0.7)
        ]

    # Common parameters for process_chan_file
    common_params = {
        'input_dir': args.input_dir,
        'canvas_w_px': DEFAULT_CANVAS_WIDTH_PX,
        'canvas_h_px': DEFAULT_CANVAS_HEIGHT_PX,
        'plot_x_half': DEFAULT_PLOT_X_LIM_HALF,
        'plot_y_half': DEFAULT_PLOT_Y_LIM_HALF,
        'sensor_trans': sensor_translations,
        'colors_sensor': DEFAULT_SENSOR_COLORS,
        'fixed_dpi': DEFAULT_DPI
    }

    if args.png:
        output_png_dir = args.output_dir if args.output_dir else 'output_pngs_cli'
        os.makedirs(output_png_dir, exist_ok=True)
        print(f"Generating PNGs in {os.path.abspath(output_png_dir)}")

        worker_partial = partial(process_chan_file,
                                 **common_params,
                                 output_dir=output_png_dir,
                                 mode='png')
        
        num_processes_to_use = min(multiprocessing.cpu_count(), len(files_to_process))
        if num_processes_to_use > 0:
            print(f"Starting parallel PNG processing of {len(files_to_process)} files using up to {num_processes_to_use} processes...")
            with multiprocessing.Pool(processes=num_processes_to_use) as pool:
                results = pool.map(worker_partial, files_to_process)
            processed_count = sum(1 for r in results if r is not None)
            print(f"PNG Processing complete. {processed_count}/{len(files_to_process)} files generated images.")
        else:
            print("No files to process for PNG generation.")

    elif args.video:
        output_video_dir = args.output_dir if args.output_dir else 'output_videos_cli'
        os.makedirs(output_video_dir, exist_ok=True)
        print(f"Generating videos in {os.path.abspath(output_video_dir)}, FPS: {args.fps}")

        for chan_file in files_to_process:
            print(f"Processing {chan_file} for video...")
            image_frames = process_chan_file(
                filename=chan_file,
                **common_params,
                output_dir=output_video_dir, # Not strictly used by video_frames mode for saving individual plot images
                mode='video_frames'
            )

            if image_frames:
                base_filename = os.path.splitext(chan_file)[0]
                # Include translation parameters in video filename for uniqueness if desired
                trans_str_parts = []
                for t_pair in sensor_translations:
                    trans_str_parts.append(f"{t_pair[0]:.2f}".replace('.', 'p').replace('-', 'm'))
                    trans_str_parts.append(f"{t_pair[1]:.2f}".replace('.', 'p').replace('-', 'm'))
                trans_filename_part = "_".join(trans_str_parts)
                
                output_video_path = os.path.join(output_video_dir, f'{base_filename}_params_{trans_filename_part}_fps{args.fps}.mp4')
                
                create_video_from_frames(image_frames, output_video_path, fps=args.fps)
            else:
                print(f"No frames generated for {chan_file}, skipping video creation.")
        print("Video processing complete.")

if __name__ == '__main__':
    # Ensure matplotlib does not try to use GUI backend in multiprocessing
    # This might be needed on some systems, especially if run from environments
    # where a GUI backend might be implicitly selected.
    import matplotlib
    matplotlib.use('Agg') 
    main()
