import pygame
import random
import math
import os
import time
import json
import hashlib
from collections import deque

# ==================== 游戏版本 ====================
VERSION = "v5.2.1"
VERSION_FILE = os.path.join(os.path.expanduser("~"), ".snake_version_pygame")
NAME_FILE = os.path.join(os.path.dirname(__file__), "player_name.txt")
HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "timed_scores.json")
ACHIEVE_FILE = os.path.join(os.path.dirname(__file__), "achievements.json")

ALL_CHANGELOGS = [
    ("v5.2.1", [
        "敌方与友方AI增加绕前攻击，拦截蛇头移动",
        "团队模式共享分数，队友击杀敌人玩家也得分",
        "友方AI优化：有人占点时主动攻击/吃食物",
    ]),
    ("v5.2.0", [
        "团队模式AI改进：敌方更积极追击玩家与队友",
        "淘汰之王模式右上方显示实时排名",
        "修复敌方AI无法攻击我方AI的问题",
    ]),
    ("v5.1.1", [
        "修复占领模式启动时 random.randint 参数为浮点数导致的崩溃",
        "优化占领模式细节，敌方重生更流畅",
    ]),
    ("v5.1.0", [
        "团队4v4改为占领模式：占领中央据点30秒获胜",
        "敌方AI死亡后会重生，保持持续压力",
        "削弱友方AI攻击性，避免过强",
        "平衡性调整，占领区域可视",
    ]),
    ("v5.0.5", [
        "团队模式地图增大至1000x800",
        "默认帧率改为30 FPS，提升低配电脑流畅度",
        "修复敌方AI不攻击友方AI的问题",
    ]),
    ("v5.0.4", [
        "团队模式地图缩小为800x600，战斗更激烈",
        "修复团队模式敌方AI无法击杀玩家的bug",
        "修复团队模式玩家无法吃食物、无法击杀敌人的bug",
    ]),
    ("v5.0.3", ["修复团队模式没有敌方AI的 bug"]),
    ("v5.0.2", ["统一鼠标控制，修复暂停界面悬停"]),
    ("v5.0.1", ["修复下拉菜单错误"]),
    ("v5.0.0", ["新增团队攻防4v4"]),
    ("v4.0.3", ["画面设置新增最高帧数选项"]),
    ("v4.0.2", ["修复移动、下拉菜单穿透"]),
    ("v4.0.1", ["修复崩溃，补全界面"]),
    ("v4.0.0", ["搜打撤重做"]),
    ("v3.36.1", ["修复障碍物生成崩溃"]),
    ("v3.36.0", ["Win11 风格悬停"]),
    ("v3.35.0", ["下拉菜单美化"]),
    ("v3.34.0", ["滚动条"]),
    ("v3.33.0", ["21种分辨率"]),
    ("v3.32.0", ["画面设置"]),
    ("v3.31.0", ["自适应分辨率"]),
    ("v3.30.3", ["修复bug"]),
    ("v3.30.0", ["搜打撤容器"]),
    ("v3.29.0", ["三阶段战术"]),
    ("v3.28.0", ["摸金模式"]),
    ("v3.27.0", ["AI增强"]),
    ("v3.26.0", ["AI绕过蛇身"]),
    ("v3.25.0", ["名字输入"]),
    ("v3.24.0", ["攻击速度调整"]),
    ("v3.23.0", ["本局排名"]),
    ("v3.22.0", ["AI避开其他蛇"]),
    ("v3.21.0", ["战术角色"]),
    ("v3.20.0", ["AI预测位置"]),
    ("v3.19.0", ["狂暴敌人计数器"]),
    ("v3.18.0", ["AI包抄"]),
    ("v3.17.0", ["淘汰之王名字"]),
    ("v3.16.0", ["绕前距离"]),
    ("v3.15.0", ["攻击速度提升"]),
    ("v3.14.0", ["AI攻击加速"]),
    ("v3.13.0", ["行为分离"]),
    ("v3.12.0", ["绕前攻击"]),
    ("v3.11.0", ["AI重写"]),
    ("v3.10.2", ["排行榜优化"]),
    ("v3.10.1", ["显示格式"]),
    ("v3.10.0", ["100敌人"]),
    ("v3.9.0", ["移除时间限制"]),
    ("v3.8.0", ["33敌人"]),
    ("v3.7.0", ["固定敌人数量"]),
    ("v3.6.0", ["淘汰之王"]),
    ("v3.5.0", ["AI躲避玩家"]),
    ("v3.4.9", ["最低速度"]),
    ("v3.4.8", ["修复分数"]),
    ("v3.4.7", ["结算界面"]),
    ("v3.4.6", ["开发者名单"]),
    ("v3.4.5", ["修复加速"]),
    ("v3.4.4", ["返回按钮"]),
    ("v3.4.3", ["更新历史顺序"]),
    ("v3.4.2", ["初始速度"]),
    ("v3.4.1", ["暂停菜单悬停"]),
    ("v3.4.0", ["ESC暂停"]),
    ("v3.3.0", ["格子背景"]),
    ("v3.2.1", ["更新日志首次启动"]),
    ("v3.2.0", ["单独窗口"]),
    ("v3.1.0", ["重做更新提示"]),
    ("v3.0.0", ["Pygame重写"]),
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

ACHIEVEMENTS = [
    {"id": "first_kill", "name": "初次击杀", "desc": "第一次击杀敌人", "icon": "1"},
    {"id": "kill_10", "name": "十人斩", "desc": "累计击杀10个敌人", "icon": "2"},
    {"id": "kill_50", "name": "五十人斩", "desc": "累计击杀50个敌人", "icon": "3"},
    {"id": "win_10", "name": "常胜将军", "desc": "赢得10场游戏", "icon": "4"},
    {"id": "survival_5min", "name": "生存专家", "desc": "单局存活超过5分钟", "icon": "5"},
    {"id": "capture_win", "name": "占领专家", "desc": "在占领模式中获胜", "icon": "6"},
]

def load_achievements():
    if not os.path.exists(ACHIEVE_FILE):
        return {a["id"]: False for a in ACHIEVEMENTS}
    try:
        with open(ACHIEVE_FILE, "r") as f: return json.load(f)
    except: return {a["id"]: False for a in ACHIEVEMENTS}

def save_achievements(data):
    with open(ACHIEVE_FILE, "w") as f: json.dump(data, f, indent=2)

achievements_unlocked = load_achievements()
game_stats = {
    "total_kills": 0,
    "total_games": 0,
    "current_game_kills": 0,
    "current_game_start_time": 0,
    "won_games": 0,
    "capture_wins": 0,
    "current_game_duration": 0,
}

def check_achievements():
    global achievements_unlocked
    modified = False
    if game_stats["total_kills"] >= 1 and not achievements_unlocked.get("first_kill", False):
        achievements_unlocked["first_kill"] = True; modified = True
    if game_stats["total_kills"] >= 10 and not achievements_unlocked.get("kill_10", False):
        achievements_unlocked["kill_10"] = True; modified = True
    if game_stats["total_kills"] >= 50 and not achievements_unlocked.get("kill_50", False):
        achievements_unlocked["kill_50"] = True; modified = True
    if game_stats["won_games"] >= 10 and not achievements_unlocked.get("win_10", False):
        achievements_unlocked["win_10"] = True; modified = True
    if game_stats.get("current_game_duration", 0) > 300 and not achievements_unlocked.get("survival_5min", False):
        achievements_unlocked["survival_5min"] = True; modified = True
    if game_stats["capture_wins"] > 0 and not achievements_unlocked.get("capture_win", False):
        achievements_unlocked["capture_win"] = True; modified = True
    if modified: save_achievements(achievements_unlocked)

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
FPS_OPTIONS = [30, 60, 120, 144, 240]
current_resolution_index = 12
current_display_mode_index = 2
ui_theme_index = 0
fps_index = 0                       # 默认30帧
UI_BG = UI_THEMES[ui_theme_index][1]

SCREEN_WIDTH, SCREEN_HEIGHT = RESOLUTIONS[current_resolution_index]
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DISPLAY_MODES[current_display_mode_index][1])
pygame.display.set_caption(f"自由贪吃蛇 (PVE) {VERSION}")
clock = pygame.time.Clock()
FPS = FPS_OPTIONS[fps_index]

