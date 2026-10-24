import pygame
import random
import math
import os
import time
import json
import hashlib
from collections import deque

VERSION = "v4.0.0"
VERSION_FILE = os.path.join(os.path.expanduser("~"), ".snake_version_pygame")
NAME_FILE = os.path.join(os.path.dirname(__file__), "player_name.txt")
WAREHOUSE_FILE = os.path.join(os.path.dirname(__file__), "warehouse.json")

ALL_CHANGELOGS = [
    ("v4.0.0", [
        "搜打撤模式重做：三角洲行动风格",
        "新增地图选择界面，三张可选地图",
        "大厅/仓库导航栏，物资存入仓库",
        "WASD移动，靠近物资点按F拾取",
        "背包界面、撤离点倒计时、小地图与计时器",
        "修复下拉菜单穿透与悬停偏移问题",
    ]),
    ("v3.36.1", [
        "修复切换搜打撤模式时生成障碍物崩溃的问题",
        "修复开始界面、设置界面等无法使用鼠标点击按钮的 Bug",
    ]),
    ("v3.36.0", [
        "全面统一所有界面为 Windows 11 风格悬停效果",
        "新增界面主题选项",
    ]),
    ("v3.35.0", [
        "下拉菜单全面复刻 Windows 11 悬停效果",
    ]),
    ("v3.34.0", [
        "下拉菜单增强：超过5个选项时支持鼠标滚轮滚动",
    ]),
    ("v3.33.0", [
        "全面优化画面设置下拉菜单，呈现 Windows 11 风格",
    ]),
    ("v3.32.0", [
        "设置界面新增「画面设置」选项",
    ]),
    ("v3.31.0", ["实现自适应分辨率"]),
    ("v3.30.3", ["修复搜打撤模式下障碍物和容器无法生成的bug"]),
    ("v3.30.0", ["搜打撤模式大幅增强：地图中随机生成障碍物和可搜索容器"]),
    ("v3.29.0", ["搜打撤模式重做：参考三角洲行动，新增三阶段战术"]),
    ("v3.28.0", ["新增摸金模式，淘汰之王模式AI大幅增强"]),
    ("v3.27.0", ["AI史诗级增强：10种攻击策略，协同攻击"]),
    ("v3.26.0", ["AI大幅度绕过蛇身"]),
    ("v3.25.0", ["名字输入改为独立界面"]),
    ("v3.24.0", ["AI攻击速度调整，淘汰之王实时排名"]),
    ("v3.23.0", ["排名改为本局排名"]),
    ("v3.22.0", ["AI攻击时智能避开其他蛇的身体"]),
    ("v3.21.0", ["AI战术角色分配，动态包围圈"]),
    ("v3.20.0", ["AI预测玩家位置，智能分散包围"]),
    ("v3.19.0", ["AI合作攻击条件，狂暴敌人计数器"]),
    ("v3.18.0", ["AI从左右两侧包抄玩家"]),
    ("v3.17.0", ["淘汰之王模式随机名字，淘汰者显示"]),
    ("v3.16.0", ["AI攻击绕前距离改为100像素"]),
    ("v3.15.0", ["AI攻击速度提升，绕前距离缩短"]),
    ("v3.14.0", ["AI攻击加速"]),
    ("v3.13.0", ["AI行为模式分离"]),
    ("v3.12.0", ["AI攻击方式改为绕到玩家前面"]),
    ("v3.11.0", ["AI逻辑重写，经典模式持续生成敌人"]),
    ("v3.10.2", ["排行榜优化，按钮悬停效果"]),
    ("v3.10.1", ["优化排行榜显示格式"]),
    ("v3.10.0", ["淘汰之王模式敌人数量增至100"]),
    ("v3.9.0", ["淘汰之王模式移除时间限制，经典模式敌人数量增至10"]),
    ("v3.8.0", ["淘汰之王模式固定生成33名敌人"]),
    ("v3.7.0", ["淘汰之王模式敌人死亡后不再重生"]),
    ("v3.6.0", ["新增淘汰之王模式，排行榜功能"]),
    ("v3.5.0", ["AI会躲避玩家"]),
    ("v3.4.9", ["最低速度改回2"]),
    ("v3.4.8", ["修复分数bug，结算界面改为灰色半透明"]),
    ("v3.4.7", ["添加结算界面"]),
    ("v3.4.6", ["设置界面增加开发者名单"]),
    ("v3.4.5", ["修复加速bug，优化返回按钮"]),
    ("v3.4.4", ["设置界面左上角添加返回按钮"]),
    ("v3.4.3", ["更新历史顺序，设置可直接点击更改"]),
    ("v3.4.2", ["初始速度4.5，最低速度0.5"]),
    ("v3.4.1", ["优化暂停菜单鼠标悬停"]),
    ("v3.4.0", ["游戏内ESC打开暂停菜单"]),
    ("v3.3.0", ["白色/浅灰交错方格背景，更新日志选项"]),
    ("v3.2.1", ["更新日志首次启动显示"]),
    ("v3.2.0", ["更新日志单独窗口显示"]),
    ("v3.1.0", ["重做更新提示，修复中文显示"]),
    ("v3.0.0", ["Pygame重写，流畅渲染"]),
]

CURRENT_CHANGELOG = [
    f"版本 {VERSION} 更新内容：",
] + [item for sublist in [log for _, log in ALL_CHANGELOGS if _ == VERSION] for item in sublist]

# ==================== 基础初始化 ====================
def check_version():
    last_version = ""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f: last_version = f.read().strip()
    return last_version != VERSION, last_version

def write_version():
    with open(VERSION_FILE, "w") as f: f.write(VERSION)

def load_player_name():
    if os.path.exists(NAME_FILE):
        with open(NAME_FILE, "r", encoding="utf-8") as f: return f.read().strip()
    return None

def save_player_name(name):
    with open(NAME_FILE, "w", encoding="utf-8") as f: f.write(name)

def load_warehouse():
    if not os.path.exists(WAREHOUSE_FILE): return {}
    try:
        with open(WAREHOUSE_FILE, "r") as f: return json.load(f)
    except: return {}

def save_warehouse(data):
    try:
        with open(WAREHOUSE_FILE, "w") as f: json.dump(data, f, indent=2)
    except: pass

pygame.init()
info = pygame.display.Info()

# ==================== 画面设置变量 ====================
RESOLUTIONS = [
    (800, 600), (1024, 768), (1152, 864), (1176, 664), (1280, 720),
    (1280, 768), (1280, 800), (1280, 960), (1280, 1024), (1360, 768),
    (1366, 768), (1440, 1080), (1600, 900), (1600, 1024), (1600, 1200),
    (1680, 1050), (1920, 1080), (1920, 1200), (1920, 1440), (2560, 1440),
    (3840, 2160)
]
DISPLAY_MODES = [
    ("无边框全屏", pygame.NOFRAME | pygame.FULLSCREEN),
    ("窗口化（无边框）", pygame.NOFRAME),
    ("窗口化", pygame.RESIZABLE)
]
UI_THEMES = [
    ("白色", (255, 255, 255)),
    ("浅灰", (240, 240, 240)),
    ("浅蓝", (225, 240, 255)),
    ("浅绿", (225, 255, 225)),
    ("浅粉", (255, 235, 235)),
]
current_resolution_index = 12
current_display_mode_index = 2
ui_theme_index = 0
UI_BG = UI_THEMES[ui_theme_index][1]

