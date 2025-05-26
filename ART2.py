# TouchDesigner Web Server DAT

import json
import cv2
import numpy as np

# ===== 圓形偵測 =====
# ===== 圓形偵測（最終版，兼容舊版 TD） =====
def detect_circles(top_name='null1'):
    top = op(top_name)
    if not top or not top.valid:
        return []                                # 找不到 TOP

    # 取 numpy array，float32, 0~1
    arr = top.numpyArray(delayed=False)
    if arr is None or arr.size == 0:
        return []                                # TOP 還沒出畫面

    # 轉成 uint8 0~255，OpenCV 才吃得下
    img = (arr * 255).clip(0, 255).astype(np.uint8)   # shape (H, W, 4)

    h, w = img.shape[:2]

    # 灰階 + 去噪
    gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)     # (H, W) uint8
    gray = cv2.medianBlur(gray, 5)

    # Hough 圓形偵測
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(10, int(min(h, w) * 0.05)),
        param1=100,
        param2=30,
        minRadius=5,
        maxRadius=0)

    pts = []
    if circles is not None:
        for x, y, r in np.round(circles[0]).astype(int):
            pts.append([x / w, y / h])           # 0~1 正規化
    return pts


# ===== HTTP (保持原本功能) =====
def onHTTPRequest(webServerDAT, request, response):
    response['statusCode'] = 200
    response['statusReason'] = 'OK'
    response['data'] = '<b>TouchDesigner: </b>' + webServerDAT.name
    return response


# ===== WebSocket callbacks =====
def onWebSocketOpen(webServerDAT, client, uri):
    return

def onWebSocketClose(webServerDAT, client):
    return

def onWebSocketReceiveText(webServerDAT, client, data):
    msg = data.strip().lower()
    if msg == 'detect':                          # 客戶端固定送 detect
        pts = detect_circles()                   # [[nx, ny], ...]
        webServerDAT.webSocketSendText(client, json.dumps(pts))
    else:
        # 其他訊息照原樣回傳
        webServerDAT.webSocketSendText(client, data)
    return

def onWebSocketReceiveBinary(webServerDAT, client, data):
    webServerDAT.webSocketSendBinary(client, data)
    return

def onWebSocketReceivePing(webServerDAT, client, data):
    webServerDAT.webSocketSendPong(client, data=data)
    return

def onWebSocketReceivePong(webServerDAT, client, data):
    return

def onServerStart(webServerDAT):
    return

def onServerStop(webServerDAT):
    return
