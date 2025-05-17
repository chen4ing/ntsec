import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import cv2

# 建立 Matplotlib 圖像與畫布
fig, ax = plt.subplots(figsize=(4, 4), dpi=100)

# 繪製 Toyota 商標（簡化三橢圓版本）
ellipses = [
    Ellipse((0.5, 0.5), 0.6, 0.4, angle=0, fill=False, linewidth=5, edgecolor='black'),  # 水平橢圓
    Ellipse((0.5, 0.5), 0.3, 0.5, angle=0, fill=False, linewidth=5, edgecolor='black'),  # 垂直橢圓
    Ellipse((0.65, 0.5), 0.3, 0.5, angle=90, fill=False, linewidth=5, edgecolor='black') # 右側橢圓（旋轉）
]

for e in ellipses:
    ax.add_patch(e)

# 設定圖像視窗
ax.set_aspect('equal')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
plt.axis('off')

# 使用 Agg 畫布渲染圖像為 RGB 陣列
canvas = FigureCanvas(fig)
canvas.draw()
width, height = fig.get_size_inches() * fig.get_dpi()
image = np.frombuffer(canvas.tostring_rgb(), dtype='uint8')
image = image.reshape(int(height), int(width), 3)

# ✅ 關鍵：將 RGB 轉換為 OpenCV 使用的 BGR 格式
image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# 顯示轉換後的圖像（可選）
cv2.imshow("Toyota Logo (Simplified)", image_bgr)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 或儲存為圖檔
# cv2.imwrite("toyota_logo.png", image_bgr)