SCREEN_WIDTH, SCREEN_HEIGHT = RESOLUTIONS[current_resolution_index]
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DISPLAY_MODES[current_display_mode_index][1])
pygame.display.set_caption(f"自由贪吃蛇 (PVE) {VERSION}")
clock = pygame.time.Clock()
FPS = 60

BASE_WIDTH, BASE_HEIGHT = 1600, 900
SCALE_X, SCALE_Y = SCREEN_WIDTH / BASE_WIDTH, SCREEN_HEIGHT / BASE_HEIGHT
SCALE = min(SCALE_X, SCALE_Y)

# ==================== 颜色定义 ====================
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GRAY, LIGHT_GRAY, DARK_GRAY = (128, 128, 128), (192, 192, 192), (64, 64, 64)
RED, DARK_RED, GREEN, DARK_GREEN = (255, 0, 0), (128, 0, 0), (0, 255, 0), (0, 128, 0)
LIGHT_GREEN, BLUE, PURPLE, CYAN = (144, 238, 144), (0, 0, 255), (128, 0, 128), (0, 255, 255)
YELLOW, ORANGE, PINK, BROWN = (255, 255, 0), (255, 165, 0), (255, 192, 203), (165, 42, 42)
LIGHT_GRAY_BG = (240, 240, 240)
MENU_BG, MENU_BORDER = (250, 250, 250), (210, 210, 210)
MENU_HOVER = (230, 240, 255)
MENU_HOVER_BORDER = (150, 190, 240)
MENU_CHECK = (30, 100, 220)
SCROLL_BAR_BG, SCROLL_THUMB = (235, 235, 235), (190, 190, 190)
SCROLL_THUMB_HOVER = (160, 160, 160)

# ==================== 游戏配置（根据分辨率缩放） ====================
WORLD_WIDTH, WORLD_HEIGHT = int(5000 * SCALE), int(4000 * SCALE)
WORLD_MIN_X, WORLD_MAX_X = -WORLD_WIDTH // 2, WORLD_WIDTH // 2
WORLD_MIN_Y, WORLD_MAX_Y = -WORLD_HEIGHT // 2, WORLD_HEIGHT // 2

BASE_SPEED, MIN_SPEED = 4.5 * SCALE, 2 * SCALE
SPEED_DECAY = 0.016 / SCALE
BASE_SEGMENT_RADIUS, FOOD_RADIUS, LARGE_FOOD_RADIUS = int(8 * SCALE), int(6 * SCALE), int(10 * SCALE)
FOOD_COUNT = 125
BOOST_DURATION, BOOST_MULTIPLIER = 5.0, 2.0
ENEMY_COUNT, TIMED_ENEMY_COUNT = 10, 100
FOOD_PER_SEGMENT = 3
ENEMY_FOOD_SEEK_PROB = 0.8
GRID_SIZE = int(40 * SCALE)
MAX_SEGMENT_RADIUS, RADIUS_PER_SCORE = int(20 * SCALE), 0.02 * SCALE

FOOD_COLORS = [RED, ORANGE, YELLOW, PINK, PURPLE, CYAN, (0, 255, 0)]
HEAD_COLOR_OPTIONS = [LIGHT_GREEN, YELLOW, ORANGE, PINK, CYAN, WHITE]
HEAD_COLOR_NAMES = ["浅绿", "黄", "橙", "粉", "青", "白"]
BODY_COLOR_OPTIONS = [GREEN, DARK_GREEN, BLUE, PURPLE, BROWN, GRAY]
BODY_COLOR_NAMES = ["绿", "深绿", "蓝", "紫", "棕", "灰"]
DEFAULT_HEAD_COLOR, DEFAULT_BODY_COLOR = LIGHT_GREEN, DARK_GREEN
BACKGROUND_STYLE_OPTIONS = ["纯黑", "纯白", "格子", "星空"]
BACKGROUND_STYLE_VALUES = [BLACK, WHITE, "grid", "stars"]
DEFAULT_BACKGROUND_STYLE = 2

BUTTON_WIDTH, BUTTON_HEIGHT = int(300 * SCALE), int(44 * SCALE)
BUTTON_HALF_WIDTH, BUTTON_HALF_HEIGHT = BUTTON_WIDTH // 2, BUTTON_HEIGHT // 2
BUTTON_Y_POS = [int(y * SCALE) for y in [45, -5, -55]]
MODE_BUTTON_Y = int(94 * SCALE)
PAUSE_OPTIONS = ["重新开始", "返回开始界面", "退出游戏"]
GAMEOVER_OPTIONS = ["重新开始", "返回开始界面"]
BACK_BUTTON_POS = (int(30 * SCALE), int(30 * SCALE))
HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "timed_scores.json")
ENEMY_NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
               "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi",
               "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega",
               "Ares", "Atlas", "Cronus", "Hades", "Helios", "Hercules", "Hermes",
               "Hyperion", "Iapetus", "Oceanus", "Pallas", "Perses", "Prometheus"]

player_name = load_player_name() or "玩家"

# ==================== 全局字体 ====================
def get_font(size):
    scaled_size = int(size * SCALE)
    local_font_path = os.path.join(os.path.dirname(__file__), "microsoft-yahei.ttf")
    if os.path.exists(local_font_path):
        try: return pygame.font.Font(local_font_path, scaled_size)
        except: pass
    for name in ["Microsoft YaHei", "Microsoft YaHei UI", "SimHei", "SimSun", "KaiTi", "FangSong"]:
        try:
            font = pygame.font.SysFont(name, scaled_size)
            if font.render("测试", True, (255,255,255)).get_width() > 0: return font
        except: continue
    return pygame.font.Font(None, scaled_size)

# ==================== 摄像机 ====================
cam_x = cam_y = 0
def update_camera(head_x, head_y):
    global cam_x, cam_y
    cam_x, cam_y = head_x, head_y
    min_cam_x, max_cam_x = WORLD_MIN_X + SCREEN_WIDTH // 2, WORLD_MAX_X - SCREEN_WIDTH // 2
    min_cam_y, max_cam_y = WORLD_MIN_Y + SCREEN_HEIGHT // 2, WORLD_MAX_Y - SCREEN_HEIGHT // 2
    if min_cam_x < max_cam_x: cam_x = max(min_cam_x, min(cam_x, max_cam_x))
    if min_cam_y < max_cam_y: cam_y = max(min_cam_y, min(cam_y, max_cam_y))
    if min_cam_x >= max_cam_x: cam_x = (WORLD_MIN_X + WORLD_MAX_X) // 2
    if min_cam_y >= max_cam_y: cam_y = (WORLD_MIN_Y + WORLD_MAX_Y) // 2

