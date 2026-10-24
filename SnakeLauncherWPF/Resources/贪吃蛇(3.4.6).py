import pygame
import random
import math
import os
import time
import json

# ========== 游戏版本 ==========
VERSION = "v3.4.6"
VERSION_FILE = os.path.join(os.path.expanduser("~"), ".snake_version_pygame")

# 所有版本更新日志（从最新到最老）
ALL_CHANGELOGS = [
    ("v3.4.6", [
        "设置界面增加“开发者名单”选项，点击可查看制作人员",
    ]),
    ("v3.4.5", [
        "修复玩家加速时敌人也加速的bug",
        "优化设置界面返回按钮：移除方框，仅保留文字",
    ]),
    ("v3.4.4", [
        "设置界面左上角添加返回按钮，点击返回开始界面",
    ]),
    ("v3.4.3", [
        "更新历史顺序改为最新到最老",
        "设置界面鼠标点击可直接更改选项值",
    ]),
    ("v3.4.2", [
        "初始速度改为4.5，最低速度0.5",
        "设置界面支持鼠标悬停和点击（点击第四项直接打开更新日志）",
    ]),
    ("v3.4.1", [
        "优化暂停菜单：鼠标悬停高亮，点击选择，键盘同时支持",
    ]),
    ("v3.4.0", [
        "游戏内ESC打开暂停菜单（重新开始/返回开始界面/退出游戏）",
    ]),
    ("v3.3.0", [
        "增加白色/浅灰交错方格背景",
        "设置中增加“更新日志”选项，可查看所有版本更新",
    ]),
    ("v3.2.1", [
        "更新日志只在版本更新后首次启动显示",
    ]),
    ("v3.2.0", [
        "更新日志改为单独窗口显示",
    ]),
    ("v3.1.0", [
        "重做更新提示，游戏内直接显示",
        "修复开始界面按钮顺序错误",
        "修复中文无法显示的问题",
        "修复设置界面标题位置",
        "死亡提示加大加粗，颜色自适应",
        "优化性能，减少画面闪烁",
    ]),
    ("v3.0.0", [
        "Pygame重写，流畅渲染",
        "支持鼠标/键盘控制",
        "敌人AI主动觅食",
        "敌人持续生成（最多10个）",
        "敌人死亡掉落红色大食物",
        "速度随分数递减",
        "Ctrl加速（5秒限时）",
        "蛇身随分数变粗",
        "敌人生成预警圆圈",
    ]),
]

# 当前版本更新日志（用于首次启动提示）
CURRENT_CHANGELOG = [
    f"版本 {VERSION} 更新内容：",
] + [item for sublist in [log for _, log in ALL_CHANGELOGS if _ == VERSION] for item in sublist]

def check_version():
    """检查版本是否更新，返回(是否需要显示更新日志, 上次版本号)"""
    last_version = ""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            last_version = f.read().strip()
    return last_version != VERSION, last_version

def write_version():
    with open(VERSION_FILE, "w") as f:
        f.write(VERSION)

# ========== 初始化 Pygame ==========
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = 1600, 900  # 窗口大小
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"自由贪吃蛇 (PVE) {VERSION}")
clock = pygame.time.Clock()
FPS = 60  # 目标帧率

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
DARK_RED = (128, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 128, 0)
LIGHT_GREEN = (144, 238, 144)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
BROWN = (165, 42, 42)
LIGHT_GRAY_BG = (240, 240, 240)  # 浅灰背景格子

# 开始界面背景色（海沫绿）
START_BG = (192, 255, 240)  # 近似 #C0F0E0

# 游戏配置
WORLD_WIDTH, WORLD_HEIGHT = 5000, 4000
WORLD_MIN_X = -WORLD_WIDTH // 2
WORLD_MAX_X = WORLD_WIDTH // 2
WORLD_MIN_Y = -WORLD_HEIGHT // 2
WORLD_MAX_Y = WORLD_HEIGHT // 2

BASE_SPEED = 4.5
MIN_SPEED = 0.5
SPEED_DECAY = 0.016
BASE_SEGMENT_RADIUS = 8
FOOD_RADIUS = 6
LARGE_FOOD_RADIUS = 10
FOOD_COUNT = 125
BOOST_DURATION = 5.0
BOOST_MULTIPLIER = 2.0
ENEMY_COUNT = 3
MAX_ENEMIES = 10
ENEMY_SPAWN_DELAY = 2000  # 毫秒
ENEMY_SPAWN_INTERVAL = 5  # 秒
FOOD_PER_SEGMENT = 3
ENEMY_FOOD_SEEK_PROB = 0.8
GRID_SIZE = 40  # 格子间距

MAX_SEGMENT_RADIUS = 20
RADIUS_PER_SCORE = 0.02

FOOD_COLORS = [RED, ORANGE, YELLOW, PINK, PURPLE, CYAN, (0, 255, 0)]  # lime

