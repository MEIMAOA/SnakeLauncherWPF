import turtle
import random
import math
import time
import os
import threading
import tkinter.messagebox as msgbox

# 导入 Windows 命名管道支持（需要 pywin32，如果未安装则跳过）
try:
    import win32pipe
    import win32file
    import pywintypes
    HAS_IPC = True
except ImportError:
    HAS_IPC = False

# ========== 游戏版本：v2.15.6 - 按钮文字下移10像素 ==========
VERSION = "v2.15.6"
CHANGELOG = f"""版本 {VERSION} - 按钮文字下移10像素

✨ 新增功能：
- 开始界面按钮文字在按钮内下移10像素，视觉更平衡
- 悬停效果与点击区域完全匹配
- 游戏进行中按 ESC 键可立即返回开始界面
- 所有界面文字改为微软雅黑字体
- 设置界面颜色选项显示中文
- 可自定义蛇头颜色、蛇身颜色和背景样式
- 地图5000×4000，摄像机跟随
- 鼠标移动控制方向
- 敌人AI主动觅食，持续生成（最多10个）
- 敌人死亡掉落密集红色大食物
- 速度随分数递减（初始10，500分时降至2）
- Ctrl加速（限时5秒）
- 蛇身随分数变粗
- 敌人生成预警圆圈
- 与启动器 IPC 通信，实时上报 FPS、得分、击杀数、模式

🐛 修复bug：
- 版本更新提示现在会检测版本变化
- 食物检测优化，防止快速移动跳过食物
- 性能优化，使用平方距离计算
"""

# 版本检测
version_file = os.path.join(os.path.expanduser("~"), ".snake_pve_version")
last_version = ""
if os.path.exists(version_file):
    with open(version_file, "r") as f:
        last_version = f.read().strip()
if last_version != VERSION:
    msgbox.showinfo("版本更新提示", CHANGELOG)
    with open(version_file, "w") as f:
        f.write(VERSION)

# ========== 游戏配置 ==========
WIDTH, HEIGHT = 1600, 900               # 屏幕窗口尺寸
WORLD_WIDTH, WORLD_HEIGHT = 5000, 4000  # 世界地图尺寸
WORLD_MIN_X = -WORLD_WIDTH//2
WORLD_MAX_X = WORLD_WIDTH//2
WORLD_MIN_Y = -WORLD_HEIGHT//2
WORLD_MAX_Y = WORLD_HEIGHT//2

BASE_SPEED = 10
MIN_SPEED = 2
SPEED_DECAY = 0.016
BASE_SEGMENT_RADIUS = 8
FOOD_RADIUS = 6
LARGE_FOOD_RADIUS = 10
FOOD_COUNT = 125
UPDATE_DELAY = 30
BOOST_DURATION = 5.0
BOOST_MULTIPLIER = 2.0
ENEMY_COUNT = 3
MAX_ENEMIES = 10
ENEMY_SPAWN_DELAY = 2000
ENEMY_SPAWN_INTERVAL = 5
FOOD_PER_SEGMENT = 3
ENEMY_FOOD_SEEK_PROB = 0.8
GRID_SIZE = 20                          # 棋盘格大小

MAX_SEGMENT_RADIUS = 20
RADIUS_PER_SCORE = 0.02

FOOD_COLORS = ["red", "orange", "yellow", "pink", "purple", "cyan", "lime"]

CLUSTER_RADIUS = 80
INHERIT_CENTER_PROB = 0.8

# 棋盘格颜色（用于方格背景）
BG_COLOR_LIGHT = "#FFFFFF"  # 白色
BG_COLOR_DARK = "#F0F0F0"   # 浅灰色

# 纯色背景定义
PURE_BLACK = "#000000"
PURE_WHITE = "#FFFFFF"

# 开始界面背景色（海沫绿）
START_BG_COLOR = "#C0F0E0"

# 其他元素颜色（敌人固定）
ENEMY_HEAD_COLOR = "red"
ENEMY_BODY_COLOR = "darkred"
WARNING_CIRCLE_COLOR = "white"
BORDER_COLOR = "red"
TEXT_COLOR = "white"

# 可自定义的蛇颜色选项（英文值）
HEAD_COLOR_OPTIONS = ["lightgreen", "yellow", "orange", "pink", "cyan", "white"]
BODY_COLOR_OPTIONS = ["green", "darkgreen", "blue", "purple", "brown", "gray"]

# 颜色中文映射
HEAD_COLOR_NAMES = {
    "lightgreen": "浅绿",
    "yellow": "黄",
    "orange": "橙",
    "pink": "粉",
    "cyan": "青",
    "white": "白"
}
BODY_COLOR_NAMES = {
    "green": "绿",
    "darkgreen": "深绿",
    "blue": "蓝",
    "purple": "紫",
    "brown": "棕",
    "gray": "灰"
}