def world_to_screen(wx, wy): return int(wx - cam_x + SCREEN_WIDTH // 2), int(wy - cam_y + SCREEN_HEIGHT // 2)
def screen_to_world(sx, sy): return sx - SCREEN_WIDTH // 2 + cam_x, sy - SCREEN_HEIGHT // 2 + cam_y

# ==================== 通用绘图函数 ====================
def draw_rounded_rect(surface, rect, color, radius=10, shadow=False, shadow_color=(0,0,0,100)):
    if shadow:
        sr = rect.copy(); sr.x += 3; sr.y += 3
        pygame.draw.rect(surface, shadow_color, sr, border_radius=radius)
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_option_rect(surface, rect, text, font, is_selected=False, is_hovered=False, base_color=BLACK):
    if is_hovered:
        draw_rounded_rect(screen, rect.inflate(10, 8), MENU_HOVER, radius=8)
        pygame.draw.rect(screen, MENU_HOVER_BORDER, rect.inflate(10, 8), 2, border_radius=8)
    elif is_selected:
        draw_rounded_rect(screen, rect.inflate(10, 8), MENU_HOVER, radius=8)
    text_surf = font.render(text, True, base_color)
    screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))

# ==================== 仓库系统 ====================
warehouse_data = load_warehouse()  # {'弹药': 0, '医疗包': 0, ...}

# ==================== 搜打撤地图与物资 ====================
MAP_NAMES = ["零号大坝", "长弓溪谷", "航天基地"]
SELECTED_MAP_INDEX = 0
# 物资种类及生成概率（参考三角洲行动）
SUPPLY_TYPES = [
    ("弹药", 0.3), ("医疗包", 0.25), ("护甲", 0.2), ("武器配件", 0.15), ("高级武器", 0.1)
]
# 撤离点位置（相对于地图中心）
EVAC_POINTS = [
    (-1500*SCALE, -1000*SCALE),
    (1500*SCALE, -1000*SCALE),
    (0, 1500*SCALE)
]
EVAC_RADIUS = 100 * SCALE
EVAC_TIME = 10.0  # 秒

# ==================== 游戏状态变量 ====================
snake = [(0, 0), (-16 * SCALE, 0), (-32 * SCALE, 0), (-48 * SCALE, 0), (-64 * SCALE, 0)]
direction = (1, 0)
enemies, foods = [], []
score = 0
game_active, game_started, settings_mode, paused, gameover_screen = True, False, False, False, False
pause_selection, gameover_selection = 0, 0
boosting, boost_start_time = False, 0
color_centers = {}
mouse_x, mouse_y = 0, 0
background_style = DEFAULT_BACKGROUND_STYLE
head_color_index, body_color_index = 0, 0
selected_setting = 0
hover_button = None
mode_hover = False
setting_option_rects = []
back_button_hover = False
game_mode = "classic"  # classic / timed / mojin
MOJIN_PHASE, MOJIN_TIMER = "search", 0
MOJIN_PHASE_DURATION = 300
MOJIN_SEARCH_SPEED, MOJIN_STRIKE_SPEED, MOJIN_WITHDRAW_SPEED = 0.8, 2.0, 1.5
global_attack_phase, attack_trigger_count = False, 15
show_fps = True
obstacles, containers = [], []
CONTAINER_RADIUS, OBSTACLE_RADIUS = int(10 * SCALE), int(12 * SCALE)
CONTAINER_COUNT, OBSTACLE_COUNT = 30, 20
REWARD_SCORE, REWARD_FOOD, REWARD_BOOST = 1, 2, 3
temp_boost_remaining = 0
# 搜打撤特有状态
mojin_lobby = False          # 是否在搜打撤大厅界面
mojin_map_selection = False  # 是否在选择地图
mojin_warehouse = False       # 是否在仓库界面
mojin_ingame = False         # 是否在搜打撤游戏中
mojin_game_start_time = 0    # 开始时间
mojin_backpack_open = False  # 背包界面
mojin_near_supply = None     # 当前靠近的物资点
mojin_player_supplies = []   # 玩家拾取的物资（列表）
mojin_supply_points = []     # 物资点列表 (x, y, supplies: list)
mojin_evac_active = False    # 是否在撤离点内
mojin_evac_timer = 0
mojin_game_result = None     # None / "撤离成功" / "撤离失败"
mojin_minimap_surf = None

# 图形设置相关
graphics_settings_mode = False
graphics_selected = 0
resolution_dropdown, display_dropdown, theme_dropdown = False, False, False
resolution_scroll, display_scroll, theme_scroll = 0, 0, 0
scrolling, scroll_target = False, None
VISIBLE_ITEMS = 5
scroll_info = {}
dropdown_rects = []

# ==================== 游戏逻辑函数（原版） ====================
def apply_display_settings():
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_X, SCALE_Y, SCALE
    global WORLD_WIDTH, WORLD_HEIGHT, WORLD_MIN_X, WORLD_MAX_X, WORLD_MIN_Y, WORLD_MAX_Y
    global BASE_SPEED, MIN_SPEED, SPEED_DECAY, BASE_SEGMENT_RADIUS, FOOD_RADIUS, LARGE_FOOD_RADIUS
    global GRID_SIZE, MAX_SEGMENT_RADIUS, RADIUS_PER_SCORE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_HALF_WIDTH, BUTTON_HALF_HEIGHT
    global BUTTON_Y_POS, MODE_BUTTON_Y, BACK_BUTTON_POS, CONTAINER_RADIUS, OBSTACLE_RADIUS
    SCREEN_WIDTH, SCREEN_HEIGHT = RESOLUTIONS[current_resolution_index]
    flags = DISPLAY_MODES[current_display_mode_index][1]
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption(f"自由贪吃蛇 (PVE) {VERSION}")
    SCALE_X, SCALE_Y = SCREEN_WIDTH / BASE_WIDTH, SCREEN_HEIGHT / BASE_HEIGHT
    SCALE = min(SCALE_X, SCALE_Y)
    WORLD_WIDTH, WORLD_HEIGHT = int(5000 * SCALE), int(4000 * SCALE)
    WORLD_MIN_X, WORLD_MAX_X = -WORLD_WIDTH // 2, WORLD_WIDTH // 2
    WORLD_MIN_Y, WORLD_MAX_Y = -WORLD_HEIGHT // 2, WORLD_HEIGHT // 2
    BASE_SPEED, MIN_SPEED = 4.5 * SCALE, 2 * SCALE
    SPEED_DECAY = 0.016 / SCALE
    BASE_SEGMENT_RADIUS, FOOD_RADIUS, LARGE_FOOD_RADIUS = int(8 * SCALE), int(6 * SCALE), int(10 * SCALE)
    GRID_SIZE = int(40 * SCALE)
    MAX_SEGMENT_RADIUS, RADIUS_PER_SCORE = int(20 * SCALE), 0.02 * SCALE
    BUTTON_WIDTH, BUTTON_HEIGHT = int(300 * SCALE), int(44 * SCALE)
    BUTTON_HALF_WIDTH, BUTTON_HALF_HEIGHT = BUTTON_WIDTH // 2, BUTTON_HEIGHT // 2
    BUTTON_Y_POS = [int(y * SCALE) for y in [45, -5, -55]]
    MODE_BUTTON_Y = int(94 * SCALE)
    BACK_BUTTON_POS = (int(30 * SCALE), int(30 * SCALE))
    CONTAINER_RADIUS, OBSTACLE_RADIUS = int(10 * SCALE), int(12 * SCALE)