# 蛇颜色选项（中文映射，实际存储颜色值）
HEAD_COLOR_OPTIONS = [LIGHT_GREEN, YELLOW, ORANGE, PINK, CYAN, WHITE]
HEAD_COLOR_NAMES = ["浅绿", "黄", "橙", "粉", "青", "白"]
BODY_COLOR_OPTIONS = [GREEN, DARK_GREEN, BLUE, PURPLE, BROWN, GRAY]
BODY_COLOR_NAMES = ["绿", "深绿", "蓝", "紫", "棕", "灰"]

DEFAULT_HEAD_COLOR = LIGHT_GREEN
DEFAULT_BODY_COLOR = GREEN

# 背景样式选项
BACKGROUND_STYLE_OPTIONS = ["纯黑", "纯白", "格子"]
BACKGROUND_STYLE_VALUES = [BLACK, WHITE, "grid"]
DEFAULT_BACKGROUND_STYLE = 2  # 格子

# 按钮尺寸
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 44
BUTTON_HALF_WIDTH = BUTTON_WIDTH // 2
BUTTON_HALF_HEIGHT = BUTTON_HEIGHT // 2
BUTTON_Y_POS = [45, -5, -55]

# 暂停菜单选项
PAUSE_OPTIONS = ["重新开始", "返回开始界面", "退出游戏"]

# 返回按钮文字位置
BACK_BUTTON_POS = (30, 30)

# ========== 字体加载函数（支持中文） ==========
def get_font(size):
    font_names = [
        "Microsoft YaHei",
        "SimHei",
        "SimSun",
        "KaiTi",
        "FangSong",
    ]
    for name in font_names:
        try:
            font = pygame.font.SysFont(name, size)
            test_surf = font.render("测试", True, (255,255,255))
            if test_surf.get_width() > 0:
                return font
        except:
            continue

    local_font_path = os.path.join(os.path.dirname(__file__), "simhei.ttf")
    if os.path.exists(local_font_path):
        try:
            return pygame.font.Font(local_font_path, size)
        except:
            pass

    print("警告：未找到中文字体，中文可能无法正常显示。请安装中文字体或将 simhei.ttf 放在游戏目录下。")
    return pygame.font.Font(None, size)

# ========== 摄像机 ==========
cam_x, cam_y = 0, 0

def update_camera(head_x, head_y):
    global cam_x, cam_y
    cam_x = head_x
    cam_y = head_y
    min_cam_x = WORLD_MIN_X + WIDTH // 2
    max_cam_x = WORLD_MAX_X - WIDTH // 2
    min_cam_y = WORLD_MIN_Y + HEIGHT // 2
    max_cam_y = WORLD_MAX_Y - HEIGHT // 2
    if min_cam_x < max_cam_x:
        cam_x = max(min_cam_x, min(cam_x, max_cam_x))
    if min_cam_y < max_cam_y:
        cam_y = max(min_cam_y, min(cam_y, max_cam_y))
    if min_cam_x >= max_cam_x:
        cam_x = (WORLD_MIN_X + WORLD_MAX_X) // 2
    if min_cam_y >= max_cam_y:
        cam_y = (WORLD_MIN_Y + WORLD_MAX_Y) // 2

def world_to_screen(wx, wy):
    sx = wx - cam_x + WIDTH // 2
    sy = wy - cam_y + HEIGHT // 2
    return int(sx), int(sy)

def screen_to_world(sx, sy):
    wx = sx - WIDTH // 2 + cam_x
    wy = sy - HEIGHT // 2 + cam_y
    return wx, wy

# ========== 游戏变量 ==========
snake = [(0, 0), (-16, 0), (-32, 0), (-48, 0), (-64, 0)]
direction = (1, 0)

enemies = []
foods = []
score = 0
game_active = True
game_started = False
settings_mode = False
paused = False
pause_selection = 0
boosting = False
boost_start_time = 0

color_centers = {}

mouse_x, mouse_y = 0, 0
mouse_pressed = False

pending_enemy_spawns = []
spawn_timer_active = False
last_spawn_check = 0

background_style = DEFAULT_BACKGROUND_STYLE
head_color_index = 0
body_color_index = 0
selected_setting = 0

hover_button = None
setting_option_rects = []
back_button_hover = False  # 返回按钮悬停状态

# 开发者名单内容
CREDITS = [
    "开发者名单",
    "",
    "策划 & 开发：没冇啊",
    "代码：deep seek，没冇啊",
    "美术设计：deep seek，没冇啊",
    "QA：没冇啊",
    "",
    "特别感谢：所有支持本游戏的玩家",
    "",
    "Pygame 社区",
    "Python 编程语言",
]

def random_position(margin=50):
    x = random.randint(WORLD_MIN_X + margin, WORLD_MAX_X - margin)
    y = random.randint(WORLD_MIN_Y + margin, WORLD_MAX_Y - margin)
    return x, y