DEFAULT_HEAD_COLOR = "lightgreen"
DEFAULT_BODY_COLOR = "green"

# 背景样式选项
BACKGROUND_STYLE_OPTIONS = ["纯黑", "纯白", "方格"]
BACKGROUND_STYLE_VALUES = [PURE_BLACK, PURE_WHITE, "grid"]
DEFAULT_BACKGROUND_STYLE = 2  # 默认方格

# 按钮尺寸（统一）
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 44
BUTTON_HALF_WIDTH = BUTTON_WIDTH // 2
BUTTON_HALF_HEIGHT = BUTTON_HEIGHT // 2

# ========== 平方距离函数 ==========
def dist_sq(x1, y1, x2, y2):
    dx = x1 - x2
    dy = y1 - y2
    return dx*dx + dy*dy

# ========== 初始化屏幕 ==========
screen = turtle.Screen()
screen.title(f"自由贪吃蛇 (PVE) {VERSION}")
screen.bgcolor("black")  # 临时背景
screen.setup(width=WIDTH, height=HEIGHT)
screen.tracer(0)

pen = turtle.Turtle()
pen.speed(0)
pen.penup()
pen.hideturtle()

writer = turtle.Turtle()
writer.speed(0)
writer.color(TEXT_COLOR)
writer.penup()
writer.hideturtle()

# ========== 游戏变量 ==========
snake = [(0, 0), (-16, 0), (-32, 0), (-48, 0), (-64, 0)]
direction = (1, 0)

enemies = []
foods = []  # 食物列表 (x, y, color, radius)
score = 0
kills = 0   # 新增：击杀计数
game_active = True
game_mode = "classic"  # 经典模式，固定值
game_started = False
boosting = False
boost_start_time = 0
color_centers = {}

mouse_x, mouse_y = None, None  # 屏幕坐标

cam_x, cam_y = 0, 0

pending_enemy_spawns = []
spawn_timer_active = False

# 设置相关
settings_mode = False
background_style = DEFAULT_BACKGROUND_STYLE
head_color_index = HEAD_COLOR_OPTIONS.index(DEFAULT_HEAD_COLOR)  # 当前蛇头颜色索引
body_color_index = BODY_COLOR_OPTIONS.index(DEFAULT_BODY_COLOR)  # 当前蛇身颜色索引
selected_setting = 0  # 0:背景样式, 1:蛇头颜色, 2:蛇身颜色

# 鼠标悬停相关
hover_button = None  # 当前悬停的按钮索引 (0:开始游戏, 1:设置, 2:重新开始, 3:退出)

# ========== 鼠标事件处理 ==========
def on_mouse_move(event):
    global mouse_x, mouse_y, hover_button
    # 记录鼠标位置
    turtle_x = event.x - WIDTH/2
    turtle_y = HEIGHT/2 - event.y
    if -WIDTH/2 <= turtle_x <= WIDTH/2 and -HEIGHT/2 <= turtle_y <= HEIGHT/2:
        mouse_x, mouse_y = turtle_x, turtle_y
    else:
        mouse_x, mouse_y = None, None

    # 更新悬停按钮（只在开始界面有效）
    if not game_started and not settings_mode:
        # 按钮中心Y坐标（下移15像素后的位置）
        button_y_positions = [45, -5, -55, -105]
        hover_button = None
        for i, y in enumerate(button_y_positions):
            if y - BUTTON_HALF_HEIGHT <= mouse_y <= y + BUTTON_HALF_HEIGHT and \
               -BUTTON_HALF_WIDTH <= mouse_x <= BUTTON_HALF_WIDTH:
                hover_button = i
                break
    else:
        hover_button = None

screen.getcanvas().bind('<Motion>', on_mouse_move)

# ========== 鼠标点击处理 ==========
def on_click(event):
    global settings_mode, game_started
    if settings_mode or game_started:
        return  # 只在开始界面处理点击
    x = event.x - WIDTH/2
    y = HEIGHT/2 - event.y
    button_y_positions = [45, -5, -55, -105]
    buttons = [
        {"func": start_game},
        {"func": enter_settings},
        {"func": restart},
        {"func": quit_game}
    ]
    for i, y_pos in enumerate(button_y_positions):
        if y_pos - BUTTON_HALF_HEIGHT <= y <= y_pos + BUTTON_HALF_HEIGHT and \
           -BUTTON_HALF_WIDTH <= x <= BUTTON_HALF_WIDTH:
            buttons[i]["func"]()
            break

screen.getcanvas().bind('<Button-1>', on_click)