BASE_WIDTH, BASE_HEIGHT = 1600, 900
SCALE_X = SCREEN_WIDTH / BASE_WIDTH
SCALE_Y = SCREEN_HEIGHT / BASE_HEIGHT
SCALE = min(SCALE_X, SCALE_Y)

WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GRAY, LIGHT_GRAY, DARK_GRAY = (128, 128, 128), (192, 192, 192), (64, 64, 64)
RED, DARK_RED = (255, 0, 0), (128, 0, 0)
GREEN, DARK_GREEN = (0, 255, 0), (0, 128, 0)
LIGHT_GREEN = (144, 238, 144)
BLUE, PURPLE, CYAN = (0, 0, 255), (128, 0, 128), (0, 255, 255)
YELLOW, ORANGE, PINK, BROWN = (255, 255, 0), (255, 165, 0), (255, 192, 203), (165, 42, 42)
LIGHT_GRAY_BG = (240, 240, 240)
MENU_BG, MENU_BORDER = (250, 250, 250), (210, 210, 210)
MENU_HOVER = (230, 240, 255)
MENU_HOVER_BORDER = (150, 190, 240)
MENU_CHECK = (30, 100, 220)
SCROLL_BAR_BG, SCROLL_THUMB = (235, 235, 235), (190, 190, 190)
SCROLL_THUMB_HOVER = (160, 160, 160)

def set_world_size(width, height):
    global WORLD_WIDTH, WORLD_HEIGHT, WORLD_MIN_X, WORLD_MAX_X, WORLD_MIN_Y, WORLD_MAX_Y
    WORLD_WIDTH = int(width * SCALE)
    WORLD_HEIGHT = int(height * SCALE)
    WORLD_MIN_X = -WORLD_WIDTH // 2
    WORLD_MAX_X = WORLD_WIDTH // 2
    WORLD_MIN_Y = -WORLD_HEIGHT // 2
    WORLD_MAX_Y = WORLD_HEIGHT // 2

set_world_size(5000, 4000)

BASE_SPEED = 4.5 * SCALE
MIN_SPEED = 2 * SCALE
SPEED_DECAY = 0.016 / SCALE
BASE_SEGMENT_RADIUS = int(8 * SCALE)
FOOD_RADIUS = int(6 * SCALE)
LARGE_FOOD_RADIUS = int(10 * SCALE)
FOOD_COUNT = 125
BOOST_DURATION = 5.0
BOOST_MULTIPLIER = 2.0
ENEMY_COUNT = 10
TIMED_ENEMY_COUNT = 100
FOOD_PER_SEGMENT = 3
ENEMY_FOOD_SEEK_PROB = 0.8
GRID_SIZE = int(40 * SCALE)
MAX_SEGMENT_RADIUS = int(20 * SCALE)
RADIUS_PER_SCORE = 0.02 * SCALE

TEAM_SIZE = 4
CAPTURE_RADIUS = int(80 * SCALE)
CAPTURE_TIME = 30.0

FOOD_COLORS = [RED, ORANGE, YELLOW, PINK, PURPLE, CYAN, (0, 255, 0)]
HEAD_COLOR_OPTIONS = [LIGHT_GREEN, YELLOW, ORANGE, PINK, CYAN, WHITE]
HEAD_COLOR_NAMES = ["浅绿", "黄", "橙", "粉", "青", "白"]
BODY_COLOR_OPTIONS = [GREEN, DARK_GREEN, BLUE, PURPLE, BROWN, GRAY]
BODY_COLOR_NAMES = ["绿", "深绿", "蓝", "紫", "棕", "灰"]
DEFAULT_HEAD_COLOR = LIGHT_GREEN
DEFAULT_BODY_COLOR = DARK_GREEN
BACKGROUND_STYLE_OPTIONS = ["纯黑", "纯白", "格子", "星空"]
BACKGROUND_STYLE_VALUES = [BLACK, WHITE, "grid", "stars"]
DEFAULT_BACKGROUND_STYLE = 2

BUTTON_WIDTH, BUTTON_HEIGHT = int(300 * SCALE), int(44 * SCALE)
BUTTON_HALF_WIDTH = BUTTON_WIDTH // 2
BUTTON_HALF_HEIGHT = BUTTON_HEIGHT // 2
BUTTON_Y_POS = [int(y * SCALE) for y in [45, -5, -55]]
MODE_BUTTON_Y = int(94 * SCALE)
PAUSE_OPTIONS = ["重新开始", "返回开始界面", "退出游戏"]
GAMEOVER_OPTIONS = ["重新开始", "返回开始界面"]
BACK_BUTTON_POS = (int(30 * SCALE), int(30 * SCALE))

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
    min_cam_x = WORLD_MIN_X + SCREEN_WIDTH // 2
    max_cam_x = WORLD_MAX_X - SCREEN_WIDTH // 2
    min_cam_y = WORLD_MIN_Y + SCREEN_HEIGHT // 2
    max_cam_y = WORLD_MAX_Y - SCREEN_HEIGHT // 2
    if min_cam_x < max_cam_x: cam_x = max(min_cam_x, min(cam_x, max_cam_x))
    if min_cam_y < max_cam_y: cam_y = max(min_cam_y, min(cam_y, max_cam_y))
    if min_cam_x >= max_cam_x: cam_x = (WORLD_MIN_X + WORLD_MAX_X) // 2
    if min_cam_y >= max_cam_y: cam_y = (WORLD_MIN_Y + WORLD_MAX_Y) // 2