def create_food(color, radius=FOOD_RADIUS):
    seg_radius = get_segment_radius()
    if color in color_centers and random.random() < 0.8:
        center_x, center_y = color_centers[color]
    else:
        center_x, center_y = random_position(margin=80+50)
    for _ in range(50):
        offset_x = random.randint(-80, 80)
        offset_y = random.randint(-80, 80)
        fx = center_x + offset_x
        fy = center_y + offset_y
        if fx < WORLD_MIN_X + radius or fx > WORLD_MAX_X - radius or fy < WORLD_MIN_Y + radius or fy > WORLD_MAX_Y - radius:
            continue
        overlap = False
        for sx, sy in snake:
            if (fx - sx) ** 2 + (fy - sy) ** 2 < (seg_radius + radius) ** 2:
                overlap = True
                break
        if not overlap:
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if (fx - sx) ** 2 + (fy - sy) ** 2 < (seg_radius + radius) ** 2:
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

def get_segment_radius():
    return min(MAX_SEGMENT_RADIUS, BASE_SEGMENT_RADIUS + score * RADIUS_PER_SCORE)

def get_current_speed():
    base = max(MIN_SPEED, BASE_SPEED - score * SPEED_DECAY)
    if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
        return base * BOOST_MULTIPLIER
    else:
        return base

def get_base_speed():
    return max(MIN_SPEED, BASE_SPEED - score * SPEED_DECAY)

def spawn_foods_from_enemy(enemy_body):
    global foods
    seg_radius = get_segment_radius()
    threshold_sq = (seg_radius + LARGE_FOOD_RADIUS) ** 2
    for segment in enemy_body:
        for _ in range(FOOD_PER_SEGMENT):
            for _ in range(30):
                offset_x = random.randint(-30, 30)
                offset_y = random.randint(-30, 30)
                fx = segment[0] + offset_x
                fy = segment[1] + offset_y
                if fx < WORLD_MIN_X + LARGE_FOOD_RADIUS or fx > WORLD_MAX_X - LARGE_FOOD_RADIUS or \
                   fy < WORLD_MIN_Y + LARGE_FOOD_RADIUS or fy > WORLD_MAX_Y - LARGE_FOOD_RADIUS:
                    continue
                overlap = False
                for sx, sy in snake:
                    if (fx - sx) ** 2 + (fy - sy) ** 2 < threshold_sq:
                        overlap = True
                        break
                if overlap:
                    continue
                for enemy in enemies:
                    for sx, sy in enemy['body']:
                        if (fx - sx) ** 2 + (fy - sy) ** 2 < threshold_sq:
                            overlap = True
                            break
                    if overlap:
                        break
                if overlap:
                    continue
                foods.append((fx, fy, RED, LARGE_FOOD_RADIUS))
                break
            else:
                pos = random_position()
                foods.append((pos[0], pos[1], RED, LARGE_FOOD_RADIUS))

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

def periodic_enemy_spawn(current_time):
    global spawn_timer_active, pending_enemy_spawns, last_spawn_check
    if not game_started or not game_active:
        return
    if current_time - last_spawn_check < ENEMY_SPAWN_INTERVAL * 1000:
        return
    last_spawn_check = current_time
    if len(enemies) < MAX_ENEMIES:
        min_dist_sq = (get_segment_radius() * 4) ** 2
        for _ in range(100):
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            overlap = False
            for sx, sy in snake:
                if (x - sx) ** 2 + (y - sy) ** 2 < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if (x - sx) ** 2 + (y - sy) ** 2 < min_dist_sq:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            for ex, ey in pending_enemy_spawns:
                if (x - ex) ** 2 + (y - ey) ** 2 < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            pending_enemy_spawns.append((x, y))
            if not spawn_timer_active:
                spawn_timer_active = True
                pygame.time.set_timer(pygame.USEREVENT + 1, ENEMY_SPAWN_DELAY)
            break

def get_enemy_new_direction(enemy, foods_list):
    old_dir = enemy['dir']
    head = enemy['body'][0]
    if foods_list and random.random() < ENEMY_FOOD_SEEK_PROB:
        min_dist_sq = float('inf')
        target = None
        for fx, fy, _, _ in foods_list:
            d_sq = (head[0] - fx) ** 2 + (head[1] - fy) ** 2
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

def check_boundary(head):
    x, y = head
    margin = get_segment_radius()
    return (x < WORLD_MIN_X + margin or x > WORLD_MAX_X - margin or
            y < WORLD_MIN_Y + margin or y > WORLD_MAX_Y - margin)

def draw_circle(surface, x, y, color, radius):
    sx, sy = world_to_screen(x, y)
    pygame.draw.circle(surface, color, (sx, sy), radius)

def restart_game():
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

    min_dist_sq = (get_segment_radius() * 4) ** 2
    for i in range(ENEMY_COUNT):
        for _ in range(100):
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            overlap = False
            for sx, sy in snake:
                if (x - sx) ** 2 + (y - sy) ** 2 < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            for ex, ey in pending_enemy_spawns:
                if (x - ex) ** 2 + (y - ey) ** 2 < min_dist_sq:
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
        pygame.time.set_timer(pygame.USEREVENT + 1, ENEMY_SPAWN_DELAY)

