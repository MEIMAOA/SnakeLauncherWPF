import turtle
import random
import math
import time
import os
import tkinter.messagebox as msgbox

# ========== 游戏版本：v2.0.0 ==========
VERSION = "v2.0.0"
CHANGELOG = f"""版本 {VERSION} 更新内容：

✨ 新增功能：
- 鼠标跟随控制，自由移动
- 敌人AI主动觅食
- 敌人持续生成，最多10个
- 敌人死亡掉落密集红色大食物
- 速度随分数递减（初始10，500分时降至2）
- Ctrl加速（限时5秒）
- 蛇身随分数变粗
- 敌人生成预警圆圈
- 开始界面优化（白色背景、示例图标、闪烁提示）

🐛 修复bug：
- 无敌模式取消
- 食物检测优化，防止快速移动跳过食物
- 性能优化，使用平方距离计算
- 界面颜色自定义（白色背景、灰色网格等）
- 多次修复启动时显示GAME OVER的问题
- 网格密集度调整、最终移除网格
"""

# 首次运行显示版本更新提示
version_file = os.path.join(os.path.expanduser("~"), ".snake_pve_version")
if not os.path.exists(version_file):
    msgbox.showinfo("版本更新提示", CHANGELOG)
    with open(version_file, "w") as f:
        f.write(VERSION)

# ========== 游戏配置 ==========
WIDTH, HEIGHT = 1280, 720          # 游戏窗口尺寸（16:9）
BASE_SPEED = 10                     # 初始移动速度（像素/帧）
MIN_SPEED = 2                       # 最低移动速度
SPEED_DECAY = 0.016                  # 每得1分速度减少量（分数达到500时速度降至2）
BASE_SEGMENT_RADIUS = 8              # 蛇身基础半径
FOOD_RADIUS = 6                      # 普通食物半径
LARGE_FOOD_RADIUS = 10                # 敌人掉落的红色大食物半径
FOOD_COUNT = 125                      # 普通食物总数（固定）
UPDATE_DELAY = 30                     # 游戏循环刷新间隔（毫秒）
BOOST_DURATION = 5.0                   # Ctrl加速持续时间（秒）
BOOST_MULTIPLIER = 2.0                 # 加速倍数
ENEMY_COUNT = 3                        # 初始敌人数量
MAX_ENEMIES = 10                       # 最大敌人数量
ENEMY_SPAWN_DELAY = 2000               # 敌人生成预警到实际出现的时间（毫秒）
ENEMY_SPAWN_INTERVAL = 5               # 新敌人生成的间隔（秒）
FOOD_PER_SEGMENT = 3                    # 敌人死亡时每个身体段掉落的食物数量
ENEMY_FOOD_SEEK_PROB = 0.8              # 敌人追踪食物的概率（剩余20%随机转向）

MAX_SEGMENT_RADIUS = 20                 # 蛇身最大半径
RADIUS_PER_SCORE = 0.02                 # 每得1分半径增加量（半径 = min(20, 8 + 分数*0.02)）

FOOD_COLORS = ["red", "orange", "yellow", "pink", "purple", "cyan", "lime"]  # 普通食物可选颜色

CLUSTER_RADIUS = 80                     # 食物聚集时中心点附近的最大偏移
INHERIT_CENTER_PROB = 0.8                # 食物生成时沿用同色上次中心点的概率

# ========== 平方距离函数（避免开方提升性能）==========
def dist_sq(x1, y1, x2, y2):
    """返回两点间的平方距离"""
    dx = x1 - x2
    dy = y1 - y2
    return dx*dx + dy*dy

# ========== 初始化屏幕 ==========
screen = turtle.Screen()
screen.title(f"自由贪吃蛇 (PVE) {VERSION}")
screen.bgcolor("black")                 # 初始背景黑色，开始界面会覆盖为白色
screen.setup(width=WIDTH, height=HEIGHT)
screen.tracer(0)                        # 关闭自动刷新，手动控制

# 画笔：用于绘制所有图形
pen = turtle.Turtle()
pen.speed(0)
pen.penup()
pen.hideturtle()

# 写字笔：用于显示文字信息
writer = turtle.Turtle()
writer.speed(0)
writer.color("white")
writer.penup()
writer.hideturtle()

# ========== 游戏变量 ==========
snake = [(0, 0), (-16, 0), (-32, 0), (-48, 0), (-64, 0)]  # 玩家蛇身体坐标（头部索引0）
direction = (1, 0)                      # 玩家当前移动方向（单位向量）

