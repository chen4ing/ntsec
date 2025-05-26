# me  – this Script CHOP DAT/project1/timer1
# scriptOp – the CHOP that is cooking
#
# 依賴：
#   1. 專案裡有一個 File In DAT，名稱為  filein1
#   2. filein1 內含你的原始 txt 資料
#
# -------------------------------------------------------------------

######################################################################
# 1. 解析函式：直接吃「文字行清單」而非檔案路徑  =====================
######################################################################
def parse_data_lines(lines):
    var_radius = [[] for _ in range(4)]
    var_angle  = [[] for _ in range(4)]
    var_radius_frame = [[] for _ in range(4)]
    var_angle_frame  = [[] for _ in range(4)]
    frame_radius, frame_angle = [], []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):          # 空行/註解
            continue
        values = list(map(float, line.split()))
        if len(values) != 8:                          # 略過格式錯誤列
            continue
        for i in range(4):
            var_radius[i].append(values[i*2])
            cur_ang = values[i*2+1]
            if i in (1, 2):                           # 感測器 2、3 需補 180°
                cur_ang = (cur_ang + 180) % 360
            var_angle[i].append(cur_ang)

    if not var_angle[0]:                              # 無有效資料
        return frame_radius, frame_angle

    for i, ang in enumerate(var_angle[0]):
        diff = abs(ang - var_angle[0][i-1]) if i else 0
        if diff > 300:                                # 角度跳變 => 新 frame
            if var_radius_frame[0]:
                frame_radius.append(var_radius_frame)
                frame_angle.append(var_angle_frame)
            var_radius_frame = [[] for _ in range(4)]
            var_angle_frame  = [[] for _ in range(4)]

        for j in range(4):                            # 加入目前點
            var_radius_frame[j].append(var_radius[j][i])
            var_angle_frame [j].append(var_angle [j][i])

    if var_radius_frame[0]:                           # 收尾
        frame_radius.append(var_radius_frame)
        frame_angle.append(var_angle_frame)

    return frame_radius, frame_angle                  # frame_radius[n][sensor][sample]

######################################################################
# 2. 全域狀態：只留一個 frame_index 來決定輸出哪一幀 ================
######################################################################
frame_index = 0      # 由 onCook 負責遞增（循環播放）

######################################################################
# 3. Script CHOP 標準回呼 ==========================================
######################################################################
def onSetupParameters(scriptOp):
    print("這是一個除錯訊息，錄製光達回放起始")
    global frame_index
    frame_index = 0
    return

def onPulse(par):
    return

def onCook(scriptOp):
    print(".")
    global frame_index
    dat = op('filein1')
    if not dat:
        return                        # 找不到檔，直接結束

    # 直接從 DAT 取得文字並解析
    lines = dat.text.splitlines()
    frames_r, frames_a = parse_data_lines(lines)
    if not frames_r:
        return                        # 無資料

    idx        = frame_index % len(frames_r)
    r_frame    = frames_r[idx]        # [sensor][sample]
    a_frame    = frames_a[idx]

    num_samples = len(r_frame[0])
    scriptOp.clear()
    scriptOp.numSamples = num_samples

    for s in range(4):
        # radius channel
        ch = scriptOp.appendChan(f'radius{s + 1}')
        ch.vals = r_frame[s]

        # angle channel
        ch = scriptOp.appendChan(f'angle{s + 1}')
        ch.vals = a_frame[s]

    frame_index += 1                  # 下一幀（循環播放）