def show_full_changelog():
    log_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    log_surface.fill((192, 255, 240, 220))

    font_title = get_font(48)
    font_version = get_font(30)
    font_content = get_font(20)
    font_button = get_font(24)

    title = font_title.render("更新历史", True, BLACK)
    back_button_text = "返回 (ESC)"

    button_rect = pygame.Rect(WIDTH//2 - BUTTON_HALF_WIDTH, HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)

    content_lines = []
    for ver, lines in ALL_CHANGELOGS:
        content_lines.append(("version", ver))
        for line in lines:
            content_lines.append(("content", line))
        content_lines.append(("spacer", ""))

    total_lines = len(content_lines)
    max_visible_lines = 20
    scroll_offset = 0

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    waiting = False
                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - 1)
                elif event.key == pygame.K_DOWN:
                    scroll_offset = min(total_lines - max_visible_lines, scroll_offset + 1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if button_rect.collidepoint(event.pos):
                        waiting = False
                elif event.button == 4:
                    scroll_offset = max(0, scroll_offset - 3)
                elif event.button == 5:
                    scroll_offset = min(total_lines - max_visible_lines, scroll_offset + 3)

        screen.fill(BLACK)
        screen.blit(log_surface, (0, 0))

        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        y = 150
        start_idx = scroll_offset
        end_idx = min(start_idx + max_visible_lines, total_lines)
        for i in range(start_idx, end_idx):
            line_type, text = content_lines[i]
            if line_type == "version":
                rendered = font_version.render(text, True, BLACK)
                screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, y))
                y += 30
            elif line_type == "content":
                rendered = font_content.render("  • " + text, True, BLACK)
                screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, y))
                y += 25
            else:
                y += 10

        if total_lines > max_visible_lines:
            scroll_hint = font_content.render(f"第 {scroll_offset+1}-{end_idx} 行 / 共 {total_lines} 行 (上下箭头/滚轮滚动)", True, DARK_GRAY)
            screen.blit(scroll_hint, (WIDTH//2 - scroll_hint.get_width()//2, HEIGHT - 150))

        pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
        pygame.draw.rect(screen, GRAY, button_rect, 2)
        btn_text = font_button.render(back_button_text, True, BLACK)
        screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))

        pygame.display.flip()
        clock.tick(FPS)

def show_credits():
    """显示开发者名单窗口"""
    credit_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    credit_surface.fill((192, 255, 240, 220))  # 海沫绿半透明

    font_title = get_font(48)
    font_credit = get_font(24)
    font_button = get_font(24)

    title = font_title.render("开发者名单", True, BLACK)
    back_button_text = "返回 (ESC)"

    button_rect = pygame.Rect(WIDTH//2 - BUTTON_HALF_WIDTH, HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if button_rect.collidepoint(event.pos):
                        waiting = False

        screen.fill(BLACK)
        screen.blit(credit_surface, (0, 0))

        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        y = 250
        for line in CREDITS:
            if line == "":
                y += 10
                continue
            rendered = font_credit.render(line, True, BLACK)
            screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, y))
            y += 40

        pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
        pygame.draw.rect(screen, GRAY, button_rect, 2)
        btn_text = font_button.render(back_button_text, True, BLACK)
        screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))

        pygame.display.flip()
        clock.tick(FPS)

def show_changelog():
    log_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    log_surface.fill((192, 255, 240, 200))

    font_title = get_font(48)
    font_content = get_font(20)
    font_button = get_font(24)

    title = font_title.render("版本更新", True, BLACK)
    button_text = "开始游戏"

    button_rect = pygame.Rect(WIDTH//2 - BUTTON_HALF_WIDTH, HEIGHT//2 + 150, BUTTON_WIDTH, BUTTON_HEIGHT)

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if button_rect.collidepoint(event.pos):
                        waiting = False

        screen.fill(BLACK)
        screen.blit(log_surface, (0, 0))

        screen.blit(title, (WIDTH//2 - title.get_width()//2, 200))

        y = 300
        for line in CURRENT_CHANGELOG:
            rendered = font_content.render(line, True, BLACK)
            screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, y))
            y += 30

        pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
        pygame.draw.rect(screen, GRAY, button_rect, 2)
        btn_text = font_button.render(button_text, True, BLACK)
        screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))

        pygame.display.flip()
        clock.tick(FPS)