# ========== 摄像机更新 ==========
def update_camera():
    global cam_x, cam_y
    head_x, head_y = snake[0]
    cam_x = head_x
    cam_y = head_y
    min_cam_x = WORLD_MIN_X + WIDTH/2
    max_cam_x = WORLD_MAX_X - WIDTH/2
    min_cam_y = WORLD_MIN_Y + HEIGHT/2
    max_cam_y = WORLD_MAX_Y - HEIGHT/2
    if min_cam_x < max_cam_x:
        cam_x = max(min_cam_x, min(cam_x, max_cam_x))
    if min_cam_y < max_cam_y:
        cam_y = max(min_cam_y, min(cam_y, max_cam_y))
    if min_cam_x >= max_cam_x:
        cam_x = (WORLD_MIN_X + WORLD_MAX_X) / 2
    if min_cam_y >= max_cam_y:
        cam_y = (WORLD_MIN_Y + WORLD_MAX_Y) / 2

def world_to_screen(wx, wy):
    sx = wx - cam_x
    sy = wy - cam_y
    return sx, sy

def screen_to_world(sx, sy):
    wx = sx + cam_x
    wy = sy + cam_y
    return wx, wy

# ========== 辅助函数 ==========
def get_segment_radius():
    return min(MAX_SEGMENT_RADIUS, BASE_SEGMENT_RADIUS + score * RADIUS_PER_SCORE)

def random_position(margin=50):
    x = random.randint(WORLD_MIN_X + margin, WORLD_MAX_X - margin)
    y = random.randint(WORLD_MIN_Y + margin, WORLD_MAX_Y - margin)
    return (x, y)

def create_food(color, radius=FOOD_RADIUS):
    seg_radius = get_segment_radius()
    if color in color_centers and random.random() < INHERIT_CENTER_PROB:
        center_x, center_y = color_centers[color]
    else:
        center_x, center_y = random_position(margin=CLUSTER_RADIUS+50)

    min_dist_sq = (seg_radius + radius) ** 2

    for _ in range(50):
        offset_x = random.randint(-CLUSTER_RADIUS, CLUSTER_RADIUS)
        offset_y = random.randint(-CLUSTER_RADIUS, CLUSTER_RADIUS)
        fx = center_x + offset_x
        fy = center_y + offset_y
        if fx < WORLD_MIN_X + radius or fx > WORLD_MAX_X - radius or \
           fy < WORLD_MIN_Y + radius or fy > WORLD_MAX_Y - radius:
            continue
        overlap = False
        for sx, sy in snake:
            if dist_sq(fx, fy, sx, sy) < min_dist_sq:
                overlap = True
                break
        if not overlap:
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if dist_sq(fx, fy, sx, sy) < min_dist_sq:
                        overlap = True
                        break
                if overlap:
                    break
        if not overlap:
            color_centers[color] = (fx, fy)
            return (fx, fy, color, radius)
    return None

def generate_foods(count):
    global foods
    foods = []
    for _ in range(count):
        color = random.choice(FOOD_COLORS)
        food = create_food(color, FOOD_RADIUS)
        if food:
            foods.append(food)
        else:
            pos = random_position()
            foods.append((pos[0], pos[1], color, FOOD_RADIUS))

def get_mouse_direction():
    global mouse_x, mouse_y
    if mouse_x is None or mouse_y is None:
        return direction
    wx, wy = screen_to_world(mouse_x, mouse_y)
    hx, hy = snake[0]
    dx = wx - hx
    dy = wy - hy
    if abs(dx) < 1 and abs(dy) < 1:
        return direction
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)

def check_boundary(head):
    x, y = head
    margin = get_segment_radius()
    return (x < WORLD_MIN_X + margin or x > WORLD_MAX_X - margin or
            y < WORLD_MIN_Y + margin or y > WORLD_MAX_Y - margin)

def draw_circle(x, y, color, radius):
    sx, sy = world_to_screen(x, y)
    pen.goto(sx, sy - radius)
    pen.color(color)
    pen.begin_fill()
    pen.circle(radius)
    pen.end_fill()

def get_current_speed():
    base = max(MIN_SPEED, BASE_SPEED - score * SPEED_DECAY)
    if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
        return base * BOOST_MULTIPLIER
    else:
        return base

def spawn_foods_from_enemy(enemy_body):
    global foods
    seg_radius = get_segment_radius()
    threshold_sq = (seg_radius + LARGE_FOOD_RADIUS) ** 2
    for segment in enemy_body:
        for _ in range(FOOD_PER_SEGMENT):
            for attempt in range(30):
                offset_x = random.randint(-30, 30)
                offset_y = random.randint(-30, 30)
                fx = segment[0] + offset_x
                fy = segment[1] + offset_y
                if fx < WORLD_MIN_X + LARGE_FOOD_RADIUS or fx > WORLD_MAX_X - LARGE_FOOD_RADIUS or \
                   fy < WORLD_MIN_Y + LARGE_FOOD_RADIUS or fy > WORLD_MAX_Y - LARGE_FOOD_RADIUS:
                    continue
                overlap = False
                for sx, sy in snake:
                    if dist_sq(fx, fy, sx, sy) < threshold_sq:
                        overlap = True
                        break
                if overlap:
                    continue
                for enemy in enemies:
                    for sx, sy in enemy['body']:
                        if dist_sq(fx, fy, sx, sy) < threshold_sq:
                            overlap = True
                            break
                    if overlap:
                        break
                if overlap:
                    continue
                foods.append((fx, fy, "red", LARGE_FOOD_RADIUS))
                break
            else:
                pos = random_position()
                foods.append((pos[0], pos[1], "red", LARGE_FOOD_RADIUS))