enemies = []                            # 敌人蛇列表，每个元素为 {'body': [(x,y)...], 'dir': (dx,dy)}
foods = []                               # 食物列表，每个元素为 (x, y, color, radius)
score = 0
game_active = True                       # 游戏是否正在进行（未结束）
game_started = False                     # 游戏是否已经开始（用于区分开始界面和游戏画面）
boosting = False                         # 是否处于加速状态
boost_start_time = 0                      # 加速开始时间
color_centers = {}                        # 记录每种颜色的食物聚集中心点 {color: (x,y)}

mouse_x, mouse_y = None, None             # 当前鼠标位置（turtle坐标系）

pending_enemy_spawns = []                 # 等待生成的敌人坐标（预警圆圈位置）
spawn_timer_active = False                 # 防止重复设置生成定时器

# ========== 鼠标事件处理 ==========
def on_mouse_move(event):
    """鼠标移动事件，记录鼠标在turtle坐标系中的位置"""
    global mouse_x, mouse_y
    canvas = screen.getcanvas()
    # 将窗口像素坐标转换为turtle坐标（原点在中心，y向上）
    turtle_x = event.x - WIDTH/2
    turtle_y = HEIGHT/2 - event.y
    # 仅当鼠标在窗口内时才记录坐标
    if -WIDTH/2 <= turtle_x <= WIDTH/2 and -HEIGHT/2 <= turtle_y <= HEIGHT/2:
        mouse_x, mouse_y = turtle_x, turtle_y
    else:
        mouse_x, mouse_y = None, None

screen.getcanvas().bind('<Motion>', on_mouse_move)

# ========== 辅助函数 ==========
def get_segment_radius():
    """根据当前分数计算蛇身半径（分数越高越粗）"""
    return min(MAX_SEGMENT_RADIUS, BASE_SEGMENT_RADIUS + score * RADIUS_PER_SCORE)

