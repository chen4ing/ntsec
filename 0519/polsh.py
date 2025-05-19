import cv2
import numpy as np

def flip_and_invert_image(img: np.ndarray) -> np.ndarray:
    """
    對影像進行左右翻轉、上下翻轉以及色彩反轉。

    參數:
        img (np.ndarray): OpenCV 影像 (含 alpha channel)

    回傳:
        np.ndarray: 處理後的 OpenCV 影像
    """
    # 確認影像有 alpha channel（4 channels）
    if img.shape[2] != 4:
        raise ValueError("影像必須包含 alpha channel（RGBA, 4 channels）")

    # 左右翻轉
    flipped_lr = cv2.flip(img, 1)  # flipCode=1 => 左右翻轉

    # 上下翻轉
    flipped_ud = cv2.flip(flipped_lr, 0)  # flipCode=0 => 上下翻轉

    # 色彩反轉（對 RGBA 所有 channel 做 255 - 值）
    inverted = 255 - flipped_ud

    return inverted