def draw():
    global setting_option_rects, back_button_hover
    screen.fill(BLACK)

    if settings_mode:
        screen.fill(START_BG)

        # 绘制返回按钮（无方框，仅文字）
        back_font = get_font(24)
        back_text_color = DARK_GRAY if back_button_hover else BLACK
        back_text = back_font.render("返回", True, back_text_color)
        text_rect = back_text.get_rect()
        text_rect.center = (BACK_BUTTON_POS[0] + 50, BACK_BUTTON_POS[1] + 20)
        screen.blit(back_text, text_rect)

        font_big = get_font(36)
        font_small = get_font(16)
        title = font_big.render("设置", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        # 五个选项：背景样式、蛇头颜色、蛇身颜色、查看更新日志、开发者名单
        items = [
            f"背景样式: {BACKGROUND_STYLE_OPTIONS[background_style]}",
            f"蛇头颜色: {HEAD_COLOR_NAMES[head_color_index]}",
            f"蛇身颜色: {BODY_COLOR_NAMES[body_color_index]}",
            "查看更新日志",
            "开发者名单"
        ]
        y = 250
        setting_option_rects = []
        for i, text in enumerate(items):
            display_text = text
            if i == selected_setting:
                display_text = ">> " + text + " <<"
            font = get_font(24)
            rendered = font.render(display_text, True, BLACK)
            rect = pygame.Rect(WIDTH//2 - rendered.get_width()//2 - 10, y - 10,
                               rendered.get_width() + 20, rendered.get_height() + 20)
            setting_option_rects.append(rect)
            screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, y))
            y += 60

        hint = font_small.render("↑↓选择  ←→更改  Enter保存  Esc取消  (鼠标点击切换前三个选项)", True, BLACK)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 100))

    elif not game_started:
        screen.fill(START_BG)
        font_title = get_font(48)
        font_small = get_font(18)

        title = font_title.render(f"自由贪吃蛇 {VERSION}", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        button_texts = ["开始游戏 (SPACE)", "设置 (S)", "退出 (Q)"]
        button_fonts = [get_font(24), get_font(18), get_font(18)]

        for i, (y, text) in enumerate(zip(BUTTON_Y_POS, button_texts)):
            screen_y = HEIGHT//2 + y
            if hover_button == i:
                rect = pygame.Rect(WIDTH//2 - BUTTON_HALF_WIDTH, screen_y - BUTTON_HALF_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT)
                pygame.draw.rect(screen, LIGHT_GRAY, rect)
                pygame.draw.rect(screen, GRAY, rect, 2)
                text_color = BLACK
            else:
                text_color = BLACK
            rendered = button_fonts[i].render(text, True, text_color)
            screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, screen_y - rendered.get_height()//2 - 2))

    else:
        bg_value = BACKGROUND_STYLE_VALUES[background_style]

        if bg_value == "grid":
            screen.fill(WHITE)
        else:
            screen.fill(bg_value)

        if bg_value == "grid":
            left_world = cam_x - WIDTH//2
            right_world = cam_x + WIDTH//2
            bottom_world = cam_y - HEIGHT//2
            top_world = cam_y + HEIGHT//2

            start_x = math.floor(left_world / GRID_SIZE) * GRID_SIZE
            end_x = math.ceil(right_world / GRID_SIZE) * GRID_SIZE
            start_y = math.floor(bottom_world / GRID_SIZE) * GRID_SIZE
            end_y = math.ceil(top_world / GRID_SIZE) * GRID_SIZE

            x = start_x
            while x < end_x:
                y = start_y
                while y < end_y:
                    if ((x // GRID_SIZE) + (y // GRID_SIZE)) % 2 == 0:
                        color = WHITE
                    else:
                        color = LIGHT_GRAY_BG
                    sx, sy = world_to_screen(x, y)
                    pygame.draw.rect(screen, color, (sx, sy, GRID_SIZE, GRID_SIZE))
                    y += GRID_SIZE
                x += GRID_SIZE

        head_color = HEAD_COLOR_OPTIONS[head_color_index]
        body_color = BODY_COLOR_OPTIONS[body_color_index]
        current_radius = get_segment_radius()
        for i, (x, y) in enumerate(snake):
            color = head_color if i == 0 else body_color
            draw_circle(screen, x, y, color, current_radius)
        for enemy in enemies:
            for i, (x, y) in enumerate(enemy['body']):
                color = RED if i == 0 else DARK_RED
                draw_circle(screen, x, y, color, current_radius)
        for fx, fy, fcolor, fr in foods:
            draw_circle(screen, fx, fy, fcolor, fr)

        if pending_enemy_spawns:
            for (x, y) in pending_enemy_spawns:
                sx, sy = world_to_screen(x, y)
                pygame.draw.circle(screen, WHITE, (sx, sy), current_radius * 2, 2)

        left, bottom = world_to_screen(WORLD_MIN_X + current_radius, WORLD_MIN_Y + current_radius)
        right, top = world_to_screen(WORLD_MAX_X - current_radius, WORLD_MAX_Y - current_radius)
        pygame.draw.rect(screen, RED, (left, bottom, right - left, top - bottom), 2)

        font_info = get_font(16)
        font_small = get_font(12)
        score_text = font_info.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 200, 30))

        speed_val = get_current_speed()
        speed_text = f"Speed: {speed_val:.1f}"
        if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
            remaining = BOOST_DURATION - (time.time() - boost_start_time)
            speed_text += f" (Boost: {remaining:.1f}s)"
        speed_rend = font_small.render(speed_text, True, WHITE)
        screen.blit(speed_rend, (20, 30))

        boost_hint = font_small.render("长按Ctrl加速(5s限时)", True, WHITE)
        screen.blit(boost_hint, (20, 50))

        enemy_count = font_small.render(f"敌人: {len(enemies)}/{MAX_ENEMIES}", True, WHITE)
        screen.blit(enemy_count, (20, 70))

        if not game_active:
            if bg_value == BLACK:
                game_over_color = WHITE
            else:
                game_over_color = BLACK
            font_gameover = get_font(32)
            font_gameover.set_bold(True)
            game_over = font_gameover.render("GAME OVER  按 R 重新开始", True, game_over_color)
            screen.blit(game_over, (WIDTH//2 - game_over.get_width()//2, HEIGHT//2))

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))

            pause_font = get_font(48)
            pause_title = pause_font.render("暂停", True, WHITE)
            screen.blit(pause_title, (WIDTH//2 - pause_title.get_width()//2, 200))

            option_font = get_font(36)
            option_y_start = 350
            for i, opt in enumerate(PAUSE_OPTIONS):
                if i == pause_selection:
                    text = "▶ " + opt + " ◀"
                    color = YELLOW
                else:
                    text = opt
                    color = WHITE
                rendered = option_font.render(text, True, color)
                screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, option_y_start + i * 60))

            hint = font_small.render("↑↓选择  Enter确认  鼠标点击选择", True, LIGHT_GRAY)
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 150))

        ver_text = font_small.render(VERSION, True, WHITE)
        screen.blit(ver_text, (WIDTH - 150, HEIGHT - 30))

    pygame.display.flip()