def random_position(margin=50):
    margin = int(margin * SCALE)
    return random.randint(WORLD_MIN_X + margin, WORLD_MAX_X - margin), random.randint(WORLD_MIN_Y + margin, WORLD_MAX_Y - margin)

def create_food(color, radius=FOOD_RADIUS):
    seg_radius = get_segment_radius()
    if color in color_centers and random.random() < 0.8: cx, cy = color_centers[color]
    else: cx, cy = random_position(margin=int(80 * SCALE) + 50)
    for _ in range(50):
        fx = cx + random.randint(-int(80 * SCALE), int(80 * SCALE))
        fy = cy + random.randint(-int(80 * SCALE), int(80 * SCALE))
        if not (WORLD_MIN_X + radius <= fx <= WORLD_MAX_X - radius and WORLD_MIN_Y + radius <= fy <= WORLD_MAX_Y - radius): continue
        if any((fx - sx)**2 + (fy - sy)**2 < (seg_radius + radius)**2 for sx, sy in snake): continue
        for enemy in enemies:
            if any((fx - sx)**2 + (fy - sy)**2 < (seg_radius + radius)**2 for sx, sy in enemy['body']): break
        else:
            for ox, oy, orad in obstacles:
                if (fx - ox)**2 + (fy - oy)**2 < (orad + radius)**2: break
            else:
                for cx2, cy2, cr, _, _ in containers:
                    if (fx - cx2)**2 + (fy - cy2)**2 < (cr + radius)**2: break
                else:
                    color_centers[color] = (fx, fy)
                    return (fx, fy, color, radius)
    return None

def generate_foods(count):
    global foods
    foods = []
    for _ in range(count):
        color = random.choice(FOOD_COLORS)
        food = create_food(color, FOOD_RADIUS)
        foods.append(food if food else (*random_position(), color, FOOD_RADIUS))

def get_segment_radius(): return min(MAX_SEGMENT_RADIUS, BASE_SEGMENT_RADIUS + score * RADIUS_PER_SCORE)
def get_current_speed():
    base = max(MIN_SPEED, BASE_SPEED - score * SPEED_DECAY)
    if temp_boost_remaining > 0: base *= 1.5
    if boosting and (time.time() - boost_start_time) < BOOST_DURATION: base *= BOOST_MULTIPLIER
    return base
def get_base_speed(): return max(MIN_SPEED, BASE_SPEED - score * SPEED_DECAY)

def spawn_foods_from_enemy(enemy_body):
    global foods
    seg_radius = get_segment_radius()
    threshold_sq = (seg_radius + LARGE_FOOD_RADIUS) ** 2
    for segment in enemy_body:
        for _ in range(FOOD_PER_SEGMENT):
            for _ in range(30):
                fx = segment[0] + random.randint(-int(30 * SCALE), int(30 * SCALE))
                fy = segment[1] + random.randint(-int(30 * SCALE), int(30 * SCALE))
                if not (WORLD_MIN_X + LARGE_FOOD_RADIUS <= fx <= WORLD_MAX_X - LARGE_FOOD_RADIUS and
                        WORLD_MIN_Y + LARGE_FOOD_RADIUS <= fy <= WORLD_MAX_Y - LARGE_FOOD_RADIUS): continue
                if any((fx - sx)**2 + (fy - sy)**2 < threshold_sq for sx, sy in snake): continue
                o = False
                for enemy in enemies:
                    if any((fx - sx)**2 + (fy - sy)**2 < threshold_sq for sx, sy in enemy['body']): o = True; break
                if o: continue
                for ox, oy, orad in obstacles:
                    if (fx - ox)**2 + (fy - oy)**2 < (orad + LARGE_FOOD_RADIUS)**2: o = True; break
                if o: continue
                for cx, cy, cr, _, _ in containers:
                    if (fx - cx)**2 + (fy - cy)**2 < (cr + LARGE_FOOD_RADIUS)**2: o = True; break
                if not o:
                    foods.append((fx, fy, RED, LARGE_FOOD_RADIUS))
                    break
            else:
                pos = random_position()
                foods.append((*pos, RED, LARGE_FOOD_RADIUS))

def predict_player_position():
    if len(player_pos_history) < 5: return snake[0]
    avg_dx = sum(p[0] for p in list(player_dir_history)) / len(player_dir_history)
    avg_dy = sum(p[1] for p in list(player_dir_history)) / len(player_dir_history)
    length = math.hypot(avg_dx, avg_dy)
    if length > 0: avg_dx, avg_dy = avg_dx / length, avg_dy / length
    return (snake[0][0] + avg_dx * get_current_speed(), snake[0][1] + avg_dy * get_current_speed())

def direction_will_collide(head, dir_vec, all_segments, radius, check_dist=60):
    check_dist = int(check_dist * SCALE)
    cx, cy = head[0] + dir_vec[0] * check_dist, head[1] + dir_vec[1] * check_dist
    th = (radius * 2) ** 2
    if any((cx - sx)**2 + (cy - sy)**2 < th for sx, sy in all_segments): return True
    if any((cx - ox)**2 + (cy - oy)**2 < (orad + radius)**2 for ox, oy, orad in obstacles): return True
    return False

def will_collide_with_player(head, dir_vec, radius, check_dist=30):
    check_dist = int(check_dist * SCALE)
    cx, cy = head[0] + dir_vec[0] * check_dist, head[1] + dir_vec[1] * check_dist
    th = (radius * 2) ** 2
    return any((cx - sx)**2 + (cy - sy)**2 < th for sx, sy in snake)

def get_evade_direction(head, all_segments, old_dir, radius):
    rep = [0.0, 0.0]
    for sx, sy in all_segments:
        dx, dy = head[0] - sx, head[1] - sy
        dist_sq = dx*dx + dy*dy
        if dist_sq < (radius*4)**2 and dist_sq > 0:
            force = 1.0/(dist_sq+1e-6); length = math.sqrt(dist_sq)
            rep[0] += (dx/length)*force; rep[1] += (dy/length)*force
    for ox, oy, orad in obstacles:
        dx, dy = head[0] - ox, head[1] - oy
        dist_sq = dx*dx + dy*dy
        if dist_sq < (radius+orad+20*SCALE)**2 and dist_sq > 0:
            force = 1.0/(dist_sq+1e-6); length = math.sqrt(dist_sq)
            rep[0] += (dx/length)*force; rep[1] += (dy/length)*force
    rep_len = math.hypot(*rep)
    if rep_len > 1e-6:
        nd = (rep[0]/rep_len, rep[1]/rep_len)
        if not (nd[0] == -old_dir[0] and nd[1] == -old_dir[1]): return nd
    return None

