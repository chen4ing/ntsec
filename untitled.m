% 參數設定
width = 1280;
height = 720;
numCircles = 6;
radius = 30;
duration = 30; % 秒
fps = 30;
totalFrames = duration * fps;

% 初始化影片物件
v = VideoWriter('DVD_bouncing.mp4', 'MPEG-4');
v.FrameRate = fps;
open(v);

% 初始化圓的座標與速度
positions = [...
    rand(numCircles,1)*(width - 2*radius) + radius, ...
    rand(numCircles,1)*(height - 2*radius) + radius];
velocities = (rand(numCircles,2)-0.5) * 10; % 每個圓的隨機速度

% 建立圖形視窗
fig = figure('Color', 'black', 'Position', [100, 100, width, height]);
axis off
set(gca, 'Position', [0 0 1 1]);
hold on;

% 繪製初始圓
h = gobjects(numCircles,1);
for i = 1:numCircles
    h(i) = rectangle('Position', [positions(i,1)-radius, positions(i,2)-radius, radius*2, radius*2], ...
                     'Curvature', [1, 1], ...
                     'FaceColor', 'w', ...
                     'EdgeColor', 'none');
end
xlim([0 width]);
ylim([0 height]);

% 主迴圈
for frame = 1:totalFrames
    for i = 1:numCircles
        % 更新位置
        positions(i,:) = positions(i,:) + velocities(i,:);

        % 碰撞檢查：左右邊界
        if positions(i,1) - radius < 0 || positions(i,1) + radius > width
            velocities(i,1) = -velocities(i,1);
        end
        % 上下邊界
        if positions(i,2) - radius < 0 || positions(i,2) + radius > height
            velocities(i,2) = -velocities(i,2);
        end

        % 更新圖形
        set(h(i), 'Position', [positions(i,1)-radius, positions(i,2)-radius, radius*2, radius*2]);
    end

    % 畫面更新與寫入影片
    drawnow;
    frameData = getframe(fig);
    writeVideo(v, frameData);
end

% 完成
close(v);
close(fig);
disp('影片完成：DVD_bouncing.mp4');