def random_position(margin=50):
    """生成一个位于窗口内的随机坐标，距离边缘至少margin像素"""
    x = random.randint(-WIDTH//2 + margin, WIDTH//2 - margin)
    y = random.randint(-HEIGHT//2 + margin, HEIGHT//2 - margin)
    return (x, y)

def create_food(color, radius=FOOD_RADIUS):
    """
    生成一个指定颜色和半径的食物，利用聚集规则。
    返回 (x, y, color, radius) 或 None（生成失败时）
    """
    seg_radius = get_segment_radius()
    # 决定中心点：有一定概率沿用上次该颜色的中心点，否则随机新中心点
    if color in color_centers and random.random() < INHERIT_CENTER_PROB:
        center_x, center_y = color_centers[color]
    else:
        center_x, center_y = random_position(margin=CLUSTER_RADIUS+50)

    min_dist_sq = (seg_radius + radius) ** 2  # 与蛇的最小距离平方阈值

    for _ in range(50):  # 最多尝试50次
        offset_x = random.randint(-CLUSTER_RADIUS, CLUSTER_RADIUS)
        offset_y = random.randint(-CLUSTER_RADIUS, CLUSTER_RADIUS)
        fx = center_x + offset_x
        fy = center_y + offset_y
        # 边界检查
        if fx < -WIDTH//2 + radius or fx > WIDTH//2 - radius or \
           fy < -HEIGHT//2 + radius or fy > HEIGHT//2 - radius:
            continue
        overlap = False
        # 检查是否与玩家蛇重叠
        for sx, sy in snake:
            if dist_sq(fx, fy, sx, sy) < min_dist_sq:
                overlap = True
                break
        if not overlap:
            # 检查是否与敌人蛇重叠
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if dist_sq(fx, fy, sx, sy) < min_dist_sq:
                        overlap = True
                        break
                if overlap:
                    break
        if not overlap:
            # 生成成功，更新颜色中心点
            color_centers[color] = (fx, fy)
            return (fx, fy, color, radius)
    return None  # 尝试失败

def generate_foods(count):
    """生成指定数量的普通食物（随机颜色）"""
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
    """根据鼠标位置计算从蛇头指向鼠标的单位方向向量"""
    global mouse_x, mouse_y
    if mouse_x is None or mouse_y is None:
        return direction  # 鼠标不在窗口内，保持原方向
    hx, hy = snake[0]
    dx = mouse_x - hx
    dy = mouse_y - hy
    if abs(dx) < 1 and abs(dy) < 1:
        return direction  # 鼠标就在头上，保持原方向
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)

def check_boundary(head):
    """检测头部是否碰到边界（考虑当前蛇身半径）"""
    x, y = head
    margin = get_segment_radius()
    return (x < -WIDTH//2 + margin or x > WIDTH//2 - margin or
            y < -HEIGHT//2 + margin or y > HEIGHT//2 - margin)

def draw_circle(x, y, color, radius):
    """在指定位置画一个填充圆"""
    pen.goto(x, y - radius)
    pen.color(color)
    pen.begin_fill()
    pen.circle(radius)
    pen.end_fill()

def get_current_speed():
    """计算当前移动速度（基础速度随分数递减，再考虑加速状态）"""
    base = max(MIN_SPEED, BASE_SPEED - score * SPEED_DECAY)
    if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
        return base * BOOST_MULTIPLIER
    else:
        return base

def spawn_foods_from_enemy(enemy_body):
    """
    敌人死亡时，在每个身体段附近生成红色大食物（数量 = FOOD_PER_SEGMENT）
    允许食物堆叠，形成密集效果
    """
    global foods
    seg_radius = get_segment_radius()
    threshold_sq = (seg_radius + LARGE_FOOD_RADIUS) ** 2
    for segment in enemy_body:
        for _ in range(FOOD_PER_SEGMENT):
            for attempt in range(30):  # 每个食物尝试30次生成
                offset_x = random.randint(-30, 30)
                offset_y = random.randint(-30, 30)
                fx = segment[0] + offset_x
                fy = segment[1] + offset_y
                # 边界检查
                if fx < -WIDTH//2 + LARGE_FOOD_RADIUS or fx > WIDTH//2 - LARGE_FOOD_RADIUS or \
                   fy < -HEIGHT//2 + LARGE_FOOD_RADIUS or fy > HEIGHT//2 - LARGE_FOOD_RADIUS:
                    continue
                overlap = False
                # 检查是否与玩家蛇重叠
                for sx, sy in snake:
                    if dist_sq(fx, fy, sx, sy) < threshold_sq:
                        overlap = True
                        break
                if overlap:
                    continue
                # 检查是否与敌人蛇重叠
                for enemy in enemies:
                    for sx, sy in enemy['body']:
                        if dist_sq(fx, fy, sx, sy) < threshold_sq:
                            overlap = True
                            break
                    if overlap:
                        break
                if overlap:
                    continue
                # 不与现有食物检查重叠（允许堆叠）
                foods.append((fx, fy, "red", LARGE_FOOD_RADIUS))
                break
            else:
                # 尝试失败，在随机位置生成一个兜底食物
                pos = random_position()
                foods.append((pos[0], pos[1], "red", LARGE_FOOD_RADIUS))

def spawn_enemies():
    """将 pending_enemy_spawns 中的预警点转换为实际敌人"""
    global enemies, pending_enemy_spawns, spawn_timer_active
    if not game_active or not game_started:
        spawn_timer_active = False
        return
    for (x, y) in pending_enemy_spawns:
        # 创建一条长度为3的小蛇
        body = [(x, y), (x - 16, y), (x - 32, y)]
        dir_options = [(1,0), (-1,0), (0,1), (0,-1)]
        dir = random.choice(dir_options)
        enemies.append({'body': body, 'dir': dir})
    pending_enemy_spawns.clear()
    spawn_timer_active = False

def periodic_enemy_spawn():
    """定期检查并生成新的敌人生成点（预警圆圈）"""
    global spawn_timer_active
    if not game_started or not game_active:
        return
    if len(enemies) < MAX_ENEMIES:
        min_dist_sq = (get_segment_radius() * 4) ** 2  # 与其他蛇的最小距离阈值
        for _ in range(100):
            x = random.randint(-WIDTH//2 + 100, WIDTH//2 - 100)
            y = random.randint(-HEIGHT//2 + 100, HEIGHT//2 - 100)
            overlap = False
            # 不与玩家蛇重叠
            for sx, sy in snake:
                if dist_sq(x, y, sx, sy) < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            # 不与现有敌人重叠
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if dist_sq(x, y, sx, sy) < min_dist_sq:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            # 不与已有生成点重叠
            for ex, ey in pending_enemy_spawns:
                if dist_sq(x, y, ex, ey) < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            # 找到合适位置，添加生成点
            pending_enemy_spawns.append((x, y))
            if not spawn_timer_active:
                spawn_timer_active = True
                screen.ontimer(spawn_enemies, ENEMY_SPAWN_DELAY)
            break
    # 继续定时检查
    screen.ontimer(periodic_enemy_spawn, ENEMY_SPAWN_INTERVAL * 1000)

def get_enemy_new_direction(enemy, foods_list):
    """
    敌人AI决策：
    - 以 ENEMY_FOOD_SEEK_PROB 概率朝向最近的食物移动
    - 否则随机转向
    - 禁止直接反向
    """
    old_dir = enemy['dir']
    head = enemy['body'][0]

    if foods_list and random.random() < ENEMY_FOOD_SEEK_PROB:
        # 寻找最近的食物（平方距离）
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
                if not (dx == -old_dir[0] and dy == -old_dir[1]):  # 不是反向
                    return (dx, dy)

    # 随机转向（排除反向）
    options = [(1,0), (-1,0), (0,1), (0,-1)]
    opposite = (-old_dir[0], -old_dir[1])
    options = [d for d in options if d != opposite]
    if options:
        return random.choice(options)
    return old_dir

# ========== 绘制函数 ==========
def draw():
    """根据游戏状态绘制画面（开始界面或游戏画面）"""
    pen.clear()
    writer.clear()
    current_radius = get_segment_radius()

    if not game_started:
        # ----- 开始界面（白色背景）-----
        # 绘制白色背景
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

        writer.color("black")  # 文字设为黑色

        # 标题
        writer.goto(0, 150)
        writer.write("自由贪吃蛇", align="center", font=("Arial", 42, "bold"))

        # 示例玩家蛇（绿色）
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

        # 示例敌人蛇（红色）
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

        # 示例食物（彩色）
        food_x = 0
        food_y = 0
        for i, col in enumerate(FOOD_COLORS[:5]):
            pen.goto(food_x + i*30 - 60, food_y)
            pen.color(col)
            pen.begin_fill()
            pen.circle(FOOD_RADIUS)
            pen.end_fill()

        # 操作说明
        writer.goto(0, -50)
        writer.write("鼠标移动控制方向", align="center", font=("Arial", 18, "normal"))

        # 闪烁的“开始游戏”提示
        if int(time.time() * 2) % 2 == 0:
            writer.goto(0, -100)
            writer.write("按 SPACE 开始游戏", align="center", font=("Arial", 22, "bold"))

        writer.goto(0, -150)
        writer.write("按 R 重新开始", align="center", font=("Arial", 18, "normal"))
        writer.goto(0, -200)
        writer.write("敌人2秒后出现，最多10个", align="center", font=("Arial", 14, "italic"))

        writer.color("white")  # 恢复为白色（用于游戏画面）

    else:
        # ----- 游戏画面（白色背景）-----
        # 绘制白色背景
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

        # 绘制所有游戏元素
        # 玩家蛇
        for i, (x, y) in enumerate(snake):
            color = "lightgreen" if i == 0 else "green"
            draw_circle(x, y, color, current_radius)
        # 敌人蛇
        for enemy in enemies:
            for i, (x, y) in enumerate(enemy['body']):
                color = "red" if i == 0 else "darkred"
                draw_circle(x, y, color, current_radius)
        # 食物
        for fx, fy, fcolor, fr in foods:
            draw_circle(fx, fy, fcolor, fr)

        # 绘制敌人生成预警圆圈（黑色）
        if pending_enemy_spawns:
            for (x, y) in pending_enemy_spawns:
                pen.penup()
                pen.goto(x, y - current_radius * 2)
                pen.pendown()
                pen.color("black")
                pen.pensize(2)
                pen.circle(current_radius * 2)
                pen.penup()
            pen.pensize(1)

        # 绘制红色边界框
        pen.penup()
        pen.goto(-WIDTH//2 + current_radius, -HEIGHT//2 + current_radius)
        pen.pendown()
        pen.color("red")
        pen.pensize(2)
        pen.setheading(0)
        for _ in range(2):
            pen.forward(WIDTH - 2 * current_radius)
            pen.left(90)
            pen.forward(HEIGHT - 2 * current_radius)
            pen.left(90)
        pen.penup()
        pen.pensize(1)

        # 显示各类信息（黑色文字）
        writer.color("black")
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

        if not game_active:
            writer.goto(0, 0)
            writer.write("GAME OVER\n按 R 重新开始", align="center", font=("Arial", 20, "bold"))

        writer.color("white")  # 恢复为白色（以备后用）

    screen.update()

# ========== 核心游戏循环 ==========
def move():
    """每帧更新游戏状态（移动蛇、检测碰撞、吃食物等）"""
    global snake, foods, score, game_active, direction, boosting, enemies

    if not game_started:
        draw()
        screen.ontimer(move, UPDATE_DELAY)
        return

    if not game_active:
        draw()
        screen.ontimer(move, UPDATE_DELAY)
        return

    # 加速计时检查
    if boosting and (time.time() - boost_start_time) >= BOOST_DURATION:
        boosting = False

    # 更新玩家方向（鼠标控制）
    new_dir = get_mouse_direction()
    direction = new_dir

    current_speed = get_current_speed()
    current_radius = get_segment_radius()
    # 预计算平方距离阈值（提升性能）
    eat_threshold_sq = (current_radius + FOOD_RADIUS) ** 2
    large_eat_threshold_sq = (current_radius + LARGE_FOOD_RADIUS) ** 2
    collision_threshold_sq = (current_radius * 2) ** 2

    # 保存旧头位置，用于中点采样
    old_player_head = snake[0]
    new_player_head = (old_player_head[0] + direction[0] * current_speed,
                       old_player_head[1] + direction[1] * current_speed)

    # 计算所有敌人的新头位置
    new_enemy_heads = []
    for enemy in enemies:
        old_head = enemy['body'][0]
        new_dir = get_enemy_new_direction(enemy, foods)
        enemy['dir'] = new_dir
        new_head = (old_head[0] + new_dir[0] * current_speed,
                    old_head[1] + new_dir[1] * current_speed)
        new_enemy_heads.append((enemy, old_head, new_head))

    # 玩家边界检测
    if check_boundary(new_player_head):
        game_active = False
        draw()
        screen.ontimer(move, UPDATE_DELAY)
        return

    # 处理敌人撞墙死亡
    surviving_enemy_heads = []
    for enemy, old_head, new_head in new_enemy_heads:
        if check_boundary(new_head):
            # 敌人撞墙死亡，掉落红色大食物
            spawn_foods_from_enemy(enemy['body'])
            enemies.remove(enemy)
        else:
            surviving_enemy_heads.append((enemy, old_head, new_head))

    # 玩家吃食物检测（包含中点采样，防止快速移动跳过食物）
    ate_index = None
    for i, (fx, fy, _, fr) in enumerate(foods):
        if fr == FOOD_RADIUS:
            threshold_sq = eat_threshold_sq
        else:
            threshold_sq = large_eat_threshold_sq
        # 检查新头
        if dist_sq(new_player_head[0], new_player_head[1], fx, fy) < threshold_sq:
            ate_index = i
            break
        # 检查从旧头到新头的中点
        mid_x = (old_player_head[0] + new_player_head[0]) / 2
        mid_y = (old_player_head[1] + new_player_head[1]) / 2
        if dist_sq(mid_x, mid_y, fx, fy) < threshold_sq:
            ate_index = i
            break

    # 敌人吃食物检测
    enemy_ate_info = []  # 列表元素为 (enemy, 食物索引)
    for enemy, old_head, new_head in surviving_enemy_heads:
        for i, (fx, fy, _, fr) in enumerate(foods):
            if fr == FOOD_RADIUS:
                threshold_sq = eat_threshold_sq
            else:
                threshold_sq = large_eat_threshold_sq
            # 检查新头
            if dist_sq(new_head[0], new_head[1], fx, fy) < threshold_sq:
                enemy_ate_info.append((enemy, i))
                break
            # 检查中点
            mid_x = (old_head[0] + new_head[0]) / 2
            mid_y = (old_head[1] + new_head[1]) / 2
            if dist_sq(mid_x, mid_y, fx, fy) < threshold_sq:
                enemy_ate_info.append((enemy, i))
                break

    # 收集所有被吃的食物索引（去重）
    foods_to_remove = set()
    if ate_index is not None:
        foods_to_remove.add(ate_index)
    for enemy, i in enemy_ate_info:
        foods_to_remove.add(i)

    # 更新玩家蛇身体
    snake.insert(0, new_player_head)
    if ate_index is None:
        snake.pop()  # 没吃到食物，尾部弹出

    # 更新敌人蛇身体
    for enemy, old_head, new_head in surviving_enemy_heads:
        enemy['body'].insert(0, new_head)
        ate = any(enemy == e for e, _ in enemy_ate_info)
        if not ate:
            enemy['body'].pop()

    # 删除被吃的食物
    for i in sorted(foods_to_remove, reverse=True):
        del foods[i]

    # 补充普通食物至总数
    while len(foods) < FOOD_COUNT:
        new_color = random.choice(FOOD_COLORS)
        new_food = create_food(new_color, FOOD_RADIUS)
        if new_food:
            foods.append(new_food)
        else:
            pos = random_position()
            foods.append((pos[0], pos[1], new_color, FOOD_RADIUS))

    # 玩家头与敌人身体碰撞检测（无自身碰撞）
    player_head = snake[0]
    for enemy in enemies:
        for segment in enemy['body'][1:]:  # 跳过敌人头部
            if dist_sq(player_head[0], player_head[1], segment[0], segment[1]) < collision_threshold_sq:
                game_active = False
                draw()
                screen.ontimer(move, UPDATE_DELAY)
                return

    # 敌人头碰撞检测（碰玩家身体或其他敌人身体）
    enemies_to_remove = []
    for enemy in enemies:
        enemy_head = enemy['body'][0]
        # 碰玩家身体
        for segment in snake[1:]:
            if dist_sq(enemy_head[0], enemy_head[1], segment[0], segment[1]) < collision_threshold_sq:
                enemies_to_remove.append(enemy)
                break
        if enemy in enemies_to_remove:
            continue
        # 碰其他敌人身体
        for other in enemies:
            if other is enemy:
                continue
            for segment in other['body'][1:]:
                if dist_sq(enemy_head[0], enemy_head[1], segment[0], segment[1]) < collision_threshold_sq:
                    enemies_to_remove.append(enemy)
                    break
            if enemy in enemies_to_remove:
                break

    # 处理敌人碰撞死亡
    for e in enemies_to_remove:
        if e in enemies:
            spawn_foods_from_enemy(e['body'])  # 掉落食物
            enemies.remove(e)

    draw()
    screen.ontimer(move, UPDATE_DELAY)

# ========== 游戏控制函数 ==========
def new_game():
    """重置所有游戏变量到初始状态"""
    global snake, direction, foods, score, game_active, boosting, color_centers, enemies, pending_enemy_spawns, spawn_timer_active
    snake = [(0, 0), (-16, 0), (-32, 0), (-48, 0), (-64, 0)]
    direction = (1, 0)
    score = 0
    game_active = True
    boosting = False
    color_centers.clear()
    enemies = []
    pending_enemy_spawns.clear()
    spawn_timer_active = False
    generate_foods(FOOD_COUNT)

    # 生成初始敌人生成点（预警圆圈）
    min_dist_sq = (get_segment_radius() * 4) ** 2
    for i in range(ENEMY_COUNT):
        for _ in range(100):
            x = random.randint(-WIDTH//2 + 100, WIDTH//2 - 100)
            y = random.randint(-HEIGHT//2 + 100, HEIGHT//2 - 100)
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
            # 如果找不到合适位置，随机选一个（兜底）
            x = random.randint(-WIDTH//2 + 100, WIDTH//2 - 100)
            y = random.randint(-HEIGHT//2 + 100, HEIGHT//2 - 100)
            pending_enemy_spawns.append((x, y))

    # 设置定时器生成第一批敌人
    if not spawn_timer_active:
        spawn_timer_active = True
        screen.ontimer(spawn_enemies, ENEMY_SPAWN_DELAY)

def restart():
    """按 R 键：返回开始界面"""
    global game_started
    new_game()
    game_started = False
    draw()

def start_game():
    """按空格键：开始游戏"""
    global game_started
    if not game_started:
        new_game()
        game_started = True
        draw()
        # 启动周期性敌人生成
        screen.ontimer(periodic_enemy_spawn, ENEMY_SPAWN_INTERVAL * 1000)

# ========== 加速控制 ==========
def boost_start():
    """Ctrl键按下：开启加速"""
    global boosting, boost_start_time
    if game_started and game_active:
        boosting = True
        boost_start_time = time.time()

def boost_end():
    """Ctrl键释放：关闭加速"""
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
new_game()          # 初始化所有变量
game_started = False # 确保显示开始界面
draw()
screen.ontimer(move, UPDATE_DELAY)  # 启动游戏循环
turtle.done()       # 进入主事件循环