def spawn_enemies():
    global enemies, pending_enemy_spawns, spawn_timer_active
    if not game_active or not game_started:
        spawn_timer_active = False
        return
    for (x, y) in pending_enemy_spawns:
        body = [(x, y), (x - 16, y), (x - 32, y)]
        dir_options = [(1,0), (-1,0), (0,1), (0,-1)]
        dir = random.choice(dir_options)
        enemies.append({'body': body, 'dir': dir})
    pending_enemy_spawns.clear()
    spawn_timer_active = False

def periodic_enemy_spawn():
    global spawn_timer_active
    if not game_started or not game_active:
        return
    if len(enemies) < MAX_ENEMIES:
        min_dist_sq = (get_segment_radius() * 4) ** 2
        for _ in range(100):
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            overlap = False
            for sx, sy in snake:
                if dist_sq(x, y, sx, sy) < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if dist_sq(x, y, sx, sy) < min_dist_sq:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            for ex, ey in pending_enemy_spawns:
                if dist_sq(x, y, ex, ey) < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            pending_enemy_spawns.append((x, y))
            if not spawn_timer_active:
                spawn_timer_active = True
                screen.ontimer(spawn_enemies, ENEMY_SPAWN_DELAY)
            break
    screen.ontimer(periodic_enemy_spawn, ENEMY_SPAWN_INTERVAL * 1000)

def get_enemy_new_direction(enemy, foods_list):
    old_dir = enemy['dir']
    head = enemy['body'][0]

    if foods_list and random.random() < ENEMY_FOOD_SEEK_PROB:
        min_dist_sq = float('inf')
        target = None
        for fx, fy, _, fr in foods_list:
            d_sq = dist_sq(head[0], head[1], fx, fy)
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                target = (fx, fy)
        if target:
            dx = target[0] - head[0]
            dy = target[1] - head[1]
            if dx != 0 or dy != 0:
                length = math.hypot(dx, dy)
                dx /= length
                dy /= length
                if not (dx == -old_dir[0] and dy == -old_dir[1]):
                    return (dx, dy)

    options = [(1,0), (-1,0), (0,1), (0,-1)]
    opposite = (-old_dir[0], -old_dir[1])
    options = [d for d in options if d != opposite]
    if options:
        return random.choice(options)
    return old_dir

# ========== 设置相关函数 ==========
def settings_up():
    global selected_setting
    if not settings_mode:
        return
    selected_setting = (selected_setting - 1) % 3
    draw()

def settings_down():
    global selected_setting
    if not settings_mode:
        return
    selected_setting = (selected_setting + 1) % 3
    draw()

def settings_left():
    global background_style, head_color_index, body_color_index
    if not settings_mode:
        return
    if selected_setting == 0:
        background_style = (background_style - 1) % len(BACKGROUND_STYLE_OPTIONS)
    elif selected_setting == 1:
        head_color_index = (head_color_index - 1) % len(HEAD_COLOR_OPTIONS)
    else:
        body_color_index = (body_color_index - 1) % len(BODY_COLOR_OPTIONS)
    draw()

def settings_right():
    global background_style, head_color_index, body_color_index
    if not settings_mode:
        return
    if selected_setting == 0:
        background_style = (background_style + 1) % len(BACKGROUND_STYLE_OPTIONS)
    elif selected_setting == 1:
        head_color_index = (head_color_index + 1) % len(HEAD_COLOR_OPTIONS)
    else:
        body_color_index = (body_color_index + 1) % len(BODY_COLOR_OPTIONS)
    draw()

def settings_save():
    global settings_mode
    settings_mode = False
    draw()

def settings_cancel():
    global settings_mode, background_style, head_color_index, body_color_index
    background_style = DEFAULT_BACKGROUND_STYLE
    head_color_index = HEAD_COLOR_OPTIONS.index(DEFAULT_HEAD_COLOR)
    body_color_index = BODY_COLOR_OPTIONS.index(DEFAULT_BODY_COLOR)
    settings_mode = False
    draw()

def enter_settings():
    global settings_mode, selected_setting
    if not game_started and not settings_mode:
        settings_mode = True
        selected_setting = 0
        draw()

# ========== 退出函数 ==========
def quit_game():
    """退出游戏"""
    screen.bye()

