# me  – this Script CHOP DAT
# scriptOp – the CHOP that is cooking
#
# 依賴：
#   1. 專案裡有一個 File In DAT，名稱為  filein1
#   2. filein1.par.file 指向你的原始 txt 資料檔
#      （parse_data_file 的格式完全沿用）                  

import os

######################################################################
# 1. 直接引用你提供的 parse_data_file()  ============================
######################################################################
def parse_data_file(input_path):
    var_radius = [[] for _ in range(4)]
    var_angle  = [[] for _ in range(4)]
    var_radius_frame = [[] for _ in range(4)]
    var_angle_frame  = [[] for _ in range(4)]
    frame_radius, frame_angle = [], []

    with open(input_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):      # 空行/註解
                continue
            values = list(map(float, line.split()))
            if len(values) != 8:                      # 略過格式錯誤列
                continue
            for i in range(4):
                var_radius[i].append(values[i*2])
                cur_ang = values[i*2+1]
                if i in (1, 2):                       # 感測器 2、3 需補 180°
                    cur_ang = (cur_ang + 180) % 360
                var_angle[i].append(cur_ang)

    if not var_angle[0]:          # 無有效資料
        return frame_radius, frame_angle

    for i, ang in enumerate(var_angle[0]):
        diff = abs(ang - var_angle[0][i-1]) if i else 0
        if diff > 300:            # 角度跳變 => 新 frame
            if var_radius_frame[0]:
                frame_radius.append(var_radius_frame)
                frame_angle.append(var_angle_frame)
            var_radius_frame = [[] for _ in range(4)]
            var_angle_frame  = [[] for _ in range(4)]

        for j in range(4):        # 加入目前點
            var_radius_frame[j].append(var_radius[j][i])
            var_angle_frame [j].append(var_angle [j][i])

    # 收尾
    if var_radius_frame[0]:
        frame_radius.append(var_radius_frame)
        frame_angle.append(var_angle_frame)

    return frame_radius, frame_angle          # 共 frame_radius[n][sensor][sample]
######################################################################
# 2. 快取結構 – 只在檔案變動時重新解析 ===============================
######################################################################
_cache = {
    'path':        None,   # 絕對路徑
    'mtime':       None,   # 最後修改時間
    'frames_r':    [],     # [[sensor][sample] …]
    'frames_a':    [],
    'frame_index': 0       # 下一次 onCook 要輸出的 frame 編號
}

def _rebuild_cache():
    """如果檔案路徑或修改時間有變就重新解析。"""
    dat       = op('filein1')
    file_path = dat.par.file.eval() if dat else ''
    if not file_path:        # 沒有資料檔
        return
    mtime = os.path.getmtime(file_path)

    if file_path != _cache['path'] or mtime != _cache['mtime']:
        _cache['frames_r'], _cache['frames_a'] = parse_data_file(file_path)
        _cache['path']        = file_path
        _cache['mtime']       = mtime
        _cache['frame_index'] = 0     # 重新開始循環

######################################################################
# 3. Script CHOP 標準回呼 ===========================================
######################################################################
def onSetupParameters(scriptOp):
    global _cache
    _cache = {
        'path':        None,   # 絕對路徑
        'mtime':       None,   # 最後修改時間
        'frames_r':    [],     # [[sensor][sample] …]
        'frames_a':    [],
        'frame_index': 0       # 下一次 onCook 要輸出的 frame 編號
    }
    return

def onPulse(par):
    return

def onCook(scriptOp):
    _rebuild_cache()            # ← 你的快取函式，保持不變
    scriptOp.clear()            # 清掉舊 channel

    frames_r = _cache['frames_r']
    frames_a = _cache['frames_a']
    if not frames_r:
        return                  # 沒資料就提早結束

    idx        = _cache['frame_index']
    r_frame    = frames_r[idx]  # [sensor][sample]
    a_frame    = frames_a[idx]

    num_samples = len(r_frame[0])
    scriptOp.numSamples = num_samples      # ① 設定長度

    for s in range(4):
        # radius channel
        ch = scriptOp.appendChan('radius{}'.format(s + 1))  # ② 建立
        ch.vals = r_frame[s]                                # ③ 填值

        # angle channel
        ch = scriptOp.appendChan('angle{}'.format(s + 1))
        ch.vals = a_frame[s]

    # 下一幀（循環播放）
    _cache['frame_index'] = (idx + 1) % len(frames_r)