def world_to_screen(wx, wy): return int(wx - cam_x + SCREEN_WIDTH // 2), int(wy - cam_y + SCREEN_HEIGHT // 2)
def screen_to_world(sx, sy): return sx - SCREEN_WIDTH // 2 + cam_x, sy - SCREEN_HEIGHT // 2 + cam_y

snake = [(0, 0), (-16 * SCALE, 0), (-32 * SCALE, 0), (-48 * SCALE, 0), (-64 * SCALE, 0)]
direction = (1, 0)
enemies = []
foods = []
score = 0
game_active = True
game_started = False
settings_mode = False
paused = False
gameover_screen = False
pause_selection = 0
gameover_selection = 0
boosting = False
boost_start_time = 0
color_centers = {}
mouse_x, mouse_y = 0, 0
background_style = DEFAULT_BACKGROUND_STYLE
head_color_index = 0
body_color_index = 0
selected_setting = 0
hover_button = None
mode_hover = False
setting_option_rects = []
back_button_hover = False
game_mode = "classic"
global_attack_phase = False
attack_trigger_count = 15
show_fps = True
obstacles, containers = [], []
CONTAINER_RADIUS = int(10 * SCALE)
OBSTACLE_RADIUS = int(12 * SCALE)
CONTAINER_COUNT = 30
OBSTACLE_COUNT = 20
REWARD_SCORE = 1
REWARD_FOOD = 2
REWARD_BOOST = 3
temp_boost_remaining = 0
CREDITS = ["开发者名单", "", "策划 & 开发：没冇啊", "代码：deep seek，没冇啊", "美术设计：deep seek，没冇啊", "QA：没冇啊", "", "特别感谢：所有支持本游戏的玩家", "", "Pygame 社区", "Python 编程语言"]

teammates = []
enemy_team_data = []
capture_progress = 0
capture_zone = (0, 0)
red_spawn_timers = {}
SPAWN_DELAY = 3.0

graphics_settings_mode = False
graphics_selected = 0
resolution_dropdown, display_dropdown, theme_dropdown, fps_dropdown = False, False, False, False
resolution_scroll, display_scroll, theme_scroll, fps_scroll = 0, 0, 0, 0
scrolling, scroll_target = False, None
VISIBLE_ITEMS = 5
scroll_info = {}
dropdown_rects = []

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

def apply_display_settings():
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_X, SCALE_Y, SCALE, FPS
    global WORLD_WIDTH, WORLD_HEIGHT, WORLD_MIN_X, WORLD_MAX_X, WORLD_MIN_Y, WORLD_MAX_Y
    global BASE_SPEED, MIN_SPEED, SPEED_DECAY, BASE_SEGMENT_RADIUS, FOOD_RADIUS, LARGE_FOOD_RADIUS
    global GRID_SIZE, MAX_SEGMENT_RADIUS, RADIUS_PER_SCORE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_HALF_WIDTH, BUTTON_HALF_HEIGHT
    global BUTTON_Y_POS, MODE_BUTTON_Y, BACK_BUTTON_POS, CONTAINER_RADIUS, OBSTACLE_RADIUS
    SCREEN_WIDTH, SCREEN_HEIGHT = RESOLUTIONS[current_resolution_index]
    flags = DISPLAY_MODES[current_display_mode_index][1]
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption(f"自由贪吃蛇 (PVE) {VERSION}")
    FPS = FPS_OPTIONS[fps_index]
    SCALE_X = SCREEN_WIDTH / BASE_WIDTH
    SCALE_Y = SCREEN_HEIGHT / BASE_HEIGHT
    SCALE = min(SCALE_X, SCALE_Y)
    BASE_SPEED = 4.5 * SCALE
    MIN_SPEED = 2 * SCALE
    SPEED_DECAY = 0.016 / SCALE
    BASE_SEGMENT_RADIUS = int(8 * SCALE)
    FOOD_RADIUS = int(6 * SCALE)
    LARGE_FOOD_RADIUS = int(10 * SCALE)
    GRID_SIZE = int(40 * SCALE)
    MAX_SEGMENT_RADIUS = int(20 * SCALE)
    RADIUS_PER_SCORE = 0.02 * SCALE
    BUTTON_WIDTH = int(300 * SCALE)
    BUTTON_HEIGHT = int(44 * SCALE)
    BUTTON_HALF_WIDTH = BUTTON_WIDTH // 2
    BUTTON_HALF_HEIGHT = BUTTON_HEIGHT // 2
    BUTTON_Y_POS = [int(y * SCALE) for y in [45, -5, -55]]
    MODE_BUTTON_Y = int(94 * SCALE)
    BACK_BUTTON_POS = (int(30 * SCALE), int(30 * SCALE))
    CONTAINER_RADIUS = int(10 * SCALE)
    OBSTACLE_RADIUS = int(12 * SCALE)

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

def intercept_position(target_head, target_dir, target_speed, from_head):
    """预测目标蛇头前方 intercept_dist 的位置，用于绕前拦截"""
    intercept_dist = 100 * SCALE
    pred_x = target_head[0] + target_dir[0] * intercept_dist
    pred_y = target_head[1] + target_dir[1] * intercept_dist
    return (pred_x, pred_y)

def get_enemy_new_direction(enemy, all_enemies):
    old_dir = enemy['dir']
    head = enemy['body'][0]
    radius = get_segment_radius()
    hostile_segments = []
    if game_mode == "team4v4":
        # 敌方AI攻击玩家和队友
        hostile_segments.extend(snake)
        for tm in teammates:
            hostile_segments.extend(tm['body'])
    else:
        hostile_segments = list(snake)
        for other in all_enemies:
            if other is not enemy: hostile_segments.extend(other['body'])
    if will_collide_with_player(head, old_dir, radius):
        evade = get_evade_direction(head, hostile_segments, old_dir, radius)
        if evade: return evade
    min_dist = 600 * SCALE
    target = None
    # 优先攻击玩家蛇头（绕前）
    player_head = snake[0]
    d = math.hypot(head[0]-player_head[0], head[1]-player_head[1])
    if d < min_dist:
        min_dist = d
        # 使用绕前预测位置
        pred_pos = intercept_position(player_head, direction, get_current_speed(), head)
        target = pred_pos
    # 其次攻击队友蛇头（绕前）
    for tm in teammates:
        d = math.hypot(head[0]-tm['body'][0][0], head[1]-tm['body'][0][1])
        if d < min_dist:
            min_dist = d
            pred_pos = intercept_position(tm['body'][0], tm['dir'], BASE_SPEED*0.7, head)
            target = pred_pos
    if target:
        dx, dy = target[0]-head[0], target[1]-head[1]
        length = math.hypot(dx, dy)
        if length > 0:
            desired = (dx/length, dy/length)
            if not direction_will_collide(head, desired, hostile_segments, radius):
                return desired
    options = [(1,0),(-1,0),(0,1),(0,-1)]
    opp = (-old_dir[0],-old_dir[1])
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
        start_x = math.floor(lw / GRID_SIZE) * GRID_SIZE
        end_x = math.ceil(rw / GRID_SIZE) * GRID_SIZE
        start_y = math.floor(bw / GRID_SIZE) * GRID_SIZE
        end_y = math.ceil(tw / GRID_SIZE) * GRID_SIZE
        x = start_x
        while x < end_x:
            y = start_y
            while y < end_y:
                color = WHITE if ((x//GRID_SIZE)+(y//GRID_SIZE))%2==0 else LIGHT_GRAY_BG
                px, py = world_to_screen(x, y)
                pygame.draw.rect(screen, color, (px, py, GRID_SIZE, GRID_SIZE))
                y += GRID_SIZE
            x += GRID_SIZE
    elif bg_value == "stars":
        screen.fill(BLACK)
        for _ in range(100):
            screen.set_at((random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT)), (random.randint(100,255),)*3)

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

def draw_dropdown_menu(option_rect, items, current_index, menu_type):
    global dropdown_rects, resolution_scroll, display_scroll, theme_scroll, fps_scroll, scroll_info
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
        elif menu_type == "theme": scroll_offset = max(0, min(theme_scroll, total_items - max_visible))
        else: scroll_offset = max(0, min(fps_scroll, total_items - max_visible))
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
            check_surf = get_font(24).render("✓", True, MENU_CHECK)
            screen.blit(check_surf, (item_rect.right - check_surf.get_width() - 15, item_rect.centery - check_surf.get_height() // 2))
    if total_items > max_visible:
        scroll_bar_x = x + width - 12; scroll_bar_y = y + 2
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

def show_achievements():
    font_title = get_font(48)
    font_entry = get_font(24)
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - BUTTON_HALF_WIDTH, SCREEN_HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(event.pos): waiting = False
        mx, my = pygame.mouse.get_pos()
        screen.fill(UI_BG)
        title = font_title.render("成就", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100 * SCALE))
        y = int(200 * SCALE)
        for ach in ACHIEVEMENTS:
            unlocked = achievements_unlocked.get(ach["id"], False)
            icon = "✔" if unlocked else "✘"
            text = f"{ach['name']}: {ach['desc']}  [{icon}]"
            color = GREEN if unlocked else GRAY
            rend = font_entry.render(text, True, color)
            screen.blit(rend, (SCREEN_WIDTH//2 - 300, y))
            y += 40 * SCALE
        draw_option_rect(screen, button_rect, "返回 (ESC)", get_font(24), is_hovered=button_rect.collidepoint(mx, my))
        pygame.display.flip(); clock.tick(FPS)

def show_name_input_screen():
    font_title = get_font(48)
    font_prompt = get_font(24)
    font_input = get_font(24)
    font_button = get_font(24)
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
        y += int(60 * SCALE)
        disp_text = f"显示方式: {DISPLAY_MODES[current_display_mode_index][0]}"
        disp_rendered = font_opt.render(disp_text, True, BLACK)
        disp_rect = disp_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - disp_rendered.get_width()//2, y))
        if graphics_selected == 1: draw_rounded_rect(screen, disp_rect.inflate(20,12), MENU_HOVER, radius=8)
        screen.blit(disp_rendered, (disp_rect.x, disp_rect.y))
        y += int(60 * SCALE)
        theme_text = f"界面主题: {UI_THEMES[ui_theme_index][0]}"
        theme_rendered = font_opt.render(theme_text, True, BLACK)
        theme_rect = theme_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - theme_rendered.get_width()//2, y))
        if graphics_selected == 2: draw_rounded_rect(screen, theme_rect.inflate(20,12), MENU_HOVER, radius=8)
        screen.blit(theme_rendered, (theme_rect.x, theme_rect.y))
        y += int(60 * SCALE)
        fps_text = f"最高帧数: {FPS_OPTIONS[fps_index]}"
        fps_rendered = font_opt.render(fps_text, True, BLACK)
        fps_rect = fps_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - fps_rendered.get_width()//2, y))
        if graphics_selected == 3: draw_rounded_rect(screen, fps_rect.inflate(20,12), MENU_HOVER, radius=8)
        screen.blit(fps_rendered, (fps_rect.x, fps_rect.y))
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
        if fps_dropdown:
            items = [str(f) for f in FPS_OPTIONS]
            draw_dropdown_menu(fps_rect, items, fps_index, "fps")
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
        elif game_mode == "team4v4": mode_text, mode_color = "模式: 占领模式  (M键切换)", ORANGE
        else: mode_text, mode_color = "模式: 经典  (M键切换)", BLACK
        mode_rend = mode_font.render(mode_text, True, mode_color)
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
            btn_rect = text_rend.get_rect(center=(SCREEN_WIDTH//2, screen_y))
            is_hov = btn_rect.inflate(20,12).collidepoint(mouse_x, mouse_y) or hover_button == i
            if is_hov:
                draw_rounded_rect(screen, btn_rect.inflate(20, 12), MENU_HOVER, radius=8)
                pygame.draw.rect(screen, MENU_HOVER_BORDER, btn_rect.inflate(20, 12), 2, border_radius=8)
            screen.blit(text_rend, btn_rect.topleft)
        hint = get_font(18).render("按 H 查看历史排行榜  按 J 查看成就", True, DARK_GRAY)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 80))
        pygame.display.flip()
        return

    # 游戏内界面
    draw_background()
    for ox, oy, orad in obstacles: pygame.draw.circle(screen, BROWN, world_to_screen(ox, oy), orad)
    for cx, cy, cr, rt, _ in containers:
        color = (255,215,0) if rt==REWARD_SCORE else (0,255,0) if rt==REWARD_FOOD else (0,255,255)
        pygame.draw.circle(screen, color, world_to_screen(cx, cy), cr)
    if game_mode == "team4v4":
        pygame.draw.circle(screen, YELLOW, world_to_screen(*capture_zone), CAPTURE_RADIUS, 3)
        if capture_progress > 0:
            bar_len = int(200 * SCALE)
            fill = int(bar_len * (capture_progress / CAPTURE_TIME))
            pygame.draw.rect(screen, LIGHT_GREEN, (SCREEN_WIDTH//2 - bar_len//2, 50*SCALE, fill, 15*SCALE))
            pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2 - bar_len//2, 50*SCALE, bar_len, 15*SCALE), 2)
        screen.blit(get_font(20).render(f"占领 {int(capture_progress)}/{int(CAPTURE_TIME)}s", True, BLACK), (SCREEN_WIDTH//2 - 100, 20*SCALE))
    head_c = HEAD_COLOR_OPTIONS[head_color_index]; body_c = BODY_COLOR_OPTIONS[body_color_index]
    cr = get_segment_radius()
    for i, (x,y) in enumerate(snake): pygame.draw.circle(screen, head_c if i==0 else body_c, world_to_screen(x,y), cr)
    if game_mode == "team4v4":
        for enemy in enemy_team_data:
            if enemy['body'][0][0] != -999:
                for i, (x,y) in enumerate(enemy['body']): pygame.draw.circle(screen, RED, world_to_screen(x,y), cr)
        for tm in teammates:
            for i, (x,y) in enumerate(tm['body']): pygame.draw.circle(screen, (0,200,200), world_to_screen(x,y), cr)
    else:
        for enemy in enemies:
            col = RED if enemy.get('team') != 'blue' else BLUE
            for i, (x,y) in enumerate(enemy['body']): pygame.draw.circle(screen, col, world_to_screen(x,y), cr)
    for fx, fy, fc, fr in foods: pygame.draw.circle(screen, fc, world_to_screen(fx, fy), fr)
    left, bottom = world_to_screen(WORLD_MIN_X+cr, WORLD_MIN_Y+cr)
    right, top = world_to_screen(WORLD_MAX_X-cr, WORLD_MAX_Y-cr)
    pygame.draw.rect(screen, RED, (left, bottom, right-left, top-bottom), 2)
    txt_col = WHITE if BACKGROUND_STYLE_VALUES[background_style]==BLACK else BLACK
    fi, fs = get_font(16), get_font(12)
    screen.blit(fi.render(f"Score: {score}", True, txt_col), (SCREEN_WIDTH-int(200*SCALE), int(30*SCALE)))
    # 淘汰之王实时排名
    if game_mode == "timed":
        rankings = get_sorted_rankings()
        rank_font = get_font(18)
        rank_surf = pygame.Surface((int(220*SCALE), int(300*SCALE)), pygame.SRCALPHA)
        rank_surf.fill((0,0,0,100))
        screen.blit(rank_surf, (SCREEN_WIDTH - int(240*SCALE), int(60*SCALE)))
        screen.blit(rank_font.render("实时排名", True, WHITE), (SCREEN_WIDTH - int(230*SCALE), int(70*SCALE)))
        y_offset = int(100*SCALE)
        for i, (name, scr) in enumerate(rankings[:15]):
            color = YELLOW if i == 0 else WHITE
            display_name = name if len(name) <= 10 else name[:7] + "..."
            line = f"{i+1}. {display_name} {scr}"
            screen.blit(rank_font.render(line, True, color), (SCREEN_WIDTH - int(230*SCALE), y_offset))
            y_offset += int(18*SCALE)
    if show_fps: screen.blit(fs.render(f"FPS: {int(clock.get_fps())}", True, txt_col), (SCREEN_WIDTH-int(100*SCALE), SCREEN_HEIGHT-int(30*SCALE)))

    if not game_active:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((128,128,128,200))
        screen.blit(overlay, (0,0))
        gof = get_font(48)
        if game_mode == "team4v4":
            result_text = "占领成功！" if capture_progress >= CAPTURE_TIME else "占领失败！"
            screen.blit(gof.render(result_text, True, WHITE), (SCREEN_WIDTH//2 - 150, 200*SCALE))
        else:
            screen.blit(gof.render("游戏结束", True, WHITE), (SCREEN_WIDTH//2 - 100, 200*SCALE))
        oy = int(400*SCALE)
        for i, opt in enumerate(GAMEOVER_OPTIONS):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, opt if i != gameover_selection else "▶ " + opt + " ◀",
                             get_font(36), is_selected=(i == gameover_selection), is_hovered=is_hov, base_color=WHITE)

    if paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,128))
        screen.blit(overlay, (0,0))
        pf = get_font(48)
        screen.blit(pf.render("暂停", True, WHITE), (SCREEN_WIDTH//2 - 60, 200*SCALE))
        oy = int(350*SCALE)
        for i, opt in enumerate(PAUSE_OPTIONS):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 200, oy + i*int(60*SCALE) - 20, 400, 40)
            is_hov = rect.collidepoint(mouse_x, mouse_y)
            draw_option_rect(screen, rect, opt if i != pause_selection else "▶ " + opt + " ◀",
                             get_font(36), is_selected=(i == pause_selection), is_hovered=is_hov, base_color=WHITE)

    pygame.display.flip()

def restart_game():
    global snake, direction, foods, score, game_active, boosting, color_centers
    global enemies, teammates, enemy_team_data, capture_progress, capture_zone, red_spawn_timers
    global gameover_killer_name, global_attack_phase, temp_boost_remaining
    global obstacles, containers, game_stats
    snake = [(0,0), (-16*SCALE,0), (-32*SCALE,0), (-48*SCALE,0), (-64*SCALE,0)]
    direction = (1,0)
    score = 0
    game_active = True
    boosting = False
    color_centers.clear()
    enemies = []
    teammates = []
    enemy_team_data = []
    capture_progress = 0
    capture_zone = (0, 0)
    red_spawn_timers = {}
    gameover_killer_name = None
    global_attack_phase = False
    temp_boost_remaining = 0
    obstacles.clear(); containers.clear()
    game_stats["current_game_start_time"] = time.time()
    game_stats["current_game_kills"] = 0

    if game_mode == "team4v4":
        set_world_size(1000, 800)
        capture_zone = (0, 0)
        snake = [(capture_zone[0]-200*SCALE, capture_zone[1]),
                 (capture_zone[0]-216*SCALE, capture_zone[1]),
                 (capture_zone[0]-232*SCALE, capture_zone[1])]
        for i in range(3):
            x = capture_zone[0] - 200*SCALE + random.randint(-int(60*SCALE), int(60*SCALE))
            y = capture_zone[1] + random.randint(-int(60*SCALE), int(60*SCALE))
            body = [(x, y), (x-16*SCALE, y), (x-32*SCALE, y)]
            teammates.append({'body': body, 'dir': (1,0), 'team': 'blue', 'name': f"队友{i+1}"})
        for i in range(4):
            x = capture_zone[0] + 200*SCALE + random.randint(-int(60*SCALE), int(60*SCALE))
            y = capture_zone[1] + random.randint(-int(60*SCALE), int(60*SCALE))
            body = [(x, y), (x-16*SCALE, y), (x-32*SCALE, y)]
            enemy_team_data.append({'body': body, 'dir': (-1,0), 'team': 'red', 'name': f"敌方{i+1}", 'id': i})
        generate_foods(FOOD_COUNT // 3)
    else:
        set_world_size(5000, 4000)
        generate_foods(FOOD_COUNT)
        ec = TIMED_ENEMY_COUNT if game_mode=="timed" else ENEMY_COUNT
        min_dist_sq = (get_segment_radius()*4)**2
        for _ in range(ec):
            placed = False
            for _ in range(500):
                x, y = random_position()
                if any((x-sx)**2+(y-sy)**2 < min_dist_sq for sx,sy in snake): continue
                o = False
                for enemy in enemies:
                    if any((x-sx)**2+(y-sy)**2 < min_dist_sq for sx,sy in enemy['body']): o = True; break
                if not o:
                    body = [(x,y), (x-16*SCALE,y), (x-32*SCALE,y)]
                    enemies.append({'body':body,'dir':random.choice([(1,0),(-1,0),(0,1),(0,-1)]),
                                    'score':0,'name':random.choice(ENEMY_NAMES),'state':'idle'})
                    placed = True; break
            if not placed:
                x,y = random_position()
                body = [(x,y),(x-16*SCALE,y),(x-32*SCALE,y)]
                enemies.append({'body':body,'dir':random.choice([(1,0),(-1,0),(0,1),(0,-1)]),'score':0,'name':'Enemy','state':'idle'})
    update_camera(snake[0][0], snake[0][1])

def new_game(): restart_game()
def start_game():
    global game_started
    if not game_started and not settings_mode:
        new_game()
        game_started = True

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
    background_style = DEFAULT_BACKGROUND_STYLE
    head_color_index = HEAD_COLOR_OPTIONS.index(DEFAULT_HEAD_COLOR)
    body_color_index = BODY_COLOR_OPTIONS.index(DEFAULT_BODY_COLOR)
    settings_mode = False
def enter_settings():
    global settings_mode, selected_setting
    if not game_started and not settings_mode: settings_mode = True; selected_setting = 0

# ==================== 主循环 ====================
def main():
    global game_started, game_mode, graphics_settings_mode, settings_mode, paused, gameover_screen
    global snake, direction, enemies, teammates, enemy_team_data, capture_progress, capture_zone, red_spawn_timers
    global score, game_active, boosting, color_centers
    global mouse_x, mouse_y, hover_button, back_button_hover, mode_hover
    global selected_setting, pause_selection, gameover_selection
    global graphics_selected, resolution_dropdown, display_dropdown, theme_dropdown, fps_dropdown
    global resolution_scroll, display_scroll, theme_scroll, fps_scroll, scrolling, scroll_target
    global FPS, clock
    global game_stats, achievements_unlocked, temp_boost_remaining, boost_start_time
    global current_resolution_index, current_display_mode_index, ui_theme_index, fps_index, UI_BG
    global dropdown_rects

    need_show, _ = check_version()
    if need_show: show_changelog(); write_version()

    if not os.path.exists(NAME_FILE):
        save_player_name(show_name_input_screen())

    new_game()
    last_time = time.time()
    running = True
    while running:
        dt = time.time() - last_time; last_time = time.time()
        if temp_boost_remaining > 0: temp_boost_remaining -= 1
        if game_started and game_active and not paused and not gameover_screen:
            player_pos_history.append(snake[0])
            player_dir_history.append(direction)
            if time.time() - game_stats["current_game_start_time"] > 300:
                game_stats["current_game_duration"] = time.time() - game_stats["current_game_start_time"]
                check_achievements()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                if scrolling and scroll_target in scroll_info:
                    info = scroll_info[scroll_target]
                    bar = info['bar_rect']
                    thumb_h = info['thumb_rect'].height
                    total = info['total']
                    visible = info['max_visible']
                    if bar.height > thumb_h:
                        ratio = (mouse_y - bar.top - thumb_h/2) / (bar.height - thumb_h)
                        new_off = max(0, min(int(ratio*(total-visible)+0.5), total-visible))
                        if scroll_target == "res": resolution_scroll = new_off
                        elif scroll_target == "disp": display_scroll = new_off
                        elif scroll_target == "theme": theme_scroll = new_off
                        elif scroll_target == "fps": fps_scroll = new_off
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if graphics_settings_mode: graphics_settings_mode = False; resolution_dropdown = display_dropdown = theme_dropdown = fps_dropdown = False
                    elif settings_mode: settings_cancel()
                    elif not game_started: pass
                    elif gameover_screen: pass
                    else: paused = not paused
                if not game_started:
                    if event.key == pygame.K_SPACE: start_game()
                    elif event.key == pygame.K_s: enter_settings()
                    elif event.key == pygame.K_q: pygame.quit(); exit()
                    elif event.key == pygame.K_m:
                        if game_mode == "classic": game_mode = "timed"
                        elif game_mode == "timed": game_mode = "team4v4"
                        else: game_mode = "classic"
                        generate_foods(FOOD_COUNT)
                    elif event.key == pygame.K_h: show_rankings()
                    elif event.key == pygame.K_j: show_achievements()
                elif game_active and not paused:
                    if event.key in (pygame.K_LCTRL, pygame.K_RCTRL): boosting = True; boost_start_time = time.time()
                if graphics_settings_mode:
                    if event.key == pygame.K_UP: graphics_selected = (graphics_selected-1)%4; resolution_dropdown = display_dropdown = theme_dropdown = fps_dropdown = False
                    elif event.key == pygame.K_DOWN: graphics_selected = (graphics_selected+1)%4; resolution_dropdown = display_dropdown = theme_dropdown = fps_dropdown = False
                    elif event.key == pygame.K_LEFT:
                        if graphics_selected==0: current_resolution_index = (current_resolution_index-1)%len(RESOLUTIONS); apply_display_settings()
                        elif graphics_selected==1: current_display_mode_index = (current_display_mode_index-1)%len(DISPLAY_MODES); apply_display_settings()
                        elif graphics_selected==2: ui_theme_index = (ui_theme_index-1)%len(UI_THEMES); UI_BG = UI_THEMES[ui_theme_index][1]
                        elif graphics_selected==3: fps_index = (fps_index-1)%len(FPS_OPTIONS); apply_display_settings()
                    elif event.key == pygame.K_RIGHT:
                        if graphics_selected==0: current_resolution_index = (current_resolution_index+1)%len(RESOLUTIONS); apply_display_settings()
                        elif graphics_selected==1: current_display_mode_index = (current_display_mode_index+1)%len(DISPLAY_MODES); apply_display_settings()
                        elif graphics_selected==2: ui_theme_index = (ui_theme_index+1)%len(UI_THEMES); UI_BG = UI_THEMES[ui_theme_index][1]
                        elif graphics_selected==3: fps_index = (fps_index+1)%len(FPS_OPTIONS); apply_display_settings()
                    elif event.key == pygame.K_RETURN:
                        if graphics_selected==0: resolution_dropdown = not resolution_dropdown; display_dropdown = theme_dropdown = fps_dropdown = False
                        elif graphics_selected==1: display_dropdown = not display_dropdown; resolution_dropdown = theme_dropdown = fps_dropdown = False
                        elif graphics_selected==2: theme_dropdown = not theme_dropdown; resolution_dropdown = display_dropdown = fps_dropdown = False
                        else: fps_dropdown = not fps_dropdown; resolution_dropdown = display_dropdown = theme_dropdown = False
                    continue
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL): boosting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dropdown_clicked = False
                for dtype, idx, rect in dropdown_rects:
                    if rect.collidepoint(mouse_x, mouse_y):
                        dropdown_clicked = True
                        if dtype == "res": current_resolution_index = idx
                        elif dtype == "disp": current_display_mode_index = idx
                        elif dtype == "theme": ui_theme_index = idx; UI_BG = UI_THEMES[idx][1]
                        elif dtype == "fps": fps_index = idx
                        apply_display_settings()
                        resolution_dropdown = display_dropdown = theme_dropdown = fps_dropdown = False
                        break
                if dropdown_clicked: continue
                if graphics_settings_mode:
                    back_rect = pygame.Rect(BACK_BUTTON_POS[0]+20, BACK_BUTTON_POS[1]+20, 60*SCALE, 30*SCALE)
                    if back_rect.collidepoint(mouse_x, mouse_y):
                        graphics_settings_mode = False; resolution_dropdown = display_dropdown = theme_dropdown = fps_dropdown = False; continue
                    res_rendered = get_font(24).render(f"画面分辨率: {RESOLUTIONS[current_resolution_index][0]} × {RESOLUTIONS[current_resolution_index][1]}", True, BLACK)
                    res_rect = res_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - res_rendered.get_width()//2, int(270*SCALE)))
                    disp_rendered = get_font(24).render(f"显示方式: {DISPLAY_MODES[current_display_mode_index][0]}", True, BLACK)
                    disp_rect = disp_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - disp_rendered.get_width()//2, int(330*SCALE)))
                    theme_rendered = get_font(24).render(f"界面主题: {UI_THEMES[ui_theme_index][0]}", True, BLACK)
                    theme_rect = theme_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - theme_rendered.get_width()//2, int(390*SCALE)))
                    fps_rendered = get_font(24).render(f"最高帧数: {FPS_OPTIONS[fps_index]}", True, BLACK)
                    fps_rect = fps_rendered.get_rect(topleft=(SCREEN_WIDTH//2 - fps_rendered.get_width()//2, int(450*SCALE)))
                    if res_rect.collidepoint(mouse_x, mouse_y):
                        graphics_selected = 0; resolution_dropdown = not resolution_dropdown; display_dropdown = theme_dropdown = fps_dropdown = False
                    elif disp_rect.collidepoint(mouse_x, mouse_y):
                        graphics_selected = 1; display_dropdown = not display_dropdown; resolution_dropdown = theme_dropdown = fps_dropdown = False
                    elif theme_rect.collidepoint(mouse_x, mouse_y):
                        graphics_selected = 2; theme_dropdown = not theme_dropdown; resolution_dropdown = display_dropdown = fps_dropdown = False
                    elif fps_rect.collidepoint(mouse_x, mouse_y):
                        graphics_selected = 3; fps_dropdown = not fps_dropdown; resolution_dropdown = display_dropdown = theme_dropdown = False
                    continue
                if settings_mode:
                    back_rect = pygame.Rect(BACK_BUTTON_POS[0]+50, BACK_BUTTON_POS[1]+20, 60*SCALE, 30*SCALE)
                    if back_rect.collidepoint(mouse_x, mouse_y): settings_cancel(); continue
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
                            elif i == 2: pygame.quit(); exit()
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
                if not game_started:
                    mode_font = get_font(24)
                    if game_mode == "timed": mode_text = "模式: 淘汰之王  (M键切换)"
                    elif game_mode == "team4v4": mode_text = "模式: 占领模式  (M键切换)"
                    else: mode_text = "模式: 经典  (M键切换)"
                    mode_rend = mode_font.render(mode_text, True, BLACK)
                    mode_rect = mode_rend.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + MODE_BUTTON_Y))
                    if mode_rect.collidepoint(mouse_x, mouse_y):
                        if game_mode == "classic": game_mode = "timed"
                        elif game_mode == "timed": game_mode = "team4v4"
                        else: game_mode = "classic"
                        generate_foods(FOOD_COUNT)
                        continue
                    for i, y_center in enumerate(BUTTON_Y_POS):
                        screen_y = SCREEN_HEIGHT//2 + y_center
                        btn_font = get_font(24) if i == 0 else get_font(18)
                        text_rend = btn_font.render(["开始游戏 (SPACE)", "设置 (S)", "退出 (Q)"][i], True, BLACK)
                        btn_rect = text_rend.get_rect(center=(SCREEN_WIDTH//2, screen_y))
                        if btn_rect.inflate(20,12).collidepoint(mouse_x, mouse_y):
                            if i == 0: start_game()
                            elif i == 1: enter_settings()
                            elif i == 2: pygame.quit(); exit()
                            break
                    continue
            elif event.type == pygame.MOUSEWHEEL:
                if graphics_settings_mode:
                    if resolution_dropdown: resolution_scroll = max(0, min(resolution_scroll-event.y, len(RESOLUTIONS)-VISIBLE_ITEMS))
                    if display_dropdown: display_scroll = max(0, min(display_scroll-event.y, len(DISPLAY_MODES)-VISIBLE_ITEMS))
                    if theme_dropdown: theme_scroll = max(0, min(theme_scroll-event.y, len(UI_THEMES)-VISIBLE_ITEMS))
                    if fps_dropdown: fps_scroll = max(0, min(fps_scroll-event.y, len(FPS_OPTIONS)-VISIBLE_ITEMS))
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: scrolling = False; scroll_target = None

        # 游戏更新
        if game_started and game_active and not paused and not gameover_screen:
            wx, wy = screen_to_world(mouse_x, mouse_y)
            hx, hy = snake[0]
            dx, dy = wx - hx, wy - hy
            if abs(dx) > 1 or abs(dy) > 1:
                direction = (dx / math.hypot(dx, dy), dy / math.hypot(dx, dy))
            cs = get_current_speed() if game_mode != "team4v4" else BASE_SPEED
            new_head = (snake[0][0] + direction[0]*cs, snake[0][1] + direction[1]*cs)
            if not check_boundary(new_head):
                snake.insert(0, new_head)
                snake.pop()
            else:
                game_active = False
                gameover_screen = True
                if game_mode == "timed" and score > 0: add_score(player_name, score)
            update_camera(snake[0][0], snake[0][1])

            # 食物碰撞
            current_radius = get_segment_radius()
            eat_threshold_sq = (current_radius + FOOD_RADIUS) ** 2
            large_eat_threshold_sq = (current_radius + LARGE_FOOD_RADIUS) ** 2
            ate_index = None
            for i, (fx, fy, _, fr) in enumerate(foods):
                threshold = large_eat_threshold_sq if fr == LARGE_FOOD_RADIUS else eat_threshold_sq
                if (new_head[0] - fx) ** 2 + (new_head[1] - fy) ** 2 < threshold:
                    ate_index = i
                    break
            if ate_index is not None:
                score += 1
                tail = snake[-1]
                snake.append(tail)
                del foods[ate_index]

            if game_mode != "team4v4":
                for enemy in enemies:
                    enemy_head = enemy['body'][0]
                    for i, (fx, fy, _, fr) in enumerate(foods):
                        if (enemy_head[0]-fx)**2+(enemy_head[1]-fy)**2 < eat_threshold_sq:
                            enemy['score'] += 1
                            enemy['body'].append(enemy['body'][-1])
                            del foods[i]
                            break

            if game_mode == "team4v4":
                collision_threshold_sq = (current_radius * 2) ** 2
                # 玩家与敌方碰撞
                for enemy in enemy_team_data:
                    if enemy['body'][0][0] == -999: continue
                    for seg in enemy['body'][1:]:
                        if (snake[0][0] - seg[0])**2 + (snake[0][1] - seg[1])**2 < collision_threshold_sq:
                            game_active = False
                            gameover_screen = True
                            break
                    if not game_active: break
                if game_active:
                    for enemy in enemy_team_data:
                        if enemy['body'][0][0] == -999: continue
                        if (snake[0][0] - enemy['body'][0][0])**2 + (snake[0][1] - enemy['body'][0][1])**2 < collision_threshold_sq:
                            game_active = False
                            gameover_screen = True
                            break
                # 玩家和队友击杀敌方 -> 共享分数
                for enemy in enemy_team_data[:]:
                    if enemy['body'][0][0] == -999: continue
                    enemy_head = enemy['body'][0]
                    killed = False
                    for seg in snake[1:]:
                        if (enemy_head[0] - seg[0])**2 + (enemy_head[1] - seg[1])**2 < collision_threshold_sq:
                            killed = True; break
                    if not killed:
                        for tm in teammates:
                            for seg in tm['body'][1:]:
                                if (enemy_head[0] - seg[0])**2 + (enemy_head[1] - seg[1])**2 < collision_threshold_sq:
                                    killed = True; break
                            if killed: break
                    if killed:
                        # 标记为死亡并开始重生计时器
                        enemy['body'][0] = (-999, -999)
                        enemy['body'][1] = (-999, -999)
                        enemy['body'][2] = (-999, -999)
                        if enemy['id'] not in red_spawn_timers:
                            red_spawn_timers[enemy['id']] = 0
                        game_stats["total_kills"] += 1
                        game_stats["current_game_kills"] += 1
                        score += 1          # 团队共享分数
                        check_achievements()
                # 占领机制
                player_in_zone = math.hypot(snake[0][0]-capture_zone[0], snake[0][1]-capture_zone[1]) < CAPTURE_RADIUS
                teammates_in_zone = any(math.hypot(tm['body'][0][0]-capture_zone[0], tm['body'][0][1]-capture_zone[1]) < CAPTURE_RADIUS for tm in teammates)
                if player_in_zone or teammates_in_zone:
                    capture_progress = min(capture_progress + dt, CAPTURE_TIME)
                    if capture_progress >= CAPTURE_TIME:
                        game_active = False
                        gameover_screen = True
                        game_stats["won_games"] += 1
                        game_stats["capture_wins"] += 1
                        check_achievements()
                else:
                    capture_progress = max(0, capture_progress - dt * 0.5)
                # 敌方重生
                for enemy in enemy_team_data:
                    if enemy['body'][0][0] == -999:
                        red_spawn_timers[enemy['id']] = red_spawn_timers.get(enemy['id'], 0) + dt
                        if red_spawn_timers[enemy['id']] >= SPAWN_DELAY:
                            x = capture_zone[0] + 200*SCALE + random.randint(-int(60*SCALE), int(60*SCALE))
                            y = capture_zone[1] + random.randint(-int(60*SCALE), int(60*SCALE))
                            enemy['body'] = [(x, y), (x-16*SCALE, y), (x-32*SCALE, y)]
                            red_spawn_timers[enemy['id']] = 0
                    else:
                        nd = get_enemy_new_direction(enemy, [])
                        enemy['body'][0] = (enemy['body'][0][0] + nd[0]*BASE_SPEED, enemy['body'][0][1] + nd[1]*BASE_SPEED)
                        enemy['body'].pop()
                        enemy['body'].insert(0, enemy['body'][0])
                # 队友AI (优化：占点、攻击、吃食物)
                for tm in teammates:
                    # 判断点内是否有队友
                    any_teammate_in_zone = player_in_zone or any(
                        math.hypot(t['body'][0][0]-capture_zone[0], t['body'][0][1]-capture_zone[1]) < CAPTURE_RADIUS
                        for t in teammates if t != tm)
                    if not any_teammate_in_zone:
                        # 优先移动到占点
                        target = capture_zone
                        dx = target[0] - tm['body'][0][0]
                        dy = target[1] - tm['body'][0][1]
                        length = math.hypot(dx, dy)
                        if length > 0:
                            nd = (dx/length, dy/length)
                            if not direction_will_collide(tm['body'][0], nd, [s for t in teammates if t != tm for s in t['body']] + snake, get_segment_radius()):
                                tm['dir'] = nd
                            else:
                                options = [(1,0),(-1,0),(0,1),(0,-1)]
                                options = [o for o in options if o != (-tm['dir'][0], -tm['dir'][1])]
                                tm['dir'] = random.choice(options) if options else (1,0)
                    else:
                        # 点内有人，可以攻击敌人或吃食物
                        # 查找最近的敌人
                        min_dist = 400 * SCALE
                        target = None
                        for enemy in enemy_team_data:
                            if enemy['body'][0][0] == -999: continue
                            d = math.hypot(tm['body'][0][0]-enemy['body'][0][0], tm['body'][0][1]-enemy['body'][0][1])
                            if d < min_dist:
                                min_dist = d
                                # 绕前拦截
                                pred = intercept_position(enemy['body'][0], enemy['dir'], BASE_SPEED, tm['body'][0])
                                target = pred
                        if target:
                            dx, dy = target[0]-tm['body'][0][0], target[1]-tm['body'][0][1]
                            length = math.hypot(dx, dy)
                            if length > 0:
                                nd = (dx/length, dy/length)
                                if not direction_will_collide(tm['body'][0], nd, [s for t in teammates if t != tm for s in t['body']] + snake, get_segment_radius()):
                                    tm['dir'] = nd
                                else:
                                    options = [(1,0),(-1,0),(0,1),(0,-1)]
                                    options = [o for o in options if o != (-tm['dir'][0], -tm['dir'][1])]
                                    tm['dir'] = random.choice(options) if options else (1,0)
                        else:
                            # 没有敌人，寻找最近的食物
                            min_food_dist = 400 * SCALE
                            food_target = None
                            for fx, fy, _, _ in foods:
                                d = math.hypot(tm['body'][0][0]-fx, tm['body'][0][1]-fy)
                                if d < min_food_dist:
                                    min_food_dist = d
                                    food_target = (fx, fy)
                            if food_target:
                                dx, dy = food_target[0]-tm['body'][0][0], food_target[1]-tm['body'][0][1]
                                length = math.hypot(dx, dy)
                                if length > 0:
                                    tm['dir'] = (dx/length, dy/length)
                            else:
                                # 随机移动
                                options = [(1,0),(-1,0),(0,1),(0,-1)]
                                options = [o for o in options if o != (-tm['dir'][0], -tm['dir'][1])]
                                tm['dir'] = random.choice(options) if options else (1,0)
                    tm['body'][0] = (tm['body'][0][0] + tm['dir'][0]*BASE_SPEED*0.7, tm['body'][0][1] + tm['dir'][1]*BASE_SPEED*0.7)
                    tm['body'].pop()
                    tm['body'].insert(0, tm['body'][0])
            else:
                collision_threshold_sq = (current_radius * 2) ** 2
                for enemy in enemies:
                    for seg in enemy['body'][1:]:
                        if (snake[0][0] - seg[0])**2 + (snake[0][1] - seg[1])**2 < collision_threshold_sq:
                            game_active = False
                            gameover_screen = True
                            gameover_killer_name = enemy['name']
                            if game_mode == "timed" and score > 0: add_score(player_name, score)
                            break
                    if not game_active: break
                if game_active:
                    for enemy in enemies[:]:
                        enemy_head = enemy['body'][0]
                        for seg in snake[1:]:
                            if (enemy_head[0] - seg[0])**2 + (enemy_head[1] - seg[1])**2 < collision_threshold_sq:
                                enemies.remove(enemy)
                                game_stats["total_kills"] += 1
                                game_stats["current_game_kills"] += 1
                                spawn_foods_from_enemy(enemy['body'])
                                break
                for enemy in enemies:
                    for other in enemies:
                        if other is enemy: continue
                        if (enemy['body'][0][0] - other['body'][0][0])**2 + (enemy['body'][0][1] - other['body'][0][1])**2 < collision_threshold_sq:
                            enemies.remove(enemy)
                            break
                for enemy in enemies:
                    nd = get_enemy_new_direction(enemy, enemies)
                    enemy['body'][0] = (enemy['body'][0][0] + nd[0]*get_base_speed(), enemy['body'][0][1] + nd[1]*get_base_speed())
                    enemy['body'].pop()
                    enemy['body'].insert(0, enemy['body'][0])

        draw()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()