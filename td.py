# me  –  Script TOP DAT (full, standalone, your variable names)
import math, cv2, numpy as np
# ───────────────────  HELPERS  ──────────────────────────────────
def group_and_draw_circles(img: np.ndarray, x_pct: float, y_pct: float, r: int) -> np.ndarray:
    h, w  = img.shape[:2]
    dx, dy = int(w*x_pct/100), int(h*y_pct/100)
    mask   = np.any(img != 255, axis=2)
    mask_crop = mask[dy:h-dy, dx:w-dx]
    mask_full = np.zeros_like(mask); mask_full[dy:h-dy, dx:w-dx] = mask_crop
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1, 2*r+1))
    _, labels = cv2.connectedComponents(cv2.dilate(mask_full.astype(np.uint8), kernel))
    out = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    for lab in range(1, labels.max()+1):
        ys, xs = np.where((labels == lab) & mask_full)
        if xs.size:
            cv2.circle(out, (int(xs.mean()), int(ys.mean())), r, (0, 0, 255), 2)
    return out

#def _draw_frame_on_ax(ax, radii_frame, angles_frame, sensor_trans, colors_sensor):
def _process_sensor_data(radii_frame, angles_frame, sensor_trans):
    sensor_coords = []
    for s in range(4):
        if not radii_frame[s]:
            continue
        tx, ty = sensor_trans[s]
        ptsx, ptsy = [], []
        for r, ang_deg in zip(radii_frame[s], angles_frame[s]):
            if r > 15.0:
                continue
            a = math.radians(ang_deg)
            ptsx.append(r * math.sin(a) + tx)
            ptsy.append(r * math.cos(a) + ty)
        #if ptsx:
        #    ax.scatter(ptsx, ptsy, s=1, color=colors_sensor[s], marker='.')
        sensor_coords.append((ptsx, ptsy))
    return sensor_coords

# 新的
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
# 新的
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

def frame2opencvIMG(frame_radii_data, frame_angles_data,
                    canvas_w_px, canvas_h_px,
                    plot_x_half, plot_y_half,
                    sensor_trans, colors_sensor,
                    fixed_dpi):
    # 舊的
    # fig, ax = plt.subplots(figsize=(canvas_w_px / fixed_dpi,
    #                                 canvas_h_px / fixed_dpi),
    #                        dpi=fixed_dpi)
    # fig.patch.set_facecolor('white')
    # _draw_frame_on_ax(ax, frame_radii_data, frame_angles_data,
    #                   sensor_trans, colors_sensor)
    # ax.set_xlim(-plot_x_half, plot_x_half)
    # ax.set_ylim(-plot_y_half, plot_y_half)
    # ax.axis('off')
    # plt.subplots_adjust(0, 0, 1, 1, 0, 0)
    # fig.canvas.draw()
    # img = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    # img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))
    # plt.close(fig)
    # return group_and_draw_circles(img, 5.0, 5.0, 20)
    # 新的
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

# ───────────────────  PARAM STUB  ───────────────────────────────
def onSetupParameters(scriptOp):
    # 無自訂參數
    return

# ───────────────────  MAIN COOK  ────────────────────────────────
def onCook(scriptOp):
    # 1️⃣  逐支感測器抓資料 —— 你要的變數名稱
    chop = op('hokuyo1')
    r_vals_1 = chop['radius'].vals
    a_vals_1 = chop['angle'].vals

    chop = op('hokuyo2')
    r_vals_2 = chop['radius'].vals
    a_vals_2 = chop['angle'].vals

    chop = op('hokuyo3')
    r_vals_3 = chop['radius'].vals
    a_vals_3 = chop['angle'].vals

    chop = op('hokuyo4')
    r_vals_4 = chop['radius'].vals
    a_vals_4 = chop['angle'].vals

    # 2️⃣  把四組資料組成函式需要的 list
    radii_frame  = [r_vals_1, r_vals_2, r_vals_3, r_vals_4]
    angles_frame = [a_vals_1, a_vals_2, a_vals_3, a_vals_4]

    # 3️⃣  固定參數
    W, H   = 1920,1080#1280, 720
    DPI    = 100
    plot_x_half = 6.7
    plot_y_half = 6.7 * H / W
    sensor_trans = [(-6.7, -1.7), (6.7, 1.0),
                    (6.7, -1.7), (-6.7, 1.0)]
    colors_sensor = ['red', 'green', 'blue', 'purple']

    # 4️⃣  產生影像→傳給 Script TOP
    img_bgr = frame2opencvIMG(radii_frame, angles_frame,
                              W, H, plot_x_half, plot_y_half,
                              sensor_trans, colors_sensor, DPI)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    scriptOp.copyNumpyArray(img_rgb)
    return