def new_game():
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

    min_dist_sq = (get_segment_radius() * 4) ** 2
    for i in range(ENEMY_COUNT):
        for _ in range(100):
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            overlap = False
            for sx, sy in snake:
                if (x - sx) ** 2 + (y - sy) ** 2 < min_dist_sq:
                    overlap = True
                    break
            if overlap:
                continue
            for ex, ey in pending_enemy_spawns:
                if (x - ex) ** 2 + (y - ey) ** 2 < min_dist_sq:
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
        pygame.time.set_timer(pygame.USEREVENT + 1, ENEMY_SPAWN_DELAY)

def restart():
    global game_started, settings_mode
    new_game()
    game_started = False
    settings_mode = False

def start_game():
    global game_started, settings_mode
    if not game_started and not settings_mode:
        new_game()
        game_started = True

def settings_up():
    global selected_setting
    if not settings_mode:
        return
    selected_setting = (selected_setting - 1) % 5  # 改为5个选项

def settings_down():
    global selected_setting
    if not settings_mode:
        return
    selected_setting = (selected_setting + 1) % 5

def settings_left():
    global background_style, head_color_index, body_color_index
    if not settings_mode:
        return
    if selected_setting == 0:
        background_style = (background_style - 1) % len(BACKGROUND_STYLE_OPTIONS)
    elif selected_setting == 1:
        head_color_index = (head_color_index - 1) % len(HEAD_COLOR_OPTIONS)
    elif selected_setting == 2:
        body_color_index = (body_color_index - 1) % len(BODY_COLOR_OPTIONS)
    # 选项3和4（更新日志、开发者名单）没有左右更改

def settings_right():
    global background_style, head_color_index, body_color_index
    if not settings_mode:
        return
    if selected_setting == 0:
        background_style = (background_style + 1) % len(BACKGROUND_STYLE_OPTIONS)
    elif selected_setting == 1:
        head_color_index = (head_color_index + 1) % len(HEAD_COLOR_OPTIONS)
    elif selected_setting == 2:
        body_color_index = (body_color_index + 1) % len(BODY_COLOR_OPTIONS)

def settings_save():
    global settings_mode
    settings_mode = False

def settings_cancel():
    global settings_mode, background_style, head_color_index, body_color_index
    background_style = DEFAULT_BACKGROUND_STYLE
    head_color_index = HEAD_COLOR_OPTIONS.index(DEFAULT_HEAD_COLOR)
    body_color_index = BODY_COLOR_OPTIONS.index(DEFAULT_BODY_COLOR)
    settings_mode = False

def enter_settings():
    global settings_mode, selected_setting
    if not game_started and not settings_mode:
        settings_mode = True
        selected_setting = 0

def quit_game():
    pygame.quit()
    exit()

# ========== 主程序入口 ==========
need_show, last_ver = check_version()
if need_show:
    show_changelog()
    write_version()

new_game()
last_time = time.time()
running = True
spawn_event = pygame.USEREVENT + 1