# ========== ESC处理（返回开始界面）=========
def esc_pressed():
    """按下ESC：如果在游戏中，返回开始界面"""
    global game_started, settings_mode
    if game_started and not settings_mode:
        # 游戏进行中，返回开始界面
        restart()  # restart 会重置游戏并回到开始界面

# ========== 绘制函数 ==========
def draw():
    pen.clear()
    writer.clear()
    current_radius = get_segment_radius()

    if settings_mode:
        # ----- 设置界面（海沫绿背景）-----
        pen.penup()
        pen.goto(-WIDTH//2, -HEIGHT//2)
        pen.pendown()
        pen.color(START_BG_COLOR)
        pen.begin_fill()
        for _ in range(2):
            pen.forward(WIDTH)
            pen.left(90)
            pen.forward(HEIGHT)
            pen.left(90)
        pen.end_fill()
        pen.penup()

        writer.color("black")
        writer.goto(0, 250)
        writer.write("设置", align="center", font=("Microsoft YaHei", 36, "bold"))

        y = 150
        bg_text = f"背景样式: {BACKGROUND_STYLE_OPTIONS[background_style]}"
        head_color_eng = HEAD_COLOR_OPTIONS[head_color_index]
        head_text = f"蛇头颜色: {HEAD_COLOR_NAMES[head_color_eng]}"
        body_color_eng = BODY_COLOR_OPTIONS[body_color_index]
        body_text = f"蛇身颜色: {BODY_COLOR_NAMES[body_color_eng]}"
        
        items = [bg_text, head_text, body_text]
        for i, text in enumerate(items):
            if i == selected_setting:
                writer.goto(0, y)
                writer.write(f">> {text} <<", align="center", font=("Microsoft YaHei", 24, "bold"))
            else:
                writer.goto(0, y)
                writer.write(text, align="center", font=("Microsoft YaHei", 24, "normal"))
            y -= 60

        writer.goto(0, -50)
        writer.write("↑↓选择  ←→更改  Enter保存  Esc取消", align="center", font=("Microsoft YaHei", 16, "normal"))

        writer.color(TEXT_COLOR)

    elif not game_started:
        # ----- 简洁开始界面（海沫绿背景）-----
        pen.penup()
        pen.goto(-WIDTH//2, -HEIGHT//2)
        pen.pendown()
        pen.color(START_BG_COLOR)
        pen.begin_fill()
        for _ in range(2):
            pen.forward(WIDTH)
            pen.left(90)
            pen.forward(HEIGHT)
            pen.left(90)
        pen.end_fill()
        pen.penup()

        writer.color("black")
        # 标题 + 版本号
        writer.goto(0, 150)
        writer.write(f"自由贪吃蛇 {VERSION}", align="center", font=("Microsoft YaHei", 48, "bold"))

        # 定义按钮位置和文字（下移15像素后的位置）
        button_y = [45, -5, -55, -105]
        button_texts = [
            "开始游戏 (SPACE)",
            "设置 (S)",
            "重新开始 (R)",
            "退出 (Q)"
        ]
        button_fonts = [(24, "bold") if i == 0 else (18, "normal") for i in range(4)]

        for i, (y, text, font_info) in enumerate(zip(button_y, button_texts, button_fonts)):
            size, weight = font_info
            # 如果是悬停按钮，绘制填充矩形（使用统一尺寸）
            if hover_button == i:
                # 绘制填充矩形
                pen.penup()
                pen.goto(-BUTTON_HALF_WIDTH, y - BUTTON_HALF_HEIGHT)  # 左下角
                pen.pendown()
                pen.color("#C0C0C0")    # 填充色：稍深的灰色
                pen.begin_fill()
                for _ in range(2):
                    pen.forward(BUTTON_WIDTH)
                    pen.left(90)
                    pen.forward(BUTTON_HEIGHT)
                    pen.left(90)
                pen.end_fill()
                # 绘制边框（更深的灰色）
                pen.color("#808080")
                pen.pensize(2)
                pen.goto(-BUTTON_HALF_WIDTH, y - BUTTON_HALF_HEIGHT)
                pen.pendown()
                for _ in range(2):
                    pen.forward(BUTTON_WIDTH)
                    pen.left(90)
                    pen.forward(BUTTON_HEIGHT)
                    pen.left(90)
                pen.penup()
                # 文字颜色加深
                writer.color("#000000")
            else:
                writer.color("black")
            # 绘制文字（下移10像素，相对于之前上移5像素，现在改为 y - 5）
            writer.goto(0, y - 5)
            writer.write(text, align="center", font=("Microsoft YaHei", size, weight))

        writer.color(TEXT_COLOR)

    else:
        # ----- 游戏画面 -----
        bg_value = BACKGROUND_STYLE_VALUES[background_style]
        if bg_value == "grid":
            left_world = cam_x - WIDTH/2
            right_world = cam_x + WIDTH/2
            bottom_world = cam_y - HEIGHT/2
            top_world = cam_y + HEIGHT/2

            start_x = math.floor(left_world / GRID_SIZE) * GRID_SIZE
            end_x = math.ceil(right_world / GRID_SIZE) * GRID_SIZE
            start_y = math.floor(bottom_world / GRID_SIZE) * GRID_SIZE
            end_y = math.ceil(top_world / GRID_SIZE) * GRID_SIZE

            pen.penup()
            pen.pensize(1)

            x = start_x
            while x < end_x:
                y = start_y
                while y < end_y:
                    if ((x // GRID_SIZE) + (y // GRID_SIZE)) % 2 == 0:
                        pen.color(BG_COLOR_LIGHT)
                    else:
                        pen.color(BG_COLOR_DARK)
                    sx, sy = world_to_screen(x, y)
                    pen.goto(sx, sy)
                    pen.begin_fill()
                    pen.goto(sx + GRID_SIZE, sy)
                    pen.goto(sx + GRID_SIZE, sy + GRID_SIZE)
                    pen.goto(sx, sy + GRID_SIZE)
                    pen.goto(sx, sy)
                    pen.end_fill()
                    y += GRID_SIZE
                x += GRID_SIZE
        else:
            pen.penup()
            pen.goto(-WIDTH//2, -HEIGHT//2)
            pen.pendown()
            pen.color(bg_value)
            pen.begin_fill()
            for _ in range(2):
                pen.forward(WIDTH)
                pen.left(90)
                pen.forward(HEIGHT)
                pen.left(90)
            pen.end_fill()
            pen.penup()

        # 绘制游戏元素
        head_color = HEAD_COLOR_OPTIONS[head_color_index]
        body_color = BODY_COLOR_OPTIONS[body_color_index]
        for i, (x, y) in enumerate(snake):
            color = head_color if i == 0 else body_color
            draw_circle(x, y, color, current_radius)
        for enemy in enemies:
            for i, (x, y) in enumerate(enemy['body']):
                color = ENEMY_HEAD_COLOR if i == 0 else ENEMY_BODY_COLOR
                draw_circle(x, y, color, current_radius)
        for fx, fy, fcolor, fr in foods:
            draw_circle(fx, fy, fcolor, fr)

        if pending_enemy_spawns:
            for (x, y) in pending_enemy_spawns:
                sx, sy = world_to_screen(x, y)
                pen.penup()
                pen.goto(sx, sy - current_radius * 2)
                pen.pendown()
                pen.color(WARNING_CIRCLE_COLOR)
                pen.pensize(2)
                pen.circle(current_radius * 2)
                pen.penup()
            pen.pensize(1)

        pen.penup()
        left, bottom = world_to_screen(WORLD_MIN_X + current_radius, WORLD_MIN_Y + current_radius)
        right, top = world_to_screen(WORLD_MAX_X - current_radius, WORLD_MAX_Y - current_radius)
        pen.goto(left, bottom)
        pen.pendown()
        pen.color(BORDER_COLOR)
        pen.pensize(2)
        pen.setheading(0)
        pen.forward(right - left)
        pen.left(90)
        pen.forward(top - bottom)
        pen.left(90)
        pen.forward(right - left)
        pen.left(90)
        pen.forward(top - bottom)
        pen.penup()
        pen.pensize(1)

        writer.color(TEXT_COLOR)
        writer.goto(WIDTH//2 - 100, HEIGHT//2 - 30)
        writer.write(f"Score: {score}", align="center", font=("Microsoft YaHei", 16, "normal"))

        current_speed = get_current_speed()
        speed_text = f"Speed: {current_speed:.1f}"
        if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
            remaining = BOOST_DURATION - (time.time() - boost_start_time)
            speed_text += f" (Boost: {remaining:.1f}s)"
        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 30)
        writer.write(speed_text, align="center", font=("Microsoft YaHei", 12, "normal"))

        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 60)
        writer.write("长按Ctrl加速(5s限时)", align="center", font=("Microsoft YaHei", 10, "normal"))

        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 90)
        writer.write(f"敌人: {len(enemies)}/{MAX_ENEMIES}", align="center", font=("Microsoft YaHei", 12, "normal"))

        # 显示击杀数
        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 120)
        writer.write(f"击杀: {kills}", align="center", font=("Microsoft YaHei", 12, "normal"))

        if not game_active:
            writer.goto(0, 0)
            writer.write("GAME OVER\n按 R 重新开始", align="center", font=("Microsoft YaHei", 20, "bold"))

        writer.goto(WIDTH//2 - 100, -HEIGHT//2 + 50)
        writer.write(VERSION, align="center", font=("Microsoft YaHei", 10, "normal"))

        writer.color(TEXT_COLOR)

    screen.update()

# ========== 核心游戏循环 ==========
def move():
    global snake, foods, score, game_active, direction, boosting, enemies, kills

    if not game_started or settings_mode:
        draw()
        screen.ontimer(move, UPDATE_DELAY)
        return

    if not game_active:
        draw()
        screen.ontimer(move, UPDATE_DELAY)
        return

    if boosting and (time.time() - boost_start_time) >= BOOST_DURATION:
        boosting = False

    new_dir = get_mouse_direction()
    direction = new_dir

    current_speed = get_current_speed()
    current_radius = get_segment_radius()
    eat_threshold_sq = (current_radius + FOOD_RADIUS) ** 2
    large_eat_threshold_sq = (current_radius + LARGE_FOOD_RADIUS) ** 2
    collision_threshold_sq = (current_radius * 2) ** 2

    old_player_head = snake[0]
    new_player_head = (old_player_head[0] + direction[0] * current_speed,
                       old_player_head[1] + direction[1] * current_speed)

    new_enemy_heads = []
    for enemy in enemies:
        old_head = enemy['body'][0]
        new_dir = get_enemy_new_direction(enemy, foods)
        enemy['dir'] = new_dir
        new_head = (old_head[0] + new_dir[0] * current_speed,
                    old_head[1] + new_dir[1] * current_speed)
        new_enemy_heads.append((enemy, old_head, new_head))

    if check_boundary(new_player_head):
        game_active = False
        draw()
        screen.ontimer(move, UPDATE_DELAY)
        return

    surviving_enemy_heads = []
    for enemy, old_head, new_head in new_enemy_heads:
        if check_boundary(new_head):
            spawn_foods_from_enemy(enemy['body'])
            enemies.remove(enemy)
            kills += 1  # 击杀计数增加
        else:
            surviving_enemy_heads.append((enemy, old_head, new_head))

    ate_index = None
    for i, (fx, fy, _, fr) in enumerate(foods):
        if fr == FOOD_RADIUS:
            threshold_sq = eat_threshold_sq
        else:
            threshold_sq = large_eat_threshold_sq
        if dist_sq(new_player_head[0], new_player_head[1], fx, fy) < threshold_sq:
            ate_index = i
            break
        mid_x = (old_player_head[0] + new_player_head[0]) / 2
        mid_y = (old_player_head[1] + new_player_head[1]) / 2
        if dist_sq(mid_x, mid_y, fx, fy) < threshold_sq:
            ate_index = i
            break

    enemy_ate_info = []
    for enemy, old_head, new_head in surviving_enemy_heads:
        for i, (fx, fy, _, fr) in enumerate(foods):
            if fr == FOOD_RADIUS:
                threshold_sq = eat_threshold_sq
            else:
                threshold_sq = large_eat_threshold_sq
            if dist_sq(new_head[0], new_head[1], fx, fy) < threshold_sq:
                enemy_ate_info.append((enemy, i))
                break
            mid_x = (old_head[0] + new_head[0]) / 2
            mid_y = (old_head[1] + new_head[1]) / 2
            if dist_sq(mid_x, mid_y, fx, fy) < threshold_sq:
                enemy_ate_info.append((enemy, i))
                break

    foods_to_remove = set()
    if ate_index is not None:
        foods_to_remove.add(ate_index)
    for enemy, i in enemy_ate_info:
        foods_to_remove.add(i)

    snake.insert(0, new_player_head)
    if ate_index is None:
        snake.pop()
    else:
        score += 1  # 每吃一个食物加一分

    for enemy, old_head, new_head in surviving_enemy_heads:
        enemy['body'].insert(0, new_head)
        ate = any(enemy == e for e, _ in enemy_ate_info)
        if not ate:
            enemy['body'].pop()

    for i in sorted(foods_to_remove, reverse=True):
        del foods[i]

    while len(foods) < FOOD_COUNT:
        new_color = random.choice(FOOD_COLORS)
        new_food = create_food(new_color, FOOD_RADIUS)
        if new_food:
            foods.append(new_food)
        else:
            pos = random_position()
            foods.append((pos[0], pos[1], new_color, FOOD_RADIUS))

    player_head = snake[0]
    for enemy in enemies:
        for segment in enemy['body'][1:]:
            if dist_sq(player_head[0], player_head[1], segment[0], segment[1]) < collision_threshold_sq:
                game_active = False
                draw()
                screen.ontimer(move, UPDATE_DELAY)
                return

    enemies_to_remove = []
    for enemy in enemies:
        enemy_head = enemy['body'][0]
        for segment in snake[1:]:
            if dist_sq(enemy_head[0], enemy_head[1], segment[0], segment[1]) < collision_threshold_sq:
                enemies_to_remove.append(enemy)
                break
        if enemy in enemies_to_remove:
            continue
        for other in enemies:
            if other is enemy:
                continue
            for segment in other['body'][1:]:
                if dist_sq(enemy_head[0], enemy_head[1], segment[0], segment[1]) < collision_threshold_sq:
                    enemies_to_remove.append(enemy)
                    break
            if enemy in enemies_to_remove:
                break

    for e in enemies_to_remove:
        if e in enemies:
            spawn_foods_from_enemy(e['body'])
            enemies.remove(e)
            kills += 1  # 击杀计数增加

    update_camera()
    draw()
    screen.ontimer(move, UPDATE_DELAY)

# ========== 游戏控制函数 ==========
def new_game():
    global snake, direction, foods, score, kills, game_active, boosting, color_centers, enemies, pending_enemy_spawns, spawn_timer_active
    snake = [(0, 0), (-16, 0), (-32, 0), (-48, 0), (-64, 0)]
    direction = (1, 0)
    score = 0
    kills = 0
    game_active = True
    boosting = False
    color_centers.clear()
    enemies = []
    pending_enemy_spawns.clear()
    spawn_timer_active = False
    generate_foods(FOOD_COUNT)

    min_dist_sq = (get_segment_radius() * 4) ** 2
    for i in range(ENEMY_COUNT):
        for _ in range(100):
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            overlap = False
            for sx, sy in snake:
                if dist_sq(x, y, sx, sy) < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            for ex, ey in pending_enemy_spawns:
                if dist_sq(x, y, ex, ey) < min_dist_sq:
                    overlap = True
                    break
            if not overlap:
                pending_enemy_spawns.append((x, y))
                break
        else:
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            pending_enemy_spawns.append((x, y))

    if not spawn_timer_active:
        spawn_timer_active = True
        screen.ontimer(spawn_enemies, ENEMY_SPAWN_DELAY)

def restart():
    global game_started, settings_mode
    new_game()
    game_started = False
    settings_mode = False
    draw()

def start_game():
    global game_started, settings_mode
    if not game_started and not settings_mode:
        new_game()
        game_started = True
        draw()
        screen.ontimer(periodic_enemy_spawn, ENEMY_SPAWN_INTERVAL * 1000)

def boost_start():
    global boosting, boost_start_time
    if game_started and game_active:
        boosting = True
        boost_start_time = time.time()

def boost_end():
    global boosting
    boosting = False

# ========== 事件绑定 ==========
screen.listen()
screen.onkeypress(start_game, "space")
screen.onkeypress(restart, "r")
screen.onkeypress(restart, "R")
screen.onkeypress(enter_settings, "s")
screen.onkeypress(enter_settings, "S")
screen.onkeypress(quit_game, "q")
screen.onkeypress(quit_game, "Q")
screen.onkeypress(boost_start, "Control_L")
screen.onkeypress(boost_start, "Control_R")
screen.onkeyrelease(boost_end, "Control_L")
screen.onkeyrelease(boost_end, "Control_R")
# 设置界面按键
screen.onkeypress(settings_up, "Up")
screen.onkeypress(settings_down, "Down")
screen.onkeypress(settings_left, "Left")
screen.onkeypress(settings_right, "Right")
screen.onkeypress(settings_save, "Return")
screen.onkeypress(settings_cancel, "Escape")
# 全局ESC：游戏中返回开始界面
screen.onkeypress(esc_pressed, "Escape")

# ========== 启动游戏 ==========
new_game()
game_started = False
settings_mode = False
draw()
screen.ontimer(move, UPDATE_DELAY)

# ========== 启动 IPC 数据发送线程 ==========
if HAS_IPC:
    def ipc_worker():
        """后台线程：持续尝试连接启动器管道，并发送游戏状态"""
        pipe_name = r'\\.\pipe\SnakeGameFPSPipe'
        while True:
            try:
                win32pipe.WaitNamedPipe(pipe_name, win32pipe.NMPWAIT_USE_DEFAULT_WAIT)
                handle = win32file.CreateFile(
                    pipe_name,
                    win32file.GENERIC_WRITE,
                    0, None, win32file.OPEN_EXISTING, 0, None
                )
                # 连接成功，循环发送数据
                while True:
                    try:
                        # 收集当前数据（理论 FPS = 1000/UPDATE_DELAY ≈ 33）
                        fps = int(1000 / UPDATE_DELAY)
                        current_score = score
                        current_kills = kills
                        mode_str = game_mode

                        # 构造一行文本（与启动器格式完全匹配）
                        line = f"FPS:{fps},SCORE:{current_score},KILLS:{current_kills},MODE:{mode_str}\n"
                        data = line.encode()

                        win32file.WriteFile(handle, data)
                    except (pywintypes.error, BrokenPipeError, ConnectionResetError):
                        break
                    time.sleep(0.5)  # 每秒发送两次
                win32file.CloseHandle(handle)
            except Exception:
                pass
            time.sleep(2)

    threading.Thread(target=ipc_worker, daemon=True).start()

turtle.done()