# me  –  Script TOP DAT (full, standalone, your variable names)
# ------------------------------------------------------------------
# 如果還沒安裝，先跑一次：
op('td_pip').InstallPackage('matplotlib')
#   op('td_pip').InstallPackage('opencv-python')
# ------------------------------------------------------------------
import math, cv2, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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

def _draw_frame_on_ax(ax, radii_frame, angles_frame, sensor_trans, colors_sensor):
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
        if ptsx:
            ax.scatter(ptsx, ptsy, s=1, color=colors_sensor[s], marker='.')

def frame2opencvIMG(frame_radii_data, frame_angles_data,
                    canvas_w_px, canvas_h_px,
                    plot_x_half, plot_y_half,
                    sensor_trans, colors_sensor,
                    fixed_dpi):
    fig, ax = plt.subplots(figsize=(canvas_w_px / fixed_dpi,
                                    canvas_h_px / fixed_dpi),
                           dpi=fixed_dpi)
    fig.patch.set_facecolor('white')
    _draw_frame_on_ax(ax, frame_radii_data, frame_angles_data,
                      sensor_trans, colors_sensor)
    ax.set_xlim(-plot_x_half, plot_x_half)
    ax.set_ylim(-plot_y_half, plot_y_half)
    ax.axis('off')
    plt.subplots_adjust(0, 0, 1, 1, 0, 0)
    fig.canvas.draw()
    img = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))
    plt.close(fig)
    return group_and_draw_circles(img, 5.0, 5.0, 20)

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