while running:
    dt = time.time() - last_time
    last_time = time.time()
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_started and not settings_mode:
                    if paused:
                        paused = False
                    else:
                        paused = True
                elif settings_mode:
                    settings_cancel()
            elif event.key == pygame.K_SPACE:
                if not game_started and not settings_mode:
                    start_game()
            elif event.key == pygame.K_r:
                if game_started and not settings_mode and not paused:
                    restart_game()
                elif not game_started and not settings_mode:
                    restart()
            elif event.key == pygame.K_s:
                if not game_started and not settings_mode:
                    enter_settings()
            elif event.key == pygame.K_q:
                if not game_started and not settings_mode:
                    quit_game()
            elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                if game_started and game_active and not paused:
                    boosting = True
                    boost_start_time = time.time()
            if paused:
                if event.key == pygame.K_UP:
                    pause_selection = (pause_selection - 1) % 3
                elif event.key == pygame.K_DOWN:
                    pause_selection = (pause_selection + 1) % 3
                elif event.key == pygame.K_RETURN:
                    if pause_selection == 0:
                        restart_game()
                        paused = False
                    elif pause_selection == 1:
                        game_started = False
                        settings_mode = False
                        paused = False
                    elif pause_selection == 2:
                        quit_game()
            if settings_mode:
                if event.key == pygame.K_UP:
                    settings_up()
                elif event.key == pygame.K_DOWN:
                    settings_down()
                elif event.key == pygame.K_LEFT:
                    settings_left()
                elif event.key == pygame.K_RIGHT:
                    settings_right()
                elif event.key == pygame.K_RETURN:
                    if selected_setting == 3:
                        show_full_changelog()
                    elif selected_setting == 4:
                        show_credits()
                    else:
                        settings_save()
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                boosting = False
        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            if not game_started and not settings_mode:
                hover_button = None
                for i, y_center in enumerate(BUTTON_Y_POS):
                    screen_y = HEIGHT//2 + y_center
                    if (screen_y - BUTTON_HALF_HEIGHT <= mouse_y <= screen_y + BUTTON_HALF_HEIGHT and
                        WIDTH//2 - BUTTON_HALF_WIDTH <= mouse_x <= WIDTH//2 + BUTTON_HALF_WIDTH):
                        hover_button = i
                        break
            else:
                hover_button = None

            if settings_mode:
                # 设置选项悬停
                for i, rect in enumerate(setting_option_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        if selected_setting != i:
                            selected_setting = i
                        break
                # 返回按钮悬停
                back_font = get_font(24)
                back_text = back_font.render("返回", True, BLACK)
                text_rect = back_text.get_rect()
                text_rect.center = (BACK_BUTTON_POS[0] + 50, BACK_BUTTON_POS[1] + 20)
                back_button_hover = text_rect.collidepoint(mouse_x, mouse_y)

            if paused:
                option_y_start = 350
                for i in range(3):
                    opt_text = PAUSE_OPTIONS[i]
                    font = get_font(36)
                    rendered = font.render(opt_text, True, WHITE)
                    rect = pygame.Rect(WIDTH//2 - rendered.get_width()//2 - 10, option_y_start + i * 60 - 10,
                                       rendered.get_width() + 20, rendered.get_height() + 20)
                    if rect.collidepoint(mouse_x, mouse_y):
                        pause_selection = i
                        break

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not game_started and not settings_mode:
                    for i, y_center in enumerate(BUTTON_Y_POS):
                        screen_y = HEIGHT//2 + y_center
                        if (screen_y - BUTTON_HALF_HEIGHT <= mouse_y <= screen_y + BUTTON_HALF_HEIGHT and
                            WIDTH//2 - BUTTON_HALF_WIDTH <= mouse_x <= WIDTH//2 + BUTTON_HALF_WIDTH):
                            if i == 0:
                                start_game()
                            elif i == 1:
                                enter_settings()
                            elif i == 2:
                                quit_game()
                            break
                elif settings_mode:
                    # 返回按钮点击
                    back_font = get_font(24)
                    back_text = back_font.render("返回", True, BLACK)
                    text_rect = back_text.get_rect()
                    text_rect.center = (BACK_BUTTON_POS[0] + 50, BACK_BUTTON_POS[1] + 20)
                    if text_rect.collidepoint(mouse_x, mouse_y):
                        settings_cancel()
                    else:
                        for i, rect in enumerate(setting_option_rects):
                            if rect.collidepoint(mouse_x, mouse_y):
                                if i == 3:
                                    show_full_changelog()
                                elif i == 4:
                                    show_credits()
                                else:
                                    selected_setting = i
                                    settings_right()
                                break
                elif paused:
                    option_y_start = 350
                    for i in range(3):
                        opt_text = PAUSE_OPTIONS[i]
                        font = get_font(36)
                        rendered = font.render(opt_text, True, WHITE)
                        rect = pygame.Rect(WIDTH//2 - rendered.get_width()//2 - 10, option_y_start + i * 60 - 10,
                                           rendered.get_width() + 20, rendered.get_height() + 20)
                        if rect.collidepoint(event.pos):
                            if i == 0:
                                restart_game()
                                paused = False
                            elif i == 1:
                                game_started = False
                                settings_mode = False
                                paused = False
                            elif i == 2:
                                quit_game()
                            break
        elif event.type == spawn_event:
            spawn_enemies()

    if game_started and not settings_mode and game_active and not paused:
        wx, wy = screen_to_world(mouse_x, mouse_y)
        hx, hy = snake[0]
        dx = wx - hx
        dy = wy - hy
        if abs(dx) > 1 or abs(dy) > 1:
            length = math.hypot(dx, dy)
            direction = (dx / length, dy / length)

    if game_started and not settings_mode and game_active and not paused:
        current_speed = get_current_speed()
        enemy_speed = get_base_speed()
        current_radius = get_segment_radius()
        eat_threshold_sq = (current_radius + FOOD_RADIUS) ** 2
        large_eat_threshold_sq = (current_radius + LARGE_FOOD_RADIUS) ** 2
        collision_threshold_sq = (current_radius * 2) ** 2

        old_head = snake[0]
        new_head = (old_head[0] + direction[0] * current_speed,
                    old_head[1] + direction[1] * current_speed)

        new_enemy_heads = []
        for enemy in enemies:
            old_enemy_head = enemy['body'][0]
            new_dir = get_enemy_new_direction(enemy, foods)
            enemy['dir'] = new_dir
            new_enemy_head = (old_enemy_head[0] + new_dir[0] * enemy_speed,
                              old_enemy_head[1] + new_dir[1] * enemy_speed)
            new_enemy_heads.append((enemy, old_enemy_head, new_enemy_head))

        if check_boundary(new_head):
            game_active = False
            draw()
            pygame.display.flip()
            continue

        surviving_enemy_heads = []
        for enemy, old_head, new_head_pos in new_enemy_heads:
            if check_boundary(new_head_pos):
                spawn_foods_from_enemy(enemy['body'])
                enemies.remove(enemy)
            else:
                surviving_enemy_heads.append((enemy, old_head, new_head_pos))

        ate_index = None
        for i, (fx, fy, _, fr) in enumerate(foods):
            threshold = large_eat_threshold_sq if fr == LARGE_FOOD_RADIUS else eat_threshold_sq
            if (new_head[0] - fx) ** 2 + (new_head[1] - fy) ** 2 < threshold:
                ate_index = i
                break
            mid_x = (old_head[0] + new_head[0]) / 2
            mid_y = (old_head[1] + new_head[1]) / 2
            if (mid_x - fx) ** 2 + (mid_y - fy) ** 2 < threshold:
                ate_index = i
                break

        enemy_ate_info = []
        for enemy, old_enemy_head, new_enemy_head in surviving_enemy_heads:
            for i, (fx, fy, _, fr) in enumerate(foods):
                threshold = large_eat_threshold_sq if fr == LARGE_FOOD_RADIUS else eat_threshold_sq
                if (new_enemy_head[0] - fx) ** 2 + (new_enemy_head[1] - fy) ** 2 < threshold:
                    enemy_ate_info.append((enemy, i))
                    break
                mid_x = (old_enemy_head[0] + new_enemy_head[0]) / 2
                mid_y = (old_enemy_head[1] + new_enemy_head[1]) / 2
                if (mid_x - fx) ** 2 + (mid_y - fy) ** 2 < threshold:
                    enemy_ate_info.append((enemy, i))
                    break

        foods_to_remove = set()
        if ate_index is not None:
            foods_to_remove.add(ate_index)
        for enemy, i in enemy_ate_info:
            foods_to_remove.add(i)

        snake.insert(0, new_head)
        if ate_index is None:
            snake.pop()

        for enemy, old_head_pos, new_head_pos in surviving_enemy_heads:
            enemy['body'].insert(0, new_head_pos)
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
                if (player_head[0] - segment[0]) ** 2 + (player_head[1] - segment[1]) ** 2 < collision_threshold_sq:
                    game_active = False

        enemies_to_remove = []
        for enemy in enemies:
            enemy_head = enemy['body'][0]
            for segment in snake[1:]:
                if (enemy_head[0] - segment[0]) ** 2 + (enemy_head[1] - segment[1]) ** 2 < collision_threshold_sq:
                    enemies_to_remove.append(enemy)
                    break
            if enemy in enemies_to_remove:
                continue
            for other in enemies:
                if other is enemy:
                    continue
                for segment in other['body'][1:]:
                    if (enemy_head[0] - segment[0]) ** 2 + (enemy_head[1] - segment[1]) ** 2 < collision_threshold_sq:
                        enemies_to_remove.append(enemy)
                        break
                if enemy in enemies_to_remove:
                    break
        for e in enemies_to_remove:
            if e in enemies:
                spawn_foods_from_enemy(e['body'])
                enemies.remove(e)

        update_camera(snake[0][0], snake[0][1])
        periodic_enemy_spawn(current_time)

    draw()
    clock.tick(FPS)

pygame.quit()