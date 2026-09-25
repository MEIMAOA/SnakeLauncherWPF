import pygame
import random
import math
import os
import time
import json
import hashlib
from collections import deque

VERSION = "v4.0.2"
VERSION_FILE = os.path.join(os.path.expanduser("~"), ".snake_version_pygame")
NAME_FILE = os.path.join(os.path.dirname(__file__), "player_name.txt")
WAREHOUSE_FILE = os.path.join(os.path.dirname(__file__), "warehouse.json")

ALL_CHANGELOGS = [
    ("v4.0.2", [
        "修复搜打撤模式需要按WASD才会移动的bug（现已自动移动）",
        "修复下拉菜单穿透点击到下层按钮的问题",
        "修复模式选择悬停效果与实际文字位置不符的偏移",
        "优化搜打撤移动手感，方向由WASD持续控制",
    ]),
    ("v4.0.1", [
        "修复输入名字时 UnboundLocalError 崩溃的 Bug",
        "补全设置界面、开始界面、暂停菜单等所有界面",
        "提升搜打撤模式稳定性",
    ]),
    ("v4.0.0", [
        "搜打撤模式重做：三角洲行动风格",
        "新增地图选择界面，三张可选地图",
        "大厅/仓库导航栏，物资存入仓库",
        "WASD移动，靠近物资点按F拾取",
        "背包界面、撤离点倒计时、小地图与计时器",
        "修复下拉菜单穿透与悬停偏移问题",
    ]),
    ("v3.36.1", ["修复切换搜打撤模式时生成障碍物崩溃的问题"]),
    ("v3.36.0", ["全面统一所有界面为 Windows 11 风格悬停效果"]),
    ("v3.35.0", ["下拉菜单全面复刻 Windows 11 悬停效果"]),
    ("v3.34.0", ["下拉菜单增强：超过5个选项时支持鼠标滚轮滚动"]),
    ("v3.33.0", ["全面优化画面设置下拉菜单，呈现 Windows 11 风格"]),
    ("v3.32.0", ["设置界面新增「画面设置」选项"]),
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
player_pos_history = deque(maxlen=60)
player_dir_history = deque(maxlen=60)

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
game_mode = "classic"
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
CREDITS = ["开发者名单", "", "策划 & 开发：没冇啊", "代码：deep seek，没冇啊", "美术设计：deep seek，没冇啊", "QA：没冇啊", "", "特别感谢：所有支持本游戏的玩家", "", "Pygame 社区", "Python 编程语言"]

warehouse_data = load_warehouse()
MAP_NAMES = ["零号大坝", "长弓溪谷", "航天基地"]
SELECTED_MAP_INDEX = 0
SUPPLY_TYPES = [
    ("弹药", 0.3), ("医疗包", 0.25), ("护甲", 0.2), ("武器配件", 0.15), ("高级武器", 0.1)
]
EVAC_POINTS = [
    (-1500*SCALE, -1000*SCALE),
    (1500*SCALE, -1000*SCALE),
    (0, 1500*SCALE)
]
EVAC_RADIUS = 100 * SCALE
EVAC_TIME = 10.0
mojin_lobby = True
mojin_map_selection = False
mojin_warehouse = False
mojin_ingame = False
mojin_game_start_time = 0
mojin_backpack_open = False
mojin_near_supply = None
mojin_player_supplies = []
mojin_supply_points = []
mojin_evac_active = False
mojin_evac_timer = 0
mojin_game_result = None

graphics_settings_mode = False
graphics_selected = 0
resolution_dropdown, display_dropdown, theme_dropdown = False, False, False
resolution_scroll, display_scroll, theme_scroll = 0, 0, 0
scrolling, scroll_target = False, None
VISIBLE_ITEMS = 5
scroll_info = {}
dropdown_rects = []

# ---------- 游戏逻辑函数 ----------
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
                elif tactic == 1:
                    perp = (-pd[1], pd[0]); off = 200*SCALE; ah = base_ahead*0.8
                    bt = (pp[0]+pd[0]*ah, pp[1]+pd[1]*ah); tx, ty = bt[0]+perp[0]*off, bt[1]+perp[1]*off
                elif tactic == 2:
                    perp = (-pd[1], pd[0]); off = -200*SCALE; ah = base_ahead*0.8
                    bt = (pp[0]+pd[0]*ah, pp[1]+pd[1]*ah); tx, ty = bt[0]+perp[0]*off, bt[1]+perp[1]*off
                elif tactic == 3: tx, ty = pp[0]-pd[0]*200*SCALE, pp[1]-pd[1]*200*SCALE
                elif tactic == 4: tx, ty = ph[0]-pd[0]*250*SCALE, ph[1]-pd[1]*250*SCALE
                elif tactic == 5:
                    perp = (-pd[1], pd[0]); t = (name_hash%1000)/500.0-1.0; off = t*250*SCALE; ah = base_ahead*0.7
                    bt = (pp[0]+pd[0]*ah, pp[1]+pd[1]*ah); tx, ty = bt[0]+perp[0]*off, bt[1]+perp[1]*off
                elif tactic == 6:
                    spread = 250*SCALE; angle = (name_hash%100)/100.0*math.pi*2; ox=math.cos(angle)*spread; oy=math.sin(angle)*spread
                    bt = (pp[0]+pd[0]*base_ahead, pp[1]+pd[1]*base_ahead); tx, ty = bt[0]+ox, bt[1]+oy
                elif tactic == 7: tx, ty = pp[0]+pd[0]*300*SCALE, pp[1]+pd[1]*300*SCALE
                elif tactic == 8:
                    jerk = (name_hash%200)-100; perp = (-pd[1], pd[0])
                    bt = (pp[0]+pd[0]*base_ahead, pp[1]+pd[1]*base_ahead); tx, ty = bt[0]+perp[0]*jerk, bt[1]+perp[1]*jerk
                else: tx, ty = pp[0]+pd[0]*base_ahead, pp[1]+pd[1]*base_ahead
                dx, dy = tx-head[0], ty-head[1]; length = math.hypot(dx, dy)
                if length > 1e-6:
                    dd = (dx/length, dy/length)
                    if will_collide_with_player(head, dd, radius): return get_evade_direction(head, all_segs, old_dir, radius)
                    if direction_will_collide(head, dd, all_segs, radius):
                        best, best_dot = None, -float('inf')
                        for ao in [-1.2,-0.9,-0.6,-0.3,0.3,0.6,0.9,1.2]:
                            ca, sa = math.cos(ao), math.sin(ao)
                            test = (dd[0]*ca - dd[1]*sa, dd[0]*sa + dd[1]*ca)
                            if test[0]==-old_dir[0] and test[1]==-old_dir[1]: continue
                            if not direction_will_collide(head, test, all_segs, radius):
                                dot = test[0]*dd[0] + test[1]*dd[1]
                                if dot > best_dot: best_dot, best = dot, test
                        if best: return best
                    else:
                        if not (dd[0]==-old_dir[0] and dd[1]==-old_dir[1]): return dd

    elif game_mode == "mojin":
        target = None
        min_dist = 400 * SCALE
        if math.hypot(head[0]-snake[0][0], head[1]-snake[0][1]) < min_dist:
            target = ("player", snake[0]); min_dist = math.hypot(head[0]-snake[0][0], head[1]-snake[0][1])
        for other in enemies:
            if other is enemy: continue
            d = math.hypot(head[0]-other['body'][0][0], head[1]-other['body'][0][1])
            if d < min_dist: target = ("enemy", other['body'][0]); min_dist = d
        if target:
            tx, ty = target[1]
            dx, dy = tx-head[0], ty-head[1]; length = math.hypot(dx, dy)
            if length > 0:
                desired = (dx/length, dy/length)
                if not direction_will_collide(head, desired, all_segs, radius): return desired

    if foods_list and random.random() < ENEMY_FOOD_SEEK_PROB:
        tf, md = None, float('inf')
        for fx, fy, _, _ in foods_list:
            dsq = (head[0]-fx)**2+(head[1]-fy)**2
            if dsq < md: tf, md = (fx, fy), dsq
        if tf:
            dx, dy = tf[0]-head[0], tf[1]-head[1]; length = math.hypot(dx, dy)
            if length > 1e-6:
                nd = (dx/length, dy/length)
                if not (nd[0]==-old_dir[0] and nd[1]==-old_dir[1]): return nd
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

def draw_dropdown_menu(option_rect, items, current_index, menu_type):
    global dropdown_rects, resolution_scroll, display_scroll, theme_scroll, scrolling, scroll_target, scroll_info
    font = get_font(20)
    item_height = int(38 * SCALE)
    width, x, y = option_rect.width, option_rect.left, option_rect.bottom + 4
    total_items = len(items)
    max_visible = VISIBLE_ITEMS
    if total_items <= max_visible:
        visible_count, scroll_offset = total_items, 0
    else:
        visible_count = max_visible
        if menu_type == "res": scroll_offset = max(0, min(resolution_scroll, total_items - max_visible))
        elif menu_type == "disp": scroll_offset = max(0, min(display_scroll, total_items - max_visible))
        else: scroll_offset = max(0, min(theme_scroll, total_items - max_visible))
    menu_height = item_height * visible_count + 4
    menu_rect = pygame.Rect(x, y, width, menu_height)
    draw_rounded_rect(screen, menu_rect.inflate(8, 8), MENU_BORDER, radius=12, shadow=True)
    draw_rounded_rect(screen, menu_rect, MENU_BG, radius=10)
    rects = []
    for i in range(visible_count):
        actual_index = i + scroll_offset
        if actual_index >= total_items: break
        item_rect = pygame.Rect(x + 2, y + 2 + i * item_height, width - 20, item_height)
        rects.append((actual_index, item_rect))
        if item_rect.collidepoint(mouse_x, mouse_y):
            draw_rounded_rect(screen, item_rect.inflate(-2, -2), MENU_HOVER, radius=6)
            pygame.draw.rect(screen, MENU_HOVER_BORDER, item_rect.inflate(-2, -2), 2, border_radius=6)
        text_surf = font.render(items[actual_index], True, BLACK)
        screen.blit(text_surf, (item_rect.x + 12, item_rect.centery - text_surf.get_height() // 2))
        if actual_index == current_index:
            check_font = get_font(24)
            check_surf = check_font.render("✓", True, MENU_CHECK)
            screen.blit(check_surf, (item_rect.right - check_surf.get_width() - 15, item_rect.centery - check_surf.get_height() // 2))
    if total_items > max_visible:
        scroll_bar_x, scroll_bar_y = x + width - 12, y + 2
        scroll_bar_height = menu_height - 4
        pygame.draw.rect(screen, SCROLL_BAR_BG, (scroll_bar_x, scroll_bar_y, 8, scroll_bar_height), border_radius=4)
        thumb_height = max(20, scroll_bar_height * max_visible / total_items)
        thumb_y = scroll_bar_y + (scroll_offset / (total_items - max_visible)) * (scroll_bar_height - thumb_height)
        thumb_rect = pygame.Rect(scroll_bar_x, thumb_y, 8, thumb_height)
        thumb_color = SCROLL_THUMB_HOVER if thumb_rect.collidepoint(mouse_x, mouse_y) else SCROLL_THUMB
        pygame.draw.rect(screen, thumb_color, thumb_rect, border_radius=4)
        scroll_info[menu_type] = {'bar_rect': pygame.Rect(scroll_bar_x, scroll_bar_y, 8, scroll_bar_height),
                                  'thumb_rect': thumb_rect, 'total': total_items, 'max_visible': max_visible}
    else:
        if menu_type in scroll_info: del scroll_info[menu_type]
    dropdown_rects = [(menu_type, idx, r) for idx, r in rects]

def draw_mojin_lobby():
    screen.fill(UI_BG)
    font_nav = get_font(24)
    nav_rects = []
    nav_texts = ["主页", "大厅", "仓库"]
    for i, txt in enumerate(nav_texts):
        rect = pygame.Rect(50 + i*120*SCALE, 10*SCALE, 100*SCALE, 36*SCALE)
        nav_rects.append(rect)
        is_hov = rect.collidepoint(mouse_x, mouse_y)
        draw_option_rect(screen, rect, txt, font_nav, is_hovered=is_hov)
    if mojin_map_selection:
        title = get_font(36).render("选择地图", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
        for i, name in enumerate(MAP_NAMES):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 150*SCALE, 200*SCALE + i*80*SCALE, 300*SCALE, 50*SCALE)
            is_sel = (i == SELECTED_MAP_INDEX)
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, name, get_font(28), is_selected=is_sel, is_hovered=is_hov)
        start_rect = pygame.Rect(SCREEN_WIDTH//2 - 100*SCALE, 450*SCALE, 200*SCALE, 50*SCALE)
        draw_option_rect(screen, start_rect, "开始游戏", get_font(28), is_hovered=start_rect.collidepoint(mouse_x, mouse_y))
        return nav_rects, start_rect
    elif mojin_warehouse:
        title = get_font(36).render("仓库", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
        y = 180*SCALE
        for item, count in warehouse_data.items():
            txt = f"{item}: {count}"
            screen.blit(get_font(24).render(txt, True, BLACK), (SCREEN_WIDTH//2 - 150*SCALE, y))
            y += 40*SCALE
        return nav_rects, None
    else:
        title = get_font(36).render("搜打撤大厅", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100*SCALE))
        return nav_rects, None

def draw_mojin_game():
    draw_background()
    for ox, oy, orad in obstacles: draw_circle(ox, oy, BROWN, orad)
    for sp in mojin_supply_points:
        draw_circle(sp[0], sp[1], YELLOW, 10*SCALE)
    for ep in EVAC_POINTS:
        draw_circle(ep[0], ep[1], GREEN, EVAC_RADIUS)
    head_c = HEAD_COLOR_OPTIONS[head_color_index]; body_c = BODY_COLOR_OPTIONS[body_color_index]
    cr = get_segment_radius()
    for i, (x,y) in enumerate(snake): draw_circle(x, y, head_c if i==0 else body_c, cr)
    for enemy in enemies:
        for i, (x,y) in enumerate(enemy['body']): draw_circle(x, y, RED if i==0 else DARK_RED, cr)
    for fx, fy, fc, fr in foods: draw_circle(fx, fy, fc, fr)
    font = get_font(18)
    elapsed = time.time() - mojin_game_start_time
    remaining = max(0, 1800 - elapsed)
    mins, secs = divmod(int(remaining), 60)
    timer_text = f"{mins:02d}:{secs:02d}"
    screen.blit(font.render(timer_text, True, BLACK), (20*SCALE, 20*SCALE))
    minimap_w, minimap_h = 150*SCALE, 150*SCALE
    minimap_surf = pygame.Surface((minimap_w, minimap_h), pygame.SRCALPHA)
    minimap_surf.fill((255,255,255,150))
    px = int((snake[0][0] - WORLD_MIN_X) / WORLD_WIDTH * minimap_w)
    py = int((snake[0][1] - WORLD_MIN_Y) / WORLD_HEIGHT * minimap_h)
    pygame.draw.circle(minimap_surf, RED, (px, py), 3)
    for ep in EVAC_POINTS:
        epx = int((ep[0] - WORLD_MIN_X) / WORLD_WIDTH * minimap_w)
        epy = int((ep[1] - WORLD_MIN_Y) / WORLD_HEIGHT * minimap_h)
        pygame.draw.circle(minimap_surf, GREEN, (epx, epy), 4)
    screen.blit(minimap_surf, (20*SCALE, 60*SCALE))
    if mojin_near_supply:
        txt = font.render("按F搜索", True, BLACK)
        screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT - 100*SCALE))
    if mojin_game_result:
        result_font = get_font(72)
        text = result_font.render(mojin_game_result, True, RED)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 50*SCALE))
    if mojin_evac_active and not mojin_game_result:
        evac_text = font.render(f"撤离中... {max(0, int(EVAC_TIME - mojin_evac_timer))}秒", True, BLACK)
        screen.blit(evac_text, (SCREEN_WIDTH//2 - evac_text.get_width()//2, SCREEN_HEIGHT//2 + 50*SCALE))

def draw_backpack():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((128,128,128,200))
    screen.blit(overlay, (0,0))
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
    waiting = True
    while waiting:
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
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: waiting = False
                elif event.key == pygame.K_UP: scroll_off = max(0, scroll_off-1)
                elif event.key == pygame.K_DOWN: scroll_off = min(total_lines - max_vis, scroll_off+1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos): waiting = False
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
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(event.pos): waiting = False
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
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN): waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(event.pos): waiting = False
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
    global setting_option_rects, back_button_hover, mode_hover, dropdown_rects

    if game_mode == "mojin" and not game_started:
        nav_rects, start_rect = draw_mojin_lobby()
        back_text = get_font(24).render("返回", True, BLACK)
        back_rect = back_text.get_rect(topleft=(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20))
        screen.blit(back_text, back_rect)
        pygame.display.flip()
        return

    if game_mode == "mojin" and mojin_ingame:
        draw_mojin_game()
        if mojin_backpack_open:
            draw_backpack()
        pygame.display.flip()
        return

    if graphics_settings_mode:
        screen.fill(UI_BG)
        font_big, font_opt, font_small = get_font(36), get_font(24), get_font(16)
        title = font_big.render("画面设置", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, int(150 * SCALE)))
        back_text = font_opt.render("返回", True, DARK_GRAY if back_button_hover else BLACK)
        back_rect = back_text.get_rect(topleft=(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20))
        screen.blit(back_text, back_rect)
        y = int(270 * SCALE)
        res_text = f"画面分辨率: {RESOLUTIONS[current_resolution_index][0]} × {RESOLUTIONS[current_resolution_index][1]}"
        res_rendered = font_opt.render(res_text, True, BLACK)
        res_rect = res_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - res_rendered.get_width()//2, y))
        if graphics_selected == 0: draw_rounded_rect(screen, res_rect.inflate(20,12), MENU_HOVER, radius=8)
        screen.blit(res_rendered, (res_rect.x, res_rect.y))
        y += int(80 * SCALE)
        disp_text = f"显示方式: {DISPLAY_MODES[current_display_mode_index][0]}"
        disp_rendered = font_opt.render(disp_text, True, BLACK)
        disp_rect = disp_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - disp_rendered.get_width()//2, y))
        if graphics_selected == 1: draw_rounded_rect(screen, disp_rect.inflate(20,12), MENU_HOVER, radius=8)
        screen.blit(disp_rendered, (disp_rect.x, disp_rect.y))
        y += int(80 * SCALE)
        theme_text = f"界面主题: {UI_THEMES[ui_theme_index][0]}"
        theme_rendered = font_opt.render(theme_text, True, BLACK)
        theme_rect = theme_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - theme_rendered.get_width()//2, y))
        if graphics_selected == 2: draw_rounded_rect(screen, theme_rect.inflate(20,12), MENU_HOVER, radius=8)
        screen.blit(theme_rendered, (theme_rect.x, theme_rect.y))
        dropdown_rects = []
        if resolution_dropdown:
            items = [f"{w} × {h}" for w, h in RESOLUTIONS]
            draw_dropdown_menu(res_rect, items, current_resolution_index, "res")
        if display_dropdown:
            items = [name for name, _ in DISPLAY_MODES]
            draw_dropdown_menu(disp_rect, items, current_display_mode_index, "disp")
        if theme_dropdown:
            items = [name for name, _ in UI_THEMES]
            draw_dropdown_menu(theme_rect, items, ui_theme_index, "theme")
        hint = font_small.render("点击选项展开下拉菜单，↑↓选择，回车确认，ESC返回", True, BLACK)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
        pygame.display.flip()
        return

    if settings_mode:
        screen.fill(UI_BG)
        back_font = get_font(24); back_text_color = DARK_GRAY if back_button_hover else BLACK
        back_text = back_font.render("返回", True, back_text_color)
        text_rect = back_text.get_rect(center=(BACK_BUTTON_POS[0]+50, BACK_BUTTON_POS[1]+20))
        screen.blit(back_text, text_rect)
        font_big = get_font(36); title = font_big.render("设置", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, int(150*SCALE)))
        items = [
            f"背景样式: {BACKGROUND_STYLE_OPTIONS[background_style]}",
            f"蛇头颜色: {HEAD_COLOR_NAMES[head_color_index]}",
            f"蛇身颜色: {BODY_COLOR_NAMES[body_color_index]}",
            "画面设置", "查看更新日志", "开发者名单"
        ]
        y = int(250*SCALE); setting_option_rects = []
        for i, text in enumerate(items):
            display_text = ">> " + text + " <<" if i == selected_setting else text
            font = get_font(24)
            rend = font.render(display_text, True, BLACK)
            rect = rend.get_rect(center=(SCREEN_WIDTH//2, y))
            setting_option_rects.append(rect)
            is_sel = i == selected_setting
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            if is_hov:
                draw_rounded_rect(screen, rect.inflate(20,12), MENU_HOVER, radius=8)
                pygame.draw.rect(screen, MENU_HOVER_BORDER, rect.inflate(20,12), 2, border_radius=8)
            elif is_sel:
                draw_rounded_rect(screen, rect.inflate(20,12), MENU_HOVER, radius=8)
            screen.blit(rend, rect.topleft)
            y += int(60*SCALE)
        hit = get_font(16).render("↑↓选择  ←→更改  Enter保存  Esc取消  (鼠标点击切换前三个选项)", True, BLACK)
        screen.blit(hit, (SCREEN_WIDTH//2 - hit.get_width()//2, SCREEN_HEIGHT-100))
        pygame.display.flip()
        return

    if not game_started:
        screen.fill(UI_BG)
        font_title = get_font(48); title = font_title.render(f"自由贪吃蛇 {VERSION}", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, int(150*SCALE)))
        mode_font = get_font(24)
        if game_mode == "timed": mode_text, mode_color = "模式: 淘汰之王  (M键切换)", YELLOW
        elif game_mode == "mojin": mode_text, mode_color = "模式: 搜打撤  (M键切换)", ORANGE
        else: mode_text, mode_color = "模式: 经典  (M键切换)", BLACK
        mode_rend = mode_font.render(mode_text, True, mode_color)
        # 修复悬停偏移：基于mode_rend尺寸精确计算矩形
        mode_rect = mode_rend.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + MODE_BUTTON_Y))
        mode_hover = mode_rect.collidepoint(mouse_x, mouse_y)
        if mode_hover:
            draw_rounded_rect(screen, mode_rect.inflate(20, 12), MENU_HOVER, radius=8)
            pygame.draw.rect(screen, MENU_HOVER_BORDER, mode_rect.inflate(20, 12), 2, border_radius=8)
        screen.blit(mode_rend, mode_rect.topleft)
        button_texts = ["开始游戏 (SPACE)", "设置 (S)", "退出 (Q)"]
        button_fonts = [get_font(24), get_font(18), get_font(18)]
        for i, (y_btn, text) in enumerate(zip(BUTTON_Y_POS, button_texts)):
            screen_y = SCREEN_HEIGHT//2 + y_btn
            text_rend = button_fonts[i].render(text, True, BLACK)
            # 同样基于文本尺寸计算按钮矩形，消除偏移
            btn_rect = text_rend.get_rect(center=(SCREEN_WIDTH//2, screen_y))
            is_hov = btn_rect.inflate(20, 12).collidepoint(mouse_x, mouse_y) or hover_button == i
            if is_hov:
                draw_rounded_rect(screen, btn_rect.inflate(20, 12), MENU_HOVER, radius=8)
                pygame.draw.rect(screen, MENU_HOVER_BORDER, btn_rect.inflate(20, 12), 2, border_radius=8)
            screen.blit(text_rend, btn_rect.topleft)
        hint = get_font(18).render("按 H 查看历史排行榜", True, DARK_GRAY)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 80))
        pygame.display.flip()
        return

    # 经典/淘汰之王游戏内
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
    left, bottom = world_to_screen(WORLD_MIN_X+cr, WORLD_MIN_Y+cr)
    right, top = world_to_screen(WORLD_MAX_X-cr, WORLD_MAX_Y-cr)
    pygame.draw.rect(screen, RED, (left, bottom, right-left, top-bottom), 2)
    txt_col = WHITE if BACKGROUND_STYLE_VALUES[background_style]==BLACK else BLACK
    fi, fs = get_font(16), get_font(12)
    screen.blit(fi.render(f"Score: {score}", True, txt_col), (SCREEN_WIDTH-int(200*SCALE), int(30*SCALE)))
    spd = get_current_speed(); spd_text = f"Speed: {spd:.1f}"
    if boosting and (time.time()-boost_start_time) < BOOST_DURATION: spd_text += f" (Boost: {BOOST_DURATION-(time.time()-boost_start_time):.1f}s)"
    if temp_boost_remaining>0: spd_text += f" (Temp Boost: {temp_boost_remaining//60}s)"
    screen.blit(fs.render(spd_text, True, txt_col), (int(20*SCALE), int(30*SCALE)))
    screen.blit(fs.render("长按Ctrl加速(5s限时)", True, txt_col), (int(20*SCALE), int(50*SCALE)))
    max_en = TIMED_ENEMY_COUNT if game_mode=="timed" else ENEMY_COUNT
    screen.blit(fs.render(f"敌人: {len(enemies)}/{max_en}", True, txt_col), (int(20*SCALE), int(70*SCALE)))
    if game_mode=="timed":
        high_cnt = sum(1 for e in enemies if e['score']>=20)
        rc = RED if high_cnt>attack_trigger_count else txt_col
        screen.blit(fs.render(f"狂暴敌人: {high_cnt}/{attack_trigger_count}", True, rc), (int(20*SCALE), int(90*SCALE)))
    if show_fps: screen.blit(fs.render(f"FPS: {int(clock.get_fps())}", True, txt_col), (SCREEN_WIDTH-int(100*SCALE), SCREEN_HEIGHT-int(30*SCALE)))
    screen.blit(fs.render(VERSION, True, txt_col), (SCREEN_WIDTH-int(150*SCALE), SCREEN_HEIGHT-int(60*SCALE)))

    if not game_active:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((128,128,128,200))
        screen.blit(overlay, (0,0))
        gof = get_font(48); screen.blit(gof.render("游戏结束", True, WHITE), (SCREEN_WIDTH//2 - 100, 200*SCALE))
        oy = int(400*SCALE)
        for i, opt in enumerate(GAMEOVER_OPTIONS):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
            is_sel = i == gameover_selection
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, opt if not is_sel else "▶ " + opt + " ◀", get_font(36), is_selected=is_sel, is_hovered=is_hov, base_color=WHITE)
    if paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,128))
        screen.blit(overlay, (0,0))
        pf = get_font(48); screen.blit(pf.render("暂停", True, WHITE), (SCREEN_WIDTH//2 - pf.size("暂停")[0]//2, 200*SCALE))
        oy = int(350*SCALE)
        for i, opt in enumerate(PAUSE_OPTIONS):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
            is_sel = i == pause_selection
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, opt if not is_sel else "▶ " + opt + " ◀", get_font(36), is_selected=is_sel, is_hovered=is_hov, base_color=WHITE)
    pygame.display.flip()

def restart_game():
    global snake, direction, foods, score, game_active, boosting, color_centers, enemies, gameover_killer_name, global_attack_phase, MOJIN_PHASE, MOJIN_TIMER, temp_boost_remaining, obstacles, containers
    snake = [(0,0), (-16*SCALE,0), (-32*SCALE,0), (-48*SCALE,0), (-64*SCALE,0)]; direction = (1,0); score = 0
    game_active = True; boosting = False; color_centers.clear(); enemies = []
    gameover_killer_name = None; global_attack_phase = False; MOJIN_PHASE = "search"; MOJIN_TIMER = 0; temp_boost_remaining = 0
    generate_foods(FOOD_COUNT)
    ec = TIMED_ENEMY_COUNT if game_mode=="timed" else ENEMY_COUNT
    min_dist_sq = (get_segment_radius()*4)**2
    for _ in range(ec):
        placed = False
        for _ in range(500):
            x = random.randint(WORLD_MIN_X+int(100*SCALE), WORLD_MAX_X-int(100*SCALE))
            y = random.randint(WORLD_MIN_Y+int(100*SCALE), WORLD_MAX_Y-int(100*SCALE))
            if any((x-sx)**2+(y-sy)**2 < min_dist_sq for sx,sy in snake): continue
            o = False
            for enemy in enemies:
                if any((x-sx)**2+(y-sy)**2 < min_dist_sq for sx,sy in enemy['body']): o = True; break
            if o: continue
            body = [(x,y), (x-16*SCALE,y), (x-32*SCALE,y)]
            dir_ = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
            name = random.choice(ENEMY_NAMES) if game_mode=="timed" else "Enemy"
            enemies.append({'body':body,'dir':dir_,'score':0,'name':name,'state':'idle'}); placed = True; break
        if not placed:
            x = random.randint(WORLD_MIN_X+int(100*SCALE), WORLD_MAX_X-int(100*SCALE))
            y = random.randint(WORLD_MIN_Y+int(100*SCALE), WORLD_MAX_Y-int(100*SCALE))
            body = [(x,y),(x-16*SCALE,y),(x-32*SCALE,y)]
            enemies.append({'body':body,'dir':random.choice([(1,0),(-1,0),(0,1),(0,-1)]),'score':0,'name':random.choice(ENEMY_NAMES) if game_mode=="timed" else "Enemy",'state':'idle'})
    if game_mode=="mojin": generate_obstacles_and_containers()
    else: obstacles.clear(); containers.clear()

def new_game(): restart_game()
def restart():
    global game_started, settings_mode, gameover_screen, paused
    new_game(); game_started = False; settings_mode = False; gameover_screen = False; paused = False
def start_game():
    global game_started
    if not game_started and not settings_mode: new_game(); game_started = True
def settings_up(): global selected_setting; selected_setting = (selected_setting-1)%6 if settings_mode else None
def settings_down(): global selected_setting; selected_setting = (selected_setting+1)%6 if settings_mode else None
def settings_left():
    global background_style, head_color_index, body_color_index
    if settings_mode:
        if selected_setting==0: background_style = (background_style-1)%len(BACKGROUND_STYLE_OPTIONS)
        elif selected_setting==1: head_color_index = (head_color_index-1)%len(HEAD_COLOR_OPTIONS)
        elif selected_setting==2: body_color_index = (body_color_index-1)%len(BODY_COLOR_OPTIONS)
def settings_right():
    global background_style, head_color_index, body_color_index
    if settings_mode:
        if selected_setting==0: background_style = (background_style+1)%len(BACKGROUND_STYLE_OPTIONS)
        elif selected_setting==1: head_color_index = (head_color_index+1)%len(HEAD_COLOR_OPTIONS)
        elif selected_setting==2: body_color_index = (body_color_index+1)%len(BODY_COLOR_OPTIONS)
def settings_save(): global settings_mode; settings_mode = False
def settings_cancel():
    global settings_mode, background_style, head_color_index, body_color_index
    background_style = DEFAULT_BACKGROUND_STYLE; head_color_index = HEAD_COLOR_OPTIONS.index(DEFAULT_HEAD_COLOR); body_color_index = BODY_COLOR_OPTIONS.index(DEFAULT_BODY_COLOR)
    settings_mode = False
def enter_settings():
    global settings_mode, selected_setting
    if not game_started and not settings_mode: settings_mode = True; selected_setting = 0
def quit_game(): pygame.quit(); exit()

# ==================== 主循环 ====================
need_show, last_ver = check_version()
if need_show: show_changelog(); write_version()

if player_name == "玩家" and not os.path.exists(NAME_FILE):
    player_name = show_name_input_screen()
    save_player_name(player_name)

new_game()
last_time = time.time()
running = True
gameover_killer_name = None
global_attack_phase = False
MOJIN_PHASE = "search"
MOJIN_TIMER = 0
temp_boost_remaining = 0

while running:
    dt = time.time() - last_time; last_time = time.time()
    if temp_boost_remaining > 0: temp_boost_remaining -= 1
    if game_started and game_active and not paused and not gameover_screen and not (game_mode == "mojin" and mojin_ingame):
        player_pos_history.append(snake[0]); player_dir_history.append(direction)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            if scrolling and scroll_target and scroll_target in scroll_info:
                info = scroll_info[scroll_target]; bar = info['bar_rect']
                thumb_h = info['thumb_rect'].height; total = info['total']; visible = info['max_visible']
                if bar.height > thumb_h:
                    ratio = (mouse_y - bar.top - thumb_h/2) / (bar.height - thumb_h)
                    new_off = max(0, min(int(ratio*(total-visible)+0.5), total-visible))
                    if scroll_target == "res": resolution_scroll = new_off
                    elif scroll_target == "disp": display_scroll = new_off
                    elif scroll_target == "theme": theme_scroll = new_off
            if graphics_settings_mode:
                back_font = get_font(24); back_text = back_font.render("返回", True, BLACK)
                back_rect = back_text.get_rect(topleft=(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20))
                back_button_hover = back_rect.collidepoint(mouse_x, mouse_y)
            elif settings_mode:
                for i, rect in enumerate(setting_option_rects):
                    if rect.collidepoint(mouse_x, mouse_y): selected_setting = i; break
                back_text = get_font(24).render("返回", True, BLACK)
                text_rect = back_text.get_rect(center=(BACK_BUTTON_POS[0]+50, BACK_BUTTON_POS[1]+20))
                back_button_hover = text_rect.collidepoint(mouse_x, mouse_y)
            elif paused:
                oy = int(350*SCALE)
                for i in range(3):
                    rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
                    if rect.collidepoint(mouse_x, mouse_y): pause_selection = i; break
            elif gameover_screen:
                oy = int(400*SCALE)
                for i in range(2):
                    rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
                    if rect.collidepoint(mouse_x, mouse_y): gameover_selection = i; break
            elif not game_started:
                hover_button = None
                for i, y_center in enumerate(BUTTON_Y_POS):
                    screen_y = SCREEN_HEIGHT//2 + y_center
                    btn_font = get_font(24) if i==0 else get_font(18)
                    text_rend = btn_font.render(["开始游戏 (SPACE)", "设置 (S)", "退出 (Q)"][i], True, BLACK)
                    btn_rect = text_rend.get_rect(center=(SCREEN_WIDTH//2, screen_y))
                    if btn_rect.inflate(20,12).collidepoint(mouse_x, mouse_y): hover_button = i; break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if graphics_settings_mode: graphics_settings_mode = False; resolution_dropdown = display_dropdown = theme_dropdown = False
                elif settings_mode: settings_cancel()
                elif game_mode == "mojin" and mojin_lobby: game_started = False; game_mode = "classic"; mojin_lobby = False
                elif mojin_ingame and not mojin_game_result: paused = not paused
                elif not game_started: pass
                else: paused = not paused
            if graphics_settings_mode:
                if event.key == pygame.K_UP: graphics_selected = (graphics_selected-1)%3; resolution_dropdown = display_dropdown = theme_dropdown = False
                elif event.key == pygame.K_DOWN: graphics_selected = (graphics_selected+1)%3; resolution_dropdown = display_dropdown = theme_dropdown = False
                elif event.key == pygame.K_LEFT:
                    if graphics_selected==0: current_resolution_index = (current_resolution_index-1)%len(RESOLUTIONS); apply_display_settings()
                    elif graphics_selected==1: current_display_mode_index = (current_display_mode_index-1)%len(DISPLAY_MODES); apply_display_settings()
                    elif graphics_selected==2: ui_theme_index = (ui_theme_index-1)%len(UI_THEMES); UI_BG = UI_THEMES[ui_theme_index][1]
                elif event.key == pygame.K_RIGHT:
                    if graphics_selected==0: current_resolution_index = (current_resolution_index+1)%len(RESOLUTIONS); apply_display_settings()
                    elif graphics_selected==1: current_display_mode_index = (current_display_mode_index+1)%len(DISPLAY_MODES); apply_display_settings()
                    elif graphics_selected==2: ui_theme_index = (ui_theme_index+1)%len(UI_THEMES); UI_BG = UI_THEMES[ui_theme_index][1]
                elif event.key == pygame.K_RETURN:
                    if graphics_selected==0: resolution_dropdown = not resolution_dropdown; display_dropdown = theme_dropdown = False
                    elif graphics_selected==1: display_dropdown = not display_dropdown; resolution_dropdown = theme_dropdown = False
                    else: theme_dropdown = not theme_dropdown; resolution_dropdown = display_dropdown = False
                continue
            if settings_mode:
                if event.key == pygame.K_UP: settings_up()
                elif event.key == pygame.K_DOWN: settings_down()
                elif event.key == pygame.K_LEFT: settings_left()
                elif event.key == pygame.K_RIGHT: settings_right()
                elif event.key == pygame.K_RETURN:
                    if selected_setting == 3: graphics_settings_mode = True; graphics_selected = 0
                    elif selected_setting == 4: show_full_changelog()
                    elif selected_setting == 5: show_credits()
                    else: settings_save()
                continue
            if paused:
                if event.key == pygame.K_UP: pause_selection = (pause_selection-1)%3
                elif event.key == pygame.K_DOWN: pause_selection = (pause_selection+1)%3
                elif event.key == pygame.K_RETURN:
                    if pause_selection == 0: restart_game(); paused = False
                    elif pause_selection == 1: game_started = False; settings_mode = False; paused = False
                    elif pause_selection == 2: quit_game()
                continue
            if gameover_screen:
                if event.key == pygame.K_UP: gameover_selection = (gameover_selection-1)%2
                elif event.key == pygame.K_DOWN: gameover_selection = (gameover_selection+1)%2
                elif event.key == pygame.K_RETURN:
                    if gameover_selection == 0: restart_game(); gameover_screen = False
                    elif gameover_selection == 1: game_started = False; settings_mode = False; gameover_screen = False
                elif event.key == pygame.K_h and game_mode == "timed": show_rankings()
                continue
            if not game_started:
                if event.key == pygame.K_SPACE: start_game()
                elif event.key == pygame.K_s: enter_settings()
                elif event.key == pygame.K_q: quit_game()
                elif event.key == pygame.K_m:
                    if game_mode == "classic": game_mode = "timed"
                    elif game_mode == "timed": game_mode = "mojin"
                    else: game_mode = "classic"
                    if game_mode == "mojin": generate_obstacles_and_containers()
                    else: obstacles.clear(); containers.clear()
                elif event.key == pygame.K_h: show_rankings()
            if game_started and game_mode != "mojin" and not paused and not gameover_screen:
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL): boosting = True; boost_start_time = time.time()
                elif event.key == pygame.K_r: restart_game()
            # 搜打撤移动控制：持续移动基于当前方向
            if mojin_ingame and not mojin_game_result and not paused:
                if event.key == pygame.K_w: direction = (0, -1)
                elif event.key == pygame.K_s: direction = (0, 1)
                elif event.key == pygame.K_a: direction = (-1, 0)
                elif event.key == pygame.K_d: direction = (1, 0)
                elif event.key == pygame.K_f:
                    if mojin_near_supply: mojin_backpack_open = True
                elif event.key == pygame.K_f and mojin_backpack_open:
                    mojin_backpack_open = False
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LCTRL, pygame.K_RCTRL): boosting = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 下拉菜单穿透防护：如果在任何下拉菜单内点击，只处理菜单，阻止事件继续传播
            dropdown_clicked = False
            for dtype, idx, rect in dropdown_rects:
                if rect.collidepoint(mouse_x, mouse_y):
                    dropdown_clicked = True
                    if dtype == "res": current_resolution_index = idx
                    elif dtype == "disp": current_display_mode_index = idx
                    elif dtype == "theme": ui_theme_index = idx; UI_BG = UI_THEMES[idx][1]
                    apply_display_settings()
                    resolution_dropdown = display_dropdown = theme_dropdown = False
                    break
            if dropdown_clicked: continue  # 穿透保护

            if graphics_settings_mode:
                back_font = get_font(24); back_text = back_font.render("返回", True, BLACK)
                back_rect = back_text.get_rect(topleft=(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20))
                if back_rect.collidepoint(mouse_x, mouse_y): graphics_settings_mode = False; resolution_dropdown = display_dropdown = theme_dropdown = False; continue
                res_rendered = get_font(24).render(f"画面分辨率: {RESOLUTIONS[current_resolution_index][0]} × {RESOLUTIONS[current_resolution_index][1]}", True, BLACK)
                res_rect = res_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - res_rendered.get_width()//2, int(270*SCALE)))
                disp_rendered = get_font(24).render(f"显示方式: {DISPLAY_MODES[current_display_mode_index][0]}", True, BLACK)
                disp_rect = disp_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - disp_rendered.get_width()//2, int(350*SCALE)))
                theme_rendered = get_font(24).render(f"界面主题: {UI_THEMES[ui_theme_index][0]}", True, BLACK)
                theme_rect = theme_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - theme_rendered.get_width()//2, int(430*SCALE)))
                if res_rect.collidepoint(mouse_x, mouse_y): graphics_selected = 0; resolution_dropdown = not resolution_dropdown; display_dropdown = theme_dropdown = False
                elif disp_rect.collidepoint(mouse_x, mouse_y): graphics_selected = 1; display_dropdown = not display_dropdown; resolution_dropdown = theme_dropdown = False
                elif theme_rect.collidepoint(mouse_x, mouse_y): graphics_selected = 2; theme_dropdown = not theme_dropdown; resolution_dropdown = display_dropdown = False
                else:
                    for menu_type, info in scroll_info.items():
                        if info['thumb_rect'].collidepoint(mouse_x, mouse_y): scrolling = True; scroll_target = menu_type; break
                continue
            if settings_mode:
                back_font = get_font(24); back_text = back_font.render("返回", True, BLACK)
                text_rect = back_text.get_rect(center=(BACK_BUTTON_POS[0]+50, BACK_BUTTON_POS[1]+20))
                if text_rect.collidepoint(mouse_x, mouse_y): settings_cancel(); continue
                for i, rect in enumerate(setting_option_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        if i == 3: graphics_settings_mode = True; graphics_selected = 0
                        elif i == 4: show_full_changelog()
                        elif i == 5: show_credits()
                        else: selected_setting = i; settings_right()
                        break
                continue
            if paused:
                oy = int(350*SCALE)
                for i in range(3):
                    rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
                    if rect.collidepoint(mouse_x, mouse_y):
                        if i == 0: restart_game(); paused = False
                        elif i == 1: game_started = False; settings_mode = False; paused = False
                        elif i == 2: quit_game()
                        break
                continue
            if gameover_screen:
                oy = int(400*SCALE)
                for i in range(2):
                    rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
                    if rect.collidepoint(mouse_x, mouse_y):
                        if i == 0: restart_game(); gameover_screen = False
                        elif i == 1: game_started = False; settings_mode = False; gameover_screen = False
                        break
                continue
            if game_mode == "mojin" and not game_started and not mojin_ingame:
                mx, my = pygame.mouse.get_pos()
                nav_rects, start_rect = draw_mojin_lobby()
                back_rect = pygame.Rect(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20, 60*SCALE, 30*SCALE)
                if back_rect.collidepoint(mx, my): game_started = False; game_mode = "classic"; mojin_lobby = False
                for i, rect in enumerate(nav_rects):
                    if rect.collidepoint(mx, my):
                        if i == 0: mojin_lobby = False; game_started = False; game_mode = "classic"
                        elif i == 1: mojin_map_selection = True; mojin_warehouse = False
                        elif i == 2: mojin_warehouse = True; mojin_map_selection = False
                if start_rect and start_rect.collidepoint(mx, my) and mojin_map_selection:
                    mojin_ingame = True; game_started = True
                    mojin_game_start_time = time.time()
                    snake = [(0,0), (-16*SCALE,0), (-32*SCALE,0)]
                    enemies = []; foods = []; mojin_supply_points = []
                    for _ in range(20):
                        x, y = random_position()
                        supplies = [t[0] for t in SUPPLY_TYPES if random.random() < t[1]]
                        mojin_supply_points.append((x, y, supplies))
                    for _ in range(5):
                        x, y = random_position()
                        enemies.append({'body': [(x,y)], 'dir': (1,0), 'score':0, 'name':random.choice(ENEMY_NAMES)})
                    generate_obstacles_and_containers()
                    mojin_evac_active = False; mojin_evac_timer = 0; mojin_game_result = None
                continue
            if not game_started and game_mode != "mojin":
                mode_font = get_font(24)
                if game_mode == "timed": mode_text = "模式: 淘汰之王  (M键切换)"
                elif game_mode == "mojin": mode_text = "模式: 搜打撤  (M键切换)"
                else: mode_text = "模式: 经典  (M键切换)"
                mode_rend = mode_font.render(mode_text, True, BLACK)
                mode_rect = mode_rend.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + MODE_BUTTON_Y))
                if mode_rect.collidepoint(mouse_x, mouse_y):
                    if game_mode == "classic": game_mode = "timed"
                    elif game_mode == "timed": game_mode = "mojin"
                    else: game_mode = "classic"
                    if game_mode == "mojin": generate_obstacles_and_containers()
                    else: obstacles.clear(); containers.clear()
                    continue
                for i, y_center in enumerate(BUTTON_Y_POS):
                    screen_y = SCREEN_HEIGHT//2 + y_center
                    btn_font = get_font(24) if i == 0 else get_font(18)
                    text_rend = btn_font.render(["开始游戏 (SPACE)", "设置 (S)", "退出 (Q)"][i], True, BLACK)
                    btn_rect = text_rend.get_rect(center=(SCREEN_WIDTH//2, screen_y))
                    if btn_rect.inflate(20,12).collidepoint(mouse_x, mouse_y):
                        if i == 0: start_game()
                        elif i == 1: enter_settings()
                        elif i == 2: quit_game()
                        break
                continue
        elif event.type == pygame.MOUSEWHEEL:
            if graphics_settings_mode:
                if resolution_dropdown: resolution_scroll = max(0, min(resolution_scroll-event.y, len(RESOLUTIONS)-VISIBLE_ITEMS))
                if display_dropdown: display_scroll = max(0, min(display_scroll-event.y, len(DISPLAY_MODES)-VISIBLE_ITEMS))
                if theme_dropdown: theme_scroll = max(0, min(theme_scroll-event.y, len(UI_THEMES)-VISIBLE_ITEMS))
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: scrolling = False; scroll_target = None

    # 搜打撤游戏更新（持续移动）
    if mojin_ingame and not paused and not mojin_game_result:
        old_head = snake[0]
        new_head = (old_head[0] + direction[0]*BASE_SPEED, old_head[1] + direction[1]*BASE_SPEED)
        if not check_boundary(new_head): snake = [new_head] + snake[:-1]
        else: game_active = False; mojin_game_result = "撤离失败"
        mojin_near_supply = None
        for sp in mojin_supply_points:
            if math.hypot(snake[0][0]-sp[0], snake[0][1]-sp[1]) < 80*SCALE:
                mojin_near_supply = sp[2]; break
        for ep in EVAC_POINTS:
            if math.hypot(snake[0][0]-ep[0], snake[0][1]-ep[1]) < EVAC_RADIUS:
                if not mojin_evac_active: mojin_evac_active = True; mojin_evac_timer = 0
                mojin_evac_timer += dt
                if mojin_evac_timer >= EVAC_TIME: mojin_game_result = "撤离成功"
                break
        else: mojin_evac_active = False; mojin_evac_timer = 0
        if time.time() - mojin_game_start_time > 1800: mojin_game_result = "撤离失败"
        for enemy in enemies:
            nd = get_enemy_new_direction(enemy, foods)
            old = enemy['body'][0]
            new = (old[0] + nd[0]*BASE_SPEED, old[1] + nd[1]*BASE_SPEED)
            if not check_boundary(new): enemy['body'] = [new]
            else: enemies.remove(enemy)

    # 经典/淘汰之王模式游戏更新
    if game_started and not settings_mode and game_active and not paused and not gameover_screen and game_mode != "mojin":
        wx, wy = screen_to_world(mouse_x, mouse_y)
        hx, hy = snake[0]; dx, dy = wx - hx, wy - hy
        if abs(dx) > 1 or abs(dy) > 1: direction = (dx / math.hypot(dx, dy), dy / math.hypot(dx, dy))
        cs = get_current_speed(); cr = get_segment_radius()
        eat_th = (cr + FOOD_RADIUS)**2; large_th = (cr + LARGE_FOOD_RADIUS)**2; coll_th = (cr*2)**2
        old_head = snake[0]; new_head = (old_head[0] + direction[0]*cs, old_head[1] + direction[1]*cs)
        handle_container_collision(new_head)
        new_enemy_heads = []
        for enemy in enemies:
            oeh = enemy['body'][0]; es = get_base_speed()
            if game_mode=="timed" and enemy['score']>=20 and enemy.get('state')=='attacking': es *= 4.0
            elif game_mode=="mojin":
                if MOJIN_PHASE=="strike": es *= MOJIN_STRIKE_SPEED
                elif MOJIN_PHASE=="withdraw": es *= MOJIN_WITHDRAW_SPEED
                else: es *= MOJIN_SEARCH_SPEED
            nd = get_enemy_new_direction(enemy, foods); enemy['dir'] = nd
            neh = (oeh[0] + nd[0]*es, oeh[1] + nd[1]*es)
            new_enemy_heads.append((enemy, oeh, neh))
        if check_boundary(new_head):
            game_active = False; gameover_screen = True
            if game_mode=="timed" and score>0: add_score(player_name, score)
            draw(); continue
        surv = []
        for enemy, oh, nh in new_enemy_heads:
            if check_boundary(nh): spawn_foods_from_enemy(enemy['body']); enemies.remove(enemy)
            else: surv.append((enemy, oh, nh)); handle_container_collision(nh)
        ate = None
        for i, (fx, fy, _, fr) in enumerate(foods):
            th = large_th if fr==LARGE_FOOD_RADIUS else eat_th
            if (new_head[0]-fx)**2+(new_head[1]-fy)**2 < th: ate = i; break
            mx, my = (old_head[0]+new_head[0])/2, (old_head[1]+new_head[1])/2
            if (mx-fx)**2+(my-fy)**2 < th: ate = i; break
        if ate is not None: score += 1
        en_ate = []
        for enemy, oh, nh in surv:
            for i, (fx, fy, _, fr) in enumerate(foods):
                th = large_th if fr==LARGE_FOOD_RADIUS else eat_th
                if (nh[0]-fx)**2+(nh[1]-fy)**2 < th: en_ate.append((enemy, i)); enemy['score'] += 1; break
                mx, my = (oh[0]+nh[0])/2, (oh[1]+nh[1])/2
                if (mx-fx)**2+(my-fy)**2 < th: en_ate.append((enemy, i)); enemy['score'] += 1; break
        remove_set = {ate} if ate is not None else set()
        for e, i in en_ate: remove_set.add(i)
        snake.insert(0, new_head)
        if ate is None: snake.pop()
        for enemy, oh, nh in surv:
            enemy['body'].insert(0, nh)
            if not any(e is enemy for e, _ in en_ate): enemy['body'].pop()
        for i in sorted(remove_set, reverse=True): del foods[i]
        while len(foods) < FOOD_COUNT:
            nc = random.choice(FOOD_COLORS); nf = create_food(nc, FOOD_RADIUS)
            foods.append(nf if nf else (*random_position(), nc, FOOD_RADIUS))
        ph = snake[0]
        for enemy in enemies:
            for seg in enemy['body'][1:]:
                if (ph[0]-seg[0])**2+(ph[1]-seg[1])**2 < coll_th:
                    game_active = False; gameover_screen = True; gameover_killer_name = enemy['name']
                    if game_mode=="timed" and score>0: add_score(player_name, score)
                    break
            if not game_active: break
        to_remove = []
        for enemy in enemies:
            eh = enemy['body'][0]
            for seg in snake[1:]:
                if (eh[0]-seg[0])**2+(eh[1]-seg[1])**2 < coll_th: to_remove.append(enemy); break
            if enemy in to_remove: continue
            for other in enemies:
                if other is enemy: continue
                for seg in other['body'][1:]:
                    if (eh[0]-seg[0])**2+(eh[1]-seg[1])**2 < coll_th: to_remove.append(enemy); break
                if enemy in to_remove: break
        for e in to_remove:
            if e in enemies: spawn_foods_from_enemy(e['body']); enemies.remove(e)
        if game_mode=="classic" and len(enemies) < ENEMY_COUNT:
            md = (get_segment_radius()*4)**2
            for _ in range(5):
                if len(enemies) >= ENEMY_COUNT: break
                placed = False
                for _ in range(50):
                    x = random.randint(WORLD_MIN_X+int(100*SCALE), WORLD_MAX_X-int(100*SCALE))
                    y = random.randint(WORLD_MIN_Y+int(100*SCALE), WORLD_MAX_Y-int(100*SCALE))
                    if any((x-sx)**2+(y-sy)**2 < md for sx,sy in snake): continue
                    o = False
                    for enemy in enemies:
                        if any((x-sx)**2+(y-sy)**2 < md for sx,sy in enemy['body']): o = True; break
                    if o: continue
                    body = [(x,y),(x-16*SCALE,y),(x-32*SCALE,y)]
                    enemies.append({'body':body,'dir':random.choice([(1,0),(-1,0),(0,1),(0,-1)]),
                                    'score':0,'name':"Enemy",'state':'idle'}); placed = True; break
                if not placed: break
        if game_mode=="timed":
            hc = sum(1 for e in enemies if e['score']>=20)
            if global_attack_phase:
                if hc < attack_trigger_count*0.7: global_attack_phase = False; [e.update({'state':'idle'}) for e in enemies]
            else:
                if hc >= attack_trigger_count:
                    global_attack_phase = True; [e.update({'state':'preparing'}) for e in enemies if e['score']>=20]
            if global_attack_phase:
                prep = sum(1 for e in enemies if e.get('state')=='preparing')
                if prep > attack_trigger_count*0.8 and random.random()<0.02:
                    [e.update({'state':'attacking'}) for e in enemies if e.get('state')=='preparing']
        update_camera(snake[0][0], snake[0][1])

    draw()
    clock.tick(FPS)

pygame.quit()