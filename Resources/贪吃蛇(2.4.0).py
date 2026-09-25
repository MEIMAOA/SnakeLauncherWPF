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

# ========== 游戏版本：v2.4.0 - 自定义背景 ==========
VERSION = "v2.4.0"
CHANGELOG = f"""版本 {VERSION} - 自定义背景

✨ 新增功能：
- 支持自定义GIF背景图片
- 若未设置图片，默认使用深色网格背景
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
GRID_SIZE = 20

MAX_SEGMENT_RADIUS = 20
RADIUS_PER_SCORE = 0.02

FOOD_COLORS = ["red", "orange", "yellow", "pink", "purple", "cyan", "lime"]

CLUSTER_RADIUS = 80
INHERIT_CENTER_PROB = 0.8

# 自定义背景图片（GIF格式）
# 请将您的图片命名为 background.gif 并放在程序同目录下，或修改为完整路径。
# 若设置为 None，则使用默认的深色背景+网格。
BACKGROUND_IMAGE = None  # 例如：BACKGROUND_IMAGE = "background.gif"

# 颜色定义（当未使用背景图片时生效）
BG_COLOR = "#1a1a1a"        # 深色背景
GRID_COLOR = "#808080"      # 灰色网格线
TEXT_COLOR = "white"        # 白色文字
BORDER_COLOR = "red"        # 红色边界框
PLAYER_HEAD_COLOR = "lightgreen"
PLAYER_BODY_COLOR = "green"
ENEMY_HEAD_COLOR = "red"
ENEMY_BODY_COLOR = "darkred"
WARNING_CIRCLE_COLOR = "white"

# ========== 平方距离函数 ==========
def dist_sq(x1, y1, x2, y2):
    dx = x1 - x2
    dy = y1 - y2
    return dx*dx + dy*dy

# ========== 初始化屏幕 ==========
screen = turtle.Screen()
screen.title(f"自由贪吃蛇 (PVE) {VERSION}")
screen.bgcolor("black")  # 临时背景，稍后可能被图片覆盖
screen.setup(width=WIDTH, height=HEIGHT)
screen.tracer(0)

# 如果设置了背景图片且文件存在，则设置图片背景
if BACKGROUND_IMAGE and os.path.exists(BACKGROUND_IMAGE):
    try:
        screen.bgpic(BACKGROUND_IMAGE)
        use_image_bg = True
    except:
        print("背景图片加载失败，使用默认背景")
        use_image_bg = False
else:
    use_image_bg = False

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

# IPC 发送定时
last_ipc_send_time = 0

# ========== 鼠标事件处理 ==========
def on_mouse_move(event):
    global mouse_x, mouse_y
    canvas = screen.getcanvas()
    turtle_x = event.x - WIDTH/2
    turtle_y = HEIGHT/2 - event.y
    if -WIDTH/2 <= turtle_x <= WIDTH/2 and -HEIGHT/2 <= turtle_y <= HEIGHT/2:
        mouse_x, mouse_y = turtle_x, turtle_y
    else:
        mouse_x, mouse_y = None, None

screen.getcanvas().bind('<Motion>', on_mouse_move)

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

# ========== 绘制函数 ==========
def draw():
    pen.clear()
    writer.clear()
    current_radius = get_segment_radius()

    if not game_started:
        # ----- 开始界面（保持白色背景）-----
        pen.penup()
        pen.goto(-WIDTH//2, -HEIGHT//2)
        pen.pendown()
        pen.color("white")
        pen.begin_fill()
        for _ in range(2):
            pen.forward(WIDTH)
            pen.left(90)
            pen.forward(HEIGHT)
            pen.left(90)
        pen.end_fill()
        pen.penup()

        writer.color("black")
        writer.goto(0, 150)
        writer.write("自由贪吃蛇", align="center", font=("Arial", 42, "bold"))

        # 示例蛇（在屏幕固定位置）
        pen.penup()
        pen.goto(-150, 50)
        pen.color("darkgreen")
        pen.begin_fill()
        pen.circle(current_radius)
        pen.end_fill()
        pen.goto(-170, 50)
        pen.color("green")
        pen.begin_fill()
        pen.circle(current_radius)
        pen.end_fill()
        pen.goto(-190, 50)
        pen.color("green")
        pen.begin_fill()
        pen.circle(current_radius)
        pen.end_fill()

        pen.goto(150, 50)
        pen.color("darkred")
        pen.begin_fill()
        pen.circle(current_radius)
        pen.end_fill()
        pen.goto(130, 50)
        pen.color("red")
        pen.begin_fill()
        pen.circle(current_radius)
        pen.end_fill()
        pen.goto(110, 50)
        pen.color("red")
        pen.begin_fill()
        pen.circle(current_radius)
        pen.end_fill()

        food_x = 0
        food_y = 0
        for i, col in enumerate(FOOD_COLORS[:5]):
            pen.goto(food_x + i*30 - 60, food_y)
            pen.color(col)
            pen.begin_fill()
            pen.circle(FOOD_RADIUS)
            pen.end_fill()

        writer.goto(0, -50)
        writer.write("鼠标移动控制方向", align="center", font=("Arial", 18, "normal"))

        if int(time.time() * 2) % 2 == 0:
            writer.goto(0, -100)
            writer.write("按 SPACE 开始游戏", align="center", font=("Arial", 22, "bold"))

        writer.goto(0, -150)
        writer.write("按 R 重新开始", align="center", font=("Arial", 18, "normal"))
        writer.goto(0, -200)
        writer.write("敌人2秒后出现，最多10个", align="center", font=("Arial", 14, "italic"))

        writer.color(TEXT_COLOR)

    else:
        # ----- 游戏画面 -----
        # 如果使用了背景图片，则不需要绘制背景和网格
        if not use_image_bg:
            # 绘制深色背景
            pen.penup()
            pen.goto(-WIDTH//2, -HEIGHT//2)
            pen.pendown()
            pen.color(BG_COLOR)
            pen.begin_fill()
            for _ in range(2):
                pen.forward(WIDTH)
                pen.left(90)
                pen.forward(HEIGHT)
                pen.left(90)
            pen.end_fill()
            pen.penup()

            # 计算摄像机视野范围，绘制网格线（只绘制视野内的，提高性能）
            left_world = cam_x - WIDTH/2
            right_world = cam_x + WIDTH/2
            bottom_world = cam_y - HEIGHT/2
            top_world = cam_y + HEIGHT/2

            pen.color(GRID_COLOR)
            pen.pensize(1)

            start_x = math.floor(left_world / GRID_SIZE) * GRID_SIZE
            end_x = math.ceil(right_world / GRID_SIZE) * GRID_SIZE
            start_y = math.floor(bottom_world / GRID_SIZE) * GRID_SIZE
            end_y = math.ceil(top_world / GRID_SIZE) * GRID_SIZE

            # 竖线
            x = start_x
            while x <= end_x:
                sx, _ = world_to_screen(x, 0)
                pen.penup()
                pen.goto(sx, -HEIGHT/2)
                pen.pendown()
                pen.goto(sx, HEIGHT/2)
                pen.penup()
                x += GRID_SIZE

            # 横线
            y = start_y
            while y <= end_y:
                _, sy = world_to_screen(0, y)
                pen.penup()
                pen.goto(-WIDTH/2, sy)
                pen.pendown()
                pen.goto(WIDTH/2, sy)
                pen.penup()
                y += GRID_SIZE

        # 绘制游戏元素（所有情况下都要绘制）
        # 玩家蛇
        for i, (x, y) in enumerate(snake):
            color = PLAYER_HEAD_COLOR if i == 0 else PLAYER_BODY_COLOR
            draw_circle(x, y, color, current_radius)
        # 敌人蛇
        for enemy in enemies:
            for i, (x, y) in enumerate(enemy['body']):
                color = ENEMY_HEAD_COLOR if i == 0 else ENEMY_BODY_COLOR
                draw_circle(x, y, color, current_radius)
        # 食物
        for fx, fy, fcolor, fr in foods:
            draw_circle(fx, fy, fcolor, fr)

        # 敌人生成预警圆圈
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

        # 绘制红色边界框
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

        # 显示信息（屏幕固定位置）
        writer.color(TEXT_COLOR)
        writer.goto(WIDTH//2 - 100, HEIGHT//2 - 30)
        writer.write(f"Score: {score}", align="center", font=("Arial", 16, "normal"))

        current_speed = get_current_speed()
        speed_text = f"Speed: {current_speed:.1f}"
        if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
            remaining = BOOST_DURATION - (time.time() - boost_start_time)
            speed_text += f" (Boost: {remaining:.1f}s)"
        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 30)
        writer.write(speed_text, align="center", font=("Arial", 12, "normal"))

        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 60)
        writer.write("长按Ctrl加速(5s限时)", align="center", font=("Arial", 10, "normal"))

        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 90)
        writer.write(f"敌人: {len(enemies)}/{MAX_ENEMIES}", align="center", font=("Arial", 12, "normal"))

        # 显示击杀数
        writer.goto(-WIDTH//2 + 100, HEIGHT//2 - 120)
        writer.write(f"击杀: {kills}", align="center", font=("Arial", 12, "normal"))

        if not game_active:
            writer.goto(0, 0)
            writer.write("GAME OVER\n按 R 重新开始", align="center", font=("Arial", 20, "bold"))

        writer.color(TEXT_COLOR)

    screen.update()

# ========== 核心游戏循环 ==========
def move():
    global snake, foods, score, game_active, direction, boosting, enemies, kills

    if not game_started:
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
    global game_started
    new_game()
    game_started = False
    draw()

def start_game():
    global game_started
    if not game_started:
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
screen.onkeypress(boost_start, "Control_L")
screen.onkeypress(boost_start, "Control_R")
screen.onkeyrelease(boost_end, "Control_L")
screen.onkeyrelease(boost_end, "Control_R")

# ========== 启动游戏 ==========
new_game()
game_started = False
draw()
screen.ontimer(move, UPDATE_DELAY)

# ========== 启动 IPC 数据发送线程 ==========
if HAS_IPC:
    # 定义管道客户端类
    class PipeClient:
        def __init__(self, pipe_name="SnakeGameFPSPipe"):
            self.pipe_name = r"\\.\pipe\\" + pipe_name
            self.handle = None
            self.connected = False
            self.lock = threading.Lock()
            self._connect()

        def _connect(self):
            if not HAS_IPC:
                return
            try:
                self.handle = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                self.connected = True
            except pywintypes.error:
                self.connected = False
                self.handle = None

        def send(self, data: str):
            if not self.connected or self.handle is None:
                return
            try:
                data_bytes = (data + "\n").encode("utf-8")
                win32file.WriteFile(self.handle, data_bytes)
            except Exception:
                self.connected = False
                self.handle = None
                self._connect()

        def close(self):
            if self.handle:
                try:
                    win32file.CloseHandle(self.handle)
                except:
                    pass
                self.handle = None
                self.connected = False

    pipe_client = None

    def send_stats(fps, score, kills, mode="classic"):
        global pipe_client
        if pipe_client is None:
            pipe_client = PipeClient()
        if pipe_client and pipe_client.connected:
            line = f"FPS:{fps},SCORE:{score},KILLS:{kills},MODE:{mode}"
            pipe_client.send(line)

    def ipc_worker():
        global pipe_client, score, kills, last_ipc_send_time
        while True:
            # 每秒发送两次
            if game_started and game_active:
                # 理论 FPS = 1000 / UPDATE_DELAY ≈ 33
                fps = int(1000 / UPDATE_DELAY)
                send_stats(fps, score, kills, game_mode)
            time.sleep(0.5)

    threading.Thread(target=ipc_worker, daemon=True).start()

turtle.done()