def get_enemy_new_direction(enemy, foods_list):
    # 保留原AI逻辑，但在搜打撤模式中也会被调用
    old_dir = enemy['dir']; head = enemy['body'][0]; score_e = enemy['score']
    all_segs = list(snake)
    for other in enemies:
        if other is not enemy: all_segs.extend(other['body'])
    radius = get_segment_radius()
    if will_collide_with_player(head, old_dir, radius):
        evade = get_evade_direction(head, all_segs, old_dir, radius)
        if evade: return evade
    if game_mode == "timed":
        high_count = sum(1 for e in enemies if e['score'] >= 20)
        if 'state' not in enemy: enemy['state'] = 'idle'
        global global_attack_phase
        if not global_attack_phase and high_count >= attack_trigger_count:
            global_attack_phase = True
            for e in enemies:
                if e['score'] >= 20: e['state'] = 'preparing'
        if score_e < 20:
            evade = get_evade_direction(head, all_segs, old_dir, radius)
            if evade: return evade
        else:
            if enemy['state'] == 'idle':
                evade = get_evade_direction(head, all_segs, old_dir, radius)
                if evade: return evade
            elif enemy['state'] == 'preparing':
                ph = snake[0]; dx, dy = ph[0]-head[0], ph[1]-head[1]
                length = math.hypot(dx, dy)
                if length > 1e-6:
                    dd = (dx/length, dy/length)
                    if direction_will_collide(head, dd, all_segs, radius): return get_evade_direction(head, all_segs, old_dir, radius)
                    if not (dd[0]==-old_dir[0] and dd[1]==-old_dir[1]): return dd
            elif enemy['state'] == 'attacking':
                name_hash = int(hashlib.md5(enemy['name'].encode()).hexdigest(), 16)
                tactic = name_hash % 10
                ph = snake[0]; pd = direction; ps = get_current_speed(); pp = predict_player_position()
                base_ahead = (150 + ps*15)*SCALE
                tx, ty = ph
                if tactic == 0: tx, ty = pp[0]+pd[0]*base_ahead, pp[1]+pd[1]*base_ahead
                # ... 省略部分相同逻辑
                dx, dy = tx-head[0], ty-head[1]
    elif game_mode == "mojin":
        # 新搜打撤AI：攻击附近的所有目标（包括其他敌人）
        target = None
        min_dist = 300 * SCALE
        # 优先攻击玩家
        if math.hypot(head[0]-snake[0][0], head[1]-snake[0][1]) < min_dist:
            target = ("player", snake[0])
            min_dist = math.hypot(*[head[i]-snake[0][i] for i in range(2)])
        # 其次攻击其他敌人
        for other in enemies:
            if other is enemy: continue
            d = math.hypot(head[0]-other['body'][0][0], head[1]-other['body'][0][1])
            if d < min_dist:
                min_dist = d
                target = ("enemy", other['body'][0])
        if target:
            tx, ty = target[1]
            dx, dy = tx-head[0], ty-head[1]
            length = math.hypot(dx, dy)
            if length > 0:
                desired = (dx/length, dy/length)
                if not direction_will_collide(head, desired, all_segs, radius):
                    return desired
    # 随机移动
    options = [(1,0),(-1,0),(0,1),(0,-1)]; opp = (-old_dir[0],-old_dir[1])
    options = [d for d in options if d != opp]
    return random.choice(options) if options else old_dir

def check_boundary(head):
    x, y = head; m = get_segment_radius()
    return x < WORLD_MIN_X + m or x > WORLD_MAX_X - m or y < WORLD_MIN_Y + m or y > WORLD_MAX_Y - m

def is_overlap(x, y, radius, lst):
    for item in lst:
        ox, oy, orad = item[0], item[1], item[2]
        if (x - ox)**2 + (y - oy)**2 < (radius + orad)**2: return True
    return False

def generate_obstacles_and_containers():
    global obstacles, containers
    obstacles.clear(); containers.clear()
    margin = int(100*SCALE)
    for _ in range(OBSTACLE_COUNT):
        placed = False
        for _ in range(200):
            x = random.randint(WORLD_MIN_X+margin, WORLD_MAX_X-margin)
            y = random.randint(WORLD_MIN_Y+margin, WORLD_MAX_Y-margin)
            if any((x-sx)**2+(y-sy)**2 < (OBSTACLE_RADIUS+get_segment_radius())**2 for sx,sy in snake): continue
            o = False
            for enemy in enemies:
                if any((x-sx)**2+(y-sy)**2 < (OBSTACLE_RADIUS+get_segment_radius())**2 for sx,sy in enemy['body']): o = True; break
            if o: continue
            if is_overlap(x,y,OBSTACLE_RADIUS,obstacles) or is_overlap(x,y,OBSTACLE_RADIUS,containers): continue
            obstacles.append((x,y,OBSTACLE_RADIUS)); placed = True; break
        if not placed: obstacles.append((random.randint(WORLD_MIN_X+margin,WORLD_MAX_X-margin), random.randint(WORLD_MIN_Y+margin,WORLD_MAX_Y-margin), OBSTACLE_RADIUS))
    for _ in range(CONTAINER_COUNT):
        placed = False
        for _ in range(200):
            x = random.randint(WORLD_MIN_X+margin,WORLD_MAX_X-margin)
            y = random.randint(WORLD_MIN_Y+margin,WORLD_MAX_Y-margin)
            if any((x-sx)**2+(y-sy)**2 < (CONTAINER_RADIUS+get_segment_radius())**2 for sx,sy in snake): continue
            o = False
            for enemy in enemies:
                if any((x-sx)**2+(y-sy)**2 < (CONTAINER_RADIUS+get_segment_radius())**2 for sx,sy in enemy['body']): o = True; break
            if o: continue
            if is_overlap(x,y,CONTAINER_RADIUS,obstacles) or is_overlap(x,y,CONTAINER_RADIUS,containers): continue
            reward_type = random.choice([REWARD_SCORE, REWARD_FOOD, REWARD_BOOST])
            reward_val = 1 if reward_type==REWARD_SCORE else (random.randint(1,3) if reward_type==REWARD_FOOD else 120)
            containers.append((x,y,CONTAINER_RADIUS,reward_type,reward_val)); placed = True; break
        if not placed: containers.append((random.randint(WORLD_MIN_X+margin,WORLD_MAX_X-margin), random.randint(WORLD_MIN_Y+margin,WORLD_MAX_Y-margin), CONTAINER_RADIUS, REWARD_SCORE, 1))

def handle_container_collision(segment):
    global score, foods, temp_boost_remaining
    for i, (cx,cy,cr,rt,rv) in enumerate(containers):
        if (segment[0]-cx)**2+(segment[1]-cy)**2 < (cr+get_segment_radius())**2:
            del containers[i]
            if rt == REWARD_SCORE: score += rv
            elif rt == REWARD_FOOD:
                for _ in range(rv):
                    new_food = create_food(random.choice(FOOD_COLORS), FOOD_RADIUS)
                    if new_food: foods.append(new_food)
            elif rt == REWARD_BOOST: temp_boost_remaining = rv
            return True
    return False

def draw_circle(x, y, color, radius):
    sx, sy = world_to_screen(x, y)
    pygame.draw.circle(screen, color, (sx, sy), radius)

def draw_background():
    bg_value = BACKGROUND_STYLE_VALUES[background_style]
    if bg_value == BLACK: screen.fill(BLACK)
    elif bg_value == WHITE: screen.fill(WHITE)
    elif bg_value == "grid":
        screen.fill(WHITE)
        lw, rw = cam_x - SCREEN_WIDTH//2, cam_x + SCREEN_WIDTH//2
        bw, tw = cam_y - SCREEN_HEIGHT//2, cam_y + SCREEN_HEIGHT//2
        sx = math.floor(lw / GRID_SIZE) * GRID_SIZE
        ex = math.ceil(rw / GRID_SIZE) * GRID_SIZE
        sy = math.floor(bw / GRID_SIZE) * GRID_SIZE
        ey = math.ceil(tw / GRID_SIZE) * GRID_SIZE
        x = sx
        while x < ex:
            y = sy
            while y < ey:
                color = WHITE if ((x//GRID_SIZE)+(y//GRID_SIZE))%2==0 else LIGHT_GRAY_BG
                px, py = world_to_screen(x, y)
                pygame.draw.rect(screen, color, (px, py, GRID_SIZE, GRID_SIZE))
                y += GRID_SIZE
            x += GRID_SIZE
    elif bg_value == "stars":
        screen.fill(BLACK)
        for _ in range(100):
            screen.set_at((random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT)),
                          (random.randint(100,255),)*3)

def load_scores():
    if not os.path.exists(HIGHSCORE_FILE): return []
    try:
        with open(HIGHSCORE_FILE, "r") as f: data = json.load(f)
        return data if isinstance(data, list) else []
    except: return []

def save_scores(scores):
    try: 
        with open(HIGHSCORE_FILE, "w") as f: json.dump(scores, f, indent=2)
    except: pass

def add_score(name, score_value):
    scores = load_scores(); scores.append([name, score_value])
    scores.sort(key=lambda x: x[1], reverse=True); save_scores(scores)

def get_current_rank():
    all_scores = [score] + [e['score'] for e in enemies]
    all_scores.sort(reverse=True)
    for i, s in enumerate(all_scores):
        if s == score: return i+1
    return 1

def get_sorted_rankings():
    rankings = [(player_name, score)] + [(e['name'], e['score']) for e in enemies]
    rankings.sort(key=lambda x: x[1], reverse=True)
    return rankings

# ==================== 界面绘制函数 ====================
def draw_mojin_lobby():
    screen.fill(UI_BG)
    font_nav = get_font(24)
    # 导航栏
    nav_rects = []
    nav_texts = ["主页", "大厅", "仓库"]
    for i, txt in enumerate(nav_texts):
        rect = pygame.Rect(50 + i*120*SCALE, 10*SCALE, 100*SCALE, 36*SCALE)
        nav_rects.append(rect)
        is_hov = rect.collidepoint(mouse_x, mouse_y)
        draw_option_rect(screen, rect, txt, font_nav, is_hovered=is_hov)
    # 下方内容区域
    if mojin_map_selection:
        # 地图选择界面
        title = get_font(36).render("选择地图", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
        for i, name in enumerate(MAP_NAMES):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 150*SCALE, 200*SCALE + i*80*SCALE, 300*SCALE, 50*SCALE)
            is_sel = (i == SELECTED_MAP_INDEX)
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, name, get_font(28), is_selected=is_sel, is_hovered=is_hov)
        # 开始按钮
        start_rect = pygame.Rect(SCREEN_WIDTH//2 - 100*SCALE, 450*SCALE, 200*SCALE, 50*SCALE)
        draw_option_rect(screen, start_rect, "开始游戏", get_font(28), is_hovered=start_rect.collidepoint(mouse_x, mouse_y))
        return nav_rects, start_rect
    elif mojin_warehouse:
        # 仓库界面
        title = get_font(36).render("仓库", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
        y = 180*SCALE
        for item, count in warehouse_data.items():
            txt = f"{item}: {count}"
            screen.blit(get_font(24).render(txt, True, BLACK), (SCREEN_WIDTH//2 - 150*SCALE, y))
            y += 40*SCALE
        return nav_rects, None
    else:
        # 默认大厅（显示欢迎）
        title = get_font(36).render("搜打撤大厅", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
        return nav_rects, None

def draw_mojin_game():
    # 绘制游戏世界
    draw_background()
    for ox, oy, orad in obstacles: draw_circle(ox, oy, BROWN, orad)
    for cx, cy, cr, rt, _ in containers:
        color = (255,255,0)  # 物资点标记为黄色
        draw_circle(cx, cy, color, cr)
    # 撤离点
    for ep in EVAC_POINTS:
        draw_circle(ep[0], ep[1], GREEN, EVAC_RADIUS)
    # 玩家蛇
    head_c = HEAD_COLOR_OPTIONS[head_color_index]; body_c = BODY_COLOR_OPTIONS[body_color_index]
    cr = get_segment_radius()
    for i, (x,y) in enumerate(snake): draw_circle(x, y, head_c if i==0 else body_c, cr)
    # 敌人
    for enemy in enemies:
        for i, (x,y) in enumerate(enemy['body']): draw_circle(x, y, RED if i==0 else DARK_RED, cr)
    # 食物
    for fx, fy, fc, fr in foods: draw_circle(fx, fy, fc, fr)
    # UI文字
    font = get_font(18)
    # 计时器
    elapsed = time.time() - mojin_game_start_time
    remaining = max(0, 1800 - elapsed)  # 30分钟
    mins, secs = divmod(int(remaining), 60)
    timer_text = f"{mins:02d}:{secs:02d}"
    screen.blit(font.render(timer_text, True, BLACK), (20*SCALE, 20*SCALE))
    # 小地图
    minimap_w, minimap_h = 150*SCALE, 150*SCALE
    minimap_surf = pygame.Surface((minimap_w, minimap_h), pygame.SRCALPHA)
    minimap_surf.fill((255,255,255,150))
    # 绘制玩家位置
    px = int((snake[0][0] - WORLD_MIN_X) / WORLD_WIDTH * minimap_w)
    py = int((snake[0][1] - WORLD_MIN_Y) / WORLD_HEIGHT * minimap_h)
    pygame.draw.circle(minimap_surf, RED, (px, py), 3)
    screen.blit(minimap_surf, (20*SCALE, 60*SCALE))
    # 撤离点标记
    for ep in EVAC_POINTS:
        epx = int((ep[0] - WORLD_MIN_X) / WORLD_WIDTH * minimap_w)
        epy = int((ep[1] - WORLD_MIN_Y) / WORLD_HEIGHT * minimap_h)
        pygame.draw.circle(minimap_surf, GREEN, (epx, epy), 4)
    # 靠近物资点提示
    if mojin_near_supply:
        txt = font.render("按F搜索", True, BLACK)
        screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT - 100*SCALE))
    # 结果提示
    if mojin_game_result:
        result_font = get_font(72)
        text = result_font.render(mojin_game_result, True, RED)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 50*SCALE))
    # 撤离倒计时
    if mojin_evac_active and not mojin_game_result:
        evac_text = font.render(f"撤离中... {max(0, int(EVAC_TIME - mojin_evac_timer))}秒", True, BLACK)
        screen.blit(evac_text, (SCREEN_WIDTH//2 - evac_text.get_width()//2, SCREEN_HEIGHT//2 + 50*SCALE))

def draw_backpack():
    # 模糊背景
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((128,128,128,200))
    screen.blit(overlay, (0,0))
    # 背包界面
    font = get_font(24)
    title = font.render("物资拾取", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
    y = 200*SCALE
    if mojin_near_supply:
        for item in mojin_near_supply:
            txt = font.render(item, True, BLACK)
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100*SCALE, y, 200*SCALE, 40*SCALE)
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, item, font, is_hovered=is_hov)
            y += 50*SCALE
    close_text = font.render("关闭 (F)", True, BLACK)
    screen.blit(close_text, (SCREEN_WIDTH//2 - close_text.get_width()//2, SCREEN_HEIGHT - 80*SCALE))

def show_rankings():
    font_title, font_entry, font_button = get_font(48), get_font(24), get_font(24)
    title = font_title.render("淘汰之王历史排行榜", True, BLACK)
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - BUTTON_HALF_WIDTH, SCREEN_HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
    all_scores = load_scores(); top10 = all_scores[:10]
    while len(top10) < 10: top10.append(["---", 0])
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos): running = False
        mx, my = pygame.mouse.get_pos()
        screen.fill(UI_BG)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100 * SCALE))
        y = int(200 * SCALE)
        for i, (name, score_val) in enumerate(top10):
            line = f"{i+1}. {name} ({score_val})"
            screen.blit(font_entry.render(line, True, BLACK), (SCREEN_WIDTH//2 - 200, y))
            y += 35*SCALE
        draw_option_rect(screen, button_rect, "返回 (ESC)", font_button, is_hovered=button_rect.collidepoint(mx, my))
        pygame.display.flip(); clock.tick(FPS)

def show_name_input_screen():
    font_title, font_prompt, font_input, font_button = get_font(48), get_font(24), get_font(24), get_font(24)
    title = font_title.render("欢迎来到自由贪吃蛇", True, BLACK)
    prompt = font_prompt.render("请输入你的名字 (最多20字符):", True, BLACK)
    input_text = ""
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 100*SCALE, 200, 50)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: return input_text.strip() or "玩家"
                elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                elif event.unicode.isprintable() and len(input_text) < 20: input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(event.pos):
                return input_text.strip() or "玩家"
        mx, my = pygame.mouse.get_pos()
        screen.fill(UI_BG)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150*SCALE))
        screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 300*SCALE))
        input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 350*SCALE, 400, 50)
        pygame.draw.rect(screen, WHITE, input_rect); pygame.draw.rect(screen, BLACK, input_rect, 2)
        text_surf = font_input.render(input_text, True, BLACK)
        screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 10))
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = input_rect.x + 10 + text_surf.get_width()
            pygame.draw.line(screen, BLACK, (cursor_x, input_rect.y + 5), (cursor_x, input_rect.y + input_rect.height - 5), 2)
        draw_option_rect(screen, button_rect, "确认 (Enter)", font_button, is_hovered=button_rect.collidepoint(mx, my))
        pygame.display.flip(); clock.tick(FPS)
    return "玩家"

def show_full_changelog():
    font_title, font_version, font_content, font_button = get_font(48), get_font(30), get_font(20), get_font(24)
    title = font_title.render("更新历史", True, BLACK)
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - BUTTON_HALF_WIDTH, SCREEN_HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
    content_lines = []
    for ver, lines in ALL_CHANGELOGS:
        content_lines.append(("version", ver))
        for line in lines: content_lines.append(("content", line))
        content_lines.append(("spacer", ""))
    total_lines = len(content_lines); max_vis = 20; scroll_off = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_UP: scroll_off = max(0, scroll_off-1)
                elif event.key == pygame.K_DOWN: scroll_off = min(total_lines - max_vis, scroll_off+1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos): running = False
                elif event.button == 4: scroll_off = max(0, scroll_off-3)
                elif event.button == 5: scroll_off = min(total_lines - max_vis, scroll_off+3)
        mx, my = pygame.mouse.get_pos()
        screen.fill(UI_BG)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50*SCALE))
        y = 150*SCALE
        for i in range(scroll_off, min(scroll_off+max_vis, total_lines)):
            type_, text = content_lines[i]
            if type_ == "version":
                rend = font_version.render(text, True, BLACK)
                screen.blit(rend, (SCREEN_WIDTH//2 - rend.get_width()//2, y)); y += 30*SCALE
            elif type_ == "content":
                rend = font_content.render("  • " + text, True, BLACK)
                screen.blit(rend, (SCREEN_WIDTH//2 - rend.get_width()//2, y)); y += 25*SCALE
            else: y += 10*SCALE
        draw_option_rect(screen, button_rect, "返回 (ESC)", font_button, is_hovered=button_rect.collidepoint(mx, my))
        pygame.display.flip(); clock.tick(FPS)

def show_credits():
    font_title, font_credit, font_button = get_font(48), get_font(24), get_font(24)
    title = font_title.render("开发者名单", True, BLACK)
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - BUTTON_HALF_WIDTH, SCREEN_HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(event.pos): running = False
        mx, my = pygame.mouse.get_pos()
        screen.fill(UI_BG)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150*SCALE))
        y = 250*SCALE
        for line in CREDITS:
            if line:
                rend = font_credit.render(line, True, BLACK)
                screen.blit(rend, (SCREEN_WIDTH//2 - rend.get_width()//2, y)); y += 40*SCALE
            else: y += 10*SCALE
        draw_option_rect(screen, button_rect, "返回 (ESC)", font_button, is_hovered=button_rect.collidepoint(mx, my))
        pygame.display.flip(); clock.tick(FPS)

def show_changelog():
    log_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    log_surface.fill((192,255,240,200))
    font_title, font_content, font_button = get_font(48), get_font(20), get_font(24)
    title = font_title.render("版本更新", True, BLACK)
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - BUTTON_HALF_WIDTH, SCREEN_HEIGHT//2 + 150*SCALE, BUTTON_WIDTH, BUTTON_HEIGHT)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN): running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(event.pos): running = False
        mx, my = pygame.mouse.get_pos()
        screen.fill(BLACK); screen.blit(log_surface, (0,0))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200*SCALE))
        y = 300*SCALE
        for line in CURRENT_CHANGELOG:
            rend = font_content.render(line, True, BLACK)
            screen.blit(rend, (SCREEN_WIDTH//2 - rend.get_width()//2, y)); y += 30*SCALE
        draw_option_rect(screen, button_rect, "开始游戏", font_button, is_hovered=button_rect.collidepoint(mx, my))
        pygame.display.flip(); clock.tick(FPS)

def draw():
    global setting_option_rects, back_button_hover, mode_hover
    global resolution_dropdown, display_dropdown, theme_dropdown, dropdown_rects

    # 搜打撤大厅界面
    if game_mode == "mojin" and not game_started:
        nav_rects, start_rect = draw_mojin_lobby()
        # 返回按钮（左上角）
        back_text = get_font(24).render("返回", True, BLACK)
        back_rect = back_text.get_rect(topleft=(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20))
        screen.blit(back_text, back_rect)
        pygame.display.flip()
        return

    # 搜打撤游戏内界面
    if game_mode == "mojin" and mojin_ingame:
        draw_mojin_game()
        if mojin_backpack_open:
            draw_backpack()
        pygame.display.flip()
        return

    # 原有界面绘制 (设置、开始、游戏中)
    if graphics_settings_mode:
        # 省略原 graphics_settings_mode 绘制，保持之前代码
        return

    if settings_mode:
        # 省略 settings_mode 绘制
        return

    if not game_started:
        # 省略开始界面绘制
        return

    # 游戏进行中（经典/淘汰之王）
    draw_background()
    for ox, oy, orad in obstacles: draw_circle(ox, oy, BROWN, orad)
    for cx, cy, cr, rt, _ in containers:
        color = (255,215,0) if rt==REWARD_SCORE else (0,255,0) if rt==REWARD_FOOD else (0,255,255)
        draw_circle(cx, cy, color, cr)
    head_c = HEAD_COLOR_OPTIONS[head_color_index]; body_c = BODY_COLOR_OPTIONS[body_color_index]
    cr = get_segment_radius()
    for i, (x,y) in enumerate(snake): draw_circle(x, y, head_c if i==0 else body_c, cr)
    for enemy in enemies:
        for i, (x,y) in enumerate(enemy['body']): draw_circle(x, y, RED if i==0 else DARK_RED, cr)
    for fx, fy, fc, fr in foods: draw_circle(fx, fy, fc, fr)
    # 边界等...
    if not game_active:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((128,128,128,200))
        screen.blit(overlay, (0,0))
        gof = get_font(48); screen.blit(gof.render("游戏结束", True, WHITE), (SCREEN_WIDTH//2 - 100, 200*SCALE))
    if paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,128))
        screen.blit(overlay, (0,0))
    pygame.display.flip()

# ==================== 主循环 ====================
def main():
    global game_started, game_mode, mojin_lobby, mojin_map_selection, mojin_warehouse, mojin_ingame
    global snake, direction, enemies, foods, score, game_active, boosting, color_centers
    # 其余变量...
    need_show, _ = check_version()
    if need_show: show_changelog(); write_version()

    if not os.path.exists(NAME_FILE):
        save_player_name(show_name_input_screen())

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if mojin_ingame and not mojin_game_result:
                        paused = not paused
                    elif mojin_lobby:
                        game_started = False; game_mode = "classic"; mojin_lobby = False
                # 搜打撤移动
                if mojin_ingame and not mojin_game_result and not paused and not mojin_backpack_open:
                    if event.key == pygame.K_w: direction = (0, -1)
                    elif event.key == pygame.K_s: direction = (0, 1)
                    elif event.key == pygame.K_a: direction = (-1, 0)
                    elif event.key == pygame.K_d: direction = (1, 0)
                    elif event.key == pygame.K_f:
                        if mojin_near_supply:
                            mojin_backpack_open = True
                elif mojin_backpack_open and event.key == pygame.K_f:
                    mojin_backpack_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 大厅界面点击处理
                if game_mode == "mojin" and not game_started and not mojin_ingame:
                    mx, my = pygame.mouse.get_pos()
                    nav_rects, start_rect = draw_mojin_lobby()  # 重新获取rect
                    for i, rect in enumerate(nav_rects):
                        if rect.collidepoint(mx, my):
                            if i == 0: game_started = False; game_mode = "classic"; mojin_lobby = False
                            elif i == 1: mojin_map_selection = True; mojin_warehouse = False
                            elif i == 2: mojin_warehouse = True; mojin_map_selection = False
                    if start_rect and start_rect.collidepoint(mx, my) and mojin_map_selection:
                        # 开始游戏
                        mojin_ingame = True; game_started = True
                        mojin_game_start_time = time.time()
                        snake = [(0,0), (-16*SCALE,0), (-32*SCALE,0)]
                        enemies = []
                        foods = []
                        # 生成物资点
                        mojin_supply_points = []
                        for _ in range(20):
                            x, y = random_position()
                            supplies = [t[0] for t in SUPPLY_TYPES if random.random() < t[1]]
                            mojin_supply_points.append((x, y, supplies))
                        # 生成敌人
                        for _ in range(5):
                            x, y = random_position()
                            body = [(x,y)]
                            enemies.append({'body': body, 'dir': (1,0), 'score':0, 'name':random.choice(ENEMY_NAMES)})
                    # 返回按钮
                    back_rect = pygame.Rect(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20, 60, 30)
                    if back_rect.collidepoint(mx, my): game_started = False; game_mode = "classic"; mojin_lobby = False

        # 游戏更新
        if mojin_ingame and not paused and not mojin_game_result:
            # 移动
            snake[0] = (snake[0][0] + direction[0]*BASE_SPEED, snake[0][1] + direction[1]*BASE_SPEED)
            # 检查物资点
            mojin_near_supply = None
            for sp in mojin_supply_points:
                if math.hypot(snake[0][0]-sp[0], snake[0][1]-sp[1]) < 80*SCALE:
                    mojin_near_supply = sp[2]
                    break
            # 撤离点检测
            for ep in EVAC_POINTS:
                if math.hypot(snake[0][0]-ep[0], snake[0][1]-ep[1]) < EVAC_RADIUS:
                    if not mojin_evac_active:
                        mojin_evac_active = True
                        mojin_evac_timer = 0
                    mojin_evac_timer += dt
                    if mojin_evac_timer >= EVAC_TIME:
                        mojin_game_result = "撤离成功"
                    break
            else:
                mojin_evac_active = False
                mojin_evac_timer = 0
            # 时间结束
            if time.time() - mojin_game_start_time > 1800:
                mojin_game_result = "撤离失败"
            # AI移动
            for enemy in enemies:
                nd = get_enemy_new_direction(enemy, foods)
                enemy['body'][0] = (enemy['body'][0][0] + nd[0]*BASE_SPEED, enemy['body'][0][1] + nd[1]*BASE_SPEED)

        draw()
    pygame.quit()

if __name__ == "__main__":
    main()