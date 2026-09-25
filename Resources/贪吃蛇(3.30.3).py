import pygame
import random
import math
import os
import time
import json
import hashlib
from collections import deque

# ========== 游戏版本 ==========
VERSION = "v3.30.3"
VERSION_FILE = os.path.join(os.path.expanduser("~"), ".snake_version_pygame")
NAME_FILE = os.path.join(os.path.dirname(__file__), "player_name.txt")

# 所有版本更新日志（从最新到最老）
ALL_CHANGELOGS = [
    ("v3.30.3", [
        "修复搜打撤模式下障碍物和容器无法生成的bug",
        "字体优先使用游戏目录下的 microsoft-yahei.ttf",
    ]),
    ("v3.30.2", [
        "字体强制使用微软雅黑，提高中文显示兼容性",
    ]),
    ("v3.30.1", [
        "修复中文字体加载问题，增强字体兼容性",
    ]),
    ("v3.30.0", [
        "搜打撤模式大幅增强：地图中随机生成障碍物和可搜索容器",
        "障碍物不可穿越，增加战术阻挡",
        "容器可被蛇或AI搜索，获得分数、食物或临时加速奖励",
        "AI在搜索阶段会主动寻找并搜索容器",
        "新增容器搜索特效和提示",
    ]),
    ("v3.29.0", [
        "搜打撤模式重做：参考三角洲行动，新增三阶段战术（搜索、打击、撤离）",
        "搜索阶段：AI 扇形搜索玩家位置，不主动攻击",
        "打击阶段：AI 加速并全力攻击玩家",
        "撤离阶段：AI 加速远离玩家并向边界撤退",
        "UI 增加阶段显示",
    ]),
    ("v3.28.0", [
        "新增摸金模式：AI采用搜索-摸金-撤离战术",
        "淘汰之王模式AI大幅增强：攻击速度提升、触发阈值降低",
        "添加实用功能：FPS显示、性能模式切换",
        "改良UI：抗锯齿渲染、阴影效果、星空背景",
        "设置中增加画质选项：可调节抗锯齿级别（性能/均衡/高品质）",
    ]),
    ("v3.27.0", [
        "AI史诗级增强：躲避玩家身体优先级最高，10种攻击策略，有组织有预谋的协同攻击",
    ]),
    ("v3.26.0", [
        "AI大幅度绕过蛇身，向蛇头前方攻击（扩大避障角度至±1.2弧度）",
    ]),
    ("v3.25.0", [
        "名字输入改为独立界面，仅在首次启动时显示",
    ]),
    ("v3.24.0", [
        "AI攻击速度从3倍改为2倍",
        "首次游戏需输入玩家名字",
        "淘汰之王模式实时显示所有敌人和玩家的排名列表（1-100）",
    ]),
    ("v3.23.0", [
        "排名改为本局排名，实时显示玩家在当前对局中的名次",
    ]),
    ("v3.22.0", [
        "AI攻击时智能避开其他蛇的身体，避免自杀式冲锋",
    ]),
    ("v3.21.0", [
        "AI史诗级加强：战术角色分配（前锋/侧翼/后卫）、玩家轨迹预测、动态包围圈（仅淘汰之王模式）",
    ]),
    ("v3.20.0", [
        "AI超级智能加强：预测玩家位置、动态绕前距离、智能分散包围、协同避免拥堵（仅淘汰之王模式）",
    ]),
    ("v3.19.0", [
        "完全无解：只有分数≥20的敌人数量超过20个时，它们才会团结攻击玩家（仅淘汰之王模式）；否则保持躲避",
        "UI增加狂暴敌人计数器",
    ]),
    ("v3.18.0", [
        "AI团结协作：多个AI会从左右两侧包抄玩家，形成包围（仅淘汰之王模式）",
    ]),
    ("v3.17.0", [
        "AI攻击分数阈值从15改为20",
        "淘汰之王模式敌人生成随机名字",
        "被淘汰时显示淘汰者名字和最终排名",
        "排行榜改为保存所有分数，便于计算排名",
    ]),
    ("v3.16.0", [
        "AI攻击绕前距离从5像素改为100像素",
    ]),
    ("v3.15.0", [
        "AI攻击速度提升3倍，绕前距离缩短至5像素（仅淘汰之王模式）",
    ]),
    ("v3.14.0", [
        "AI攻击加速：淘汰之王模式下分数≥15的AI移动速度提升1.5倍",
    ]),
    ("v3.13.0", [
        "AI行为模式分离：淘汰之王模式下AI会加速移动到玩家前方攻击，经典模式沿用原逻辑（追击其他敌人）",
    ]),
    ("v3.12.0", [
        "AI攻击方式改为绕到玩家前面，并且只攻击玩家",
    ]),
    ("v3.11.0", [
        "AI逻辑重写：分数<15躲避所有人，分数≥15追击其他AI，吃食物优先级最低",
        "经典模式持续生成敌人，淘汰之王模式不补充",
        "默认蛇身颜色改为深绿",
    ]),
    ("v3.10.2", [
        "排行榜优化：第一名显示“玩家”，其余显示“敌人”",
        "开始界面按钮悬停效果改为仅文字变灰",
    ]),
    ("v3.10.1", [
        "优化排行榜显示格式：1. 玩家 (分数)",
    ]),
    ("v3.10.0", [
        "淘汰之王模式敌人数量增至100",
    ]),
    ("v3.9.0", [
        "淘汰之王模式移除时间限制，敌人数量增至43",
        "经典模式敌人数量增至10",
    ]),
    ("v3.8.0", [
        "淘汰之王模式固定生成33名敌人",
    ]),
    ("v3.7.0", [
        "淘汰之王模式改为固定敌人数量，敌人死亡后不再重生",
        "开局所有敌人同时生成，存活到时间结束即为胜利",
    ]),
    ("v3.6.0", [
        "新增淘汰之王模式（限时生存，得分倍率递增）",
        "增加排行榜功能（仅限淘汰之王模式）",
    ]),
    ("v3.5.0", [
        "AI会躲避玩家，优先级比吃食物高",
    ]),
    ("v3.4.9", [
        "最低速度从0.5改回2",
    ]),
    ("v3.4.8", [
        "修复分数始终为0的bug",
        "结算界面改为灰色半透明窗口",
    ]),
    ("v3.4.7", [
        "添加结算界面，显示最终分数和操作选项",
        "游戏内UI颜色自适应背景（黑色背景白字，白色背景黑字）",
    ]),
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

def load_player_name():
    """从文件加载玩家名称，如果文件不存在返回None"""
    if os.path.exists(NAME_FILE):
        with open(NAME_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_player_name(name):
    """保存玩家名称到文件"""
    with open(NAME_FILE, "w", encoding="utf-8") as f:
        f.write(name)

# ========== 初始化 Pygame ==========
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"自由贪吃蛇 (PVE) {VERSION}")
clock = pygame.time.Clock()
FPS = 60

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
LIGHT_GRAY_BG = (240, 240, 240)

# 开始界面背景色
START_BG = (192, 255, 240)

# 游戏配置
WORLD_WIDTH, WORLD_HEIGHT = 5000, 4000
WORLD_MIN_X = -WORLD_WIDTH // 2
WORLD_MAX_X = WORLD_WIDTH // 2
WORLD_MIN_Y = -WORLD_HEIGHT // 2
WORLD_MAX_Y = WORLD_HEIGHT // 2

BASE_SPEED = 4.5
MIN_SPEED = 2
SPEED_DECAY = 0.016
BASE_SEGMENT_RADIUS = 8
FOOD_RADIUS = 6
LARGE_FOOD_RADIUS = 10
FOOD_COUNT = 125
BOOST_DURATION = 5.0
BOOST_MULTIPLIER = 2.0
ENEMY_COUNT = 10
TIMED_ENEMY_COUNT = 100
FOOD_PER_SEGMENT = 3
ENEMY_FOOD_SEEK_PROB = 0.8
GRID_SIZE = 40

MAX_SEGMENT_RADIUS = 20
RADIUS_PER_SCORE = 0.02

FOOD_COLORS = [RED, ORANGE, YELLOW, PINK, PURPLE, CYAN, (0, 255, 0)]

# 蛇颜色选项
HEAD_COLOR_OPTIONS = [LIGHT_GREEN, YELLOW, ORANGE, PINK, CYAN, WHITE]
HEAD_COLOR_NAMES = ["浅绿", "黄", "橙", "粉", "青", "白"]
BODY_COLOR_OPTIONS = [GREEN, DARK_GREEN, BLUE, PURPLE, BROWN, GRAY]
BODY_COLOR_NAMES = ["绿", "深绿", "蓝", "紫", "棕", "灰"]

DEFAULT_HEAD_COLOR = LIGHT_GREEN
DEFAULT_BODY_COLOR = DARK_GREEN

# 背景样式选项
BACKGROUND_STYLE_OPTIONS = ["纯黑", "纯白", "格子", "星空"]
BACKGROUND_STYLE_VALUES = [BLACK, WHITE, "grid", "stars"]
DEFAULT_BACKGROUND_STYLE = 2

# 按钮尺寸
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 44
BUTTON_HALF_WIDTH = BUTTON_WIDTH // 2
BUTTON_HALF_HEIGHT = BUTTON_HEIGHT // 2
BUTTON_Y_POS = [45, -5, -55]

# 模式按钮Y坐标
MODE_BUTTON_Y = 94

# 暂停菜单选项
PAUSE_OPTIONS = ["重新开始", "返回开始界面", "退出游戏"]

# 结算菜单选项
GAMEOVER_OPTIONS = ["重新开始", "返回开始界面"]

# 返回按钮文字位置
BACK_BUTTON_POS = (30, 30)

# 排行榜文件
HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "timed_scores.json")

# 敌人名字列表
ENEMY_NAMES = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi",
    "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega",
    "Ares", "Atlas", "Cronus", "Hades", "Helios", "Hercules", "Hermes",
    "Hyperion", "Iapetus", "Oceanus", "Pallas", "Perses", "Prometheus"
]

# ========== 玩家名称 ==========
player_name = load_player_name()
if player_name is None:
    player_name = "玩家"

# ========== 玩家轨迹记录 ==========
player_pos_history = deque(maxlen=60)
player_dir_history = deque(maxlen=60)

# ========== 改进的字体加载函数（优先使用目录下的 microsoft-yahei.ttf） ==========
def get_font(size):
    # 优先尝试加载游戏目录下的 microsoft-yahei.ttf
    local_font_path = os.path.join(os.path.dirname(__file__), "microsoft-yahei.ttf")
    if os.path.exists(local_font_path):
        try:
            return pygame.font.Font(local_font_path, size)
        except:
            pass

    # 尝试系统字体中的微软雅黑
    font_names = [
        "Microsoft YaHei",
        "Microsoft YaHei UI",
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

    # 最后回退：使用系统默认字体（可能不支持中文）
    print("警告：未找到中文字体，中文可能无法正常显示。请将 microsoft-yahei.ttf 放在游戏目录下。")
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
gameover_screen = False
pause_selection = 0
gameover_selection = 0
boosting = False
boost_start_time = 0

color_centers = {}

mouse_x, mouse_y = 0, 0
mouse_pressed = False

background_style = DEFAULT_BACKGROUND_STYLE
head_color_index = 0
body_color_index = 0
selected_setting = 0

hover_button = None
mode_hover = False
setting_option_rects = []
back_button_hover = False

game_mode = "classic"  # "classic", "timed", "mojin"（搜打撤）

# 搜打撤模式参数
MOJIN_PHASE = "search"  # search, strike, withdraw
MOJIN_TIMER = 0
MOJIN_PHASE_DURATION = 300  # 帧数，约5秒（60fps）
MOJIN_SEARCH_SPEED = 0.8    # 搜索阶段速度系数
MOJIN_STRIKE_SPEED = 2.0    # 打击阶段速度系数
MOJIN_WITHDRAW_SPEED = 1.5  # 撤离阶段速度系数

# 全局攻击状态（仅淘汰之王模式）
global_attack_phase = False
attack_trigger_count = 15

# 实用功能标志
show_fps = True

# 障碍物和容器
obstacles = []          # 障碍物列表，每个元素为 (x, y, radius)
containers = []         # 容器列表，每个元素为 (x, y, radius, reward_type, reward_value)
CONTAINER_RADIUS = 10
OBSTACLE_RADIUS = 12
CONTAINER_COUNT = 30
OBSTACLE_COUNT = 20

# 容器奖励类型
REWARD_SCORE = 1        # 增加分数
REWARD_FOOD = 2         # 生成食物
REWARD_BOOST = 3        # 临时加速

# 临时加速效果变量
temp_boost_remaining = 0  # 剩余帧数

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
            # 检查与障碍物和容器的碰撞
            for ox, oy, orad in obstacles:
                if (fx - ox) ** 2 + (fy - oy) ** 2 < (orad + radius) ** 2:
                    overlap = True
                    break
            if not overlap:
                for cx, cy, cr, _, _ in containers:
                    if (fx - cx) ** 2 + (fy - cy) ** 2 < (cr + radius) ** 2:
                        overlap = True
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
    if temp_boost_remaining > 0:
        base *= 1.5
    if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
        base *= BOOST_MULTIPLIER
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
                # 检查障碍物和容器
                for ox, oy, orad in obstacles:
                    if (fx - ox) ** 2 + (fy - oy) ** 2 < (orad + LARGE_FOOD_RADIUS) ** 2:
                        overlap = True
                        break
                if not overlap:
                    for cx, cy, cr, _, _ in containers:
                        if (fx - cx) ** 2 + (fy - cy) ** 2 < (cr + LARGE_FOOD_RADIUS) ** 2:
                            overlap = True
                            break
                if not overlap:
                    foods.append((fx, fy, RED, LARGE_FOOD_RADIUS))
                    break
            else:
                pos = random_position()
                foods.append((pos[0], pos[1], RED, LARGE_FOOD_RADIUS))

def predict_player_position():
    if len(player_pos_history) < 5:
        return snake[0]
    avg_dx = 0
    avg_dy = 0
    for i in range(len(player_dir_history) - 1):
        avg_dx += player_dir_history[i][0]
        avg_dy += player_dir_history[i][1]
    if len(player_dir_history) > 0:
        avg_dx /= len(player_dir_history)
        avg_dy /= len(player_dir_history)
        length = math.hypot(avg_dx, avg_dy)
        if length > 0:
            avg_dx /= length
            avg_dy /= length
    player_speed = get_current_speed()
    predict_time = 1.0
    predicted_x = snake[0][0] + avg_dx * player_speed * predict_time
    predicted_y = snake[0][1] + avg_dy * player_speed * predict_time
    return (predicted_x, predicted_y)

def direction_will_collide(head, dir_vec, all_segments, radius, check_dist=60):
    """检查沿给定方向移动check_dist距离是否会与任何蛇身、障碍物或容器碰撞"""
    check_x = head[0] + dir_vec[0] * check_dist
    check_y = head[1] + dir_vec[1] * check_dist
    threshold_sq = (radius * 2) ** 2
    # 蛇身碰撞
    for sx, sy in all_segments:
        if (check_x - sx) ** 2 + (check_y - sy) ** 2 < threshold_sq:
            return True
    # 障碍物碰撞
    for ox, oy, orad in obstacles:
        if (check_x - ox) ** 2 + (check_y - oy) ** 2 < (orad + radius) ** 2:
            return True
    # 容器碰撞（容器可以穿越，不视为碰撞阻挡）
    return False

def will_collide_with_player(head, dir_vec, radius, check_dist=30):
    """检查是否会与玩家身体碰撞"""
    check_x = head[0] + dir_vec[0] * check_dist
    check_y = head[1] + dir_vec[1] * check_dist
    threshold_sq = (radius * 2) ** 2
    for sx, sy in snake:
        if (check_x - sx) ** 2 + (check_y - sy) ** 2 < threshold_sq:
            return True
    return False

def get_evade_direction(head, all_segments, old_dir, radius):
    """计算躲避方向（基于排斥）"""
    repulsion = [0.0, 0.0]
    # 躲避蛇身
    for sx, sy in all_segments:
        dx = head[0] - sx
        dy = head[1] - sy
        dist_sq = dx*dx + dy*dy
        if dist_sq < (radius * 4) ** 2 and dist_sq > 0:
            force = 1.0 / (dist_sq + 1e-6)
            length = math.sqrt(dist_sq)
            norm_dx = dx / length
            norm_dy = dy / length
            repulsion[0] += norm_dx * force
            repulsion[1] += norm_dy * force
    # 躲避障碍物
    for ox, oy, orad in obstacles:
        dx = head[0] - ox
        dy = head[1] - oy
        dist_sq = dx*dx + dy*dy
        if dist_sq < (radius + orad + 20) ** 2 and dist_sq > 0:
            force = 1.0 / (dist_sq + 1e-6)
            length = math.sqrt(dist_sq)
            norm_dx = dx / length
            norm_dy = dy / length
            repulsion[0] += norm_dx * force
            repulsion[1] += norm_dy * force
    rep_length = math.hypot(repulsion[0], repulsion[1])
    if rep_length > 1e-6:
        new_dir = (repulsion[0] / rep_length, repulsion[1] / rep_length)
        if not (new_dir[0] == -old_dir[0] and new_dir[1] == -old_dir[1]):
            return new_dir
    return None

def get_enemy_new_direction(enemy, foods_list):
    """
    根据游戏模式决定行为：
    - 淘汰之王模式：AI 状态机（躲避、准备、攻击），10种攻击策略，协同攻击。
    - 搜打撤模式：三段式战术（搜索、打击、撤离），搜索阶段优先寻找容器。
    - 经典模式：保持原逻辑。
    """
    old_dir = enemy['dir']
    head = enemy['body'][0]
    enemy_score = enemy['score']

    # 获取所有其他蛇的身体段（玩家 + 其他敌人，排除自己）
    all_segments = []
    for seg in snake:
        all_segments.append(seg)
    for other in enemies:
        if other is enemy:
            continue
        for seg in other['body']:
            all_segments.append(seg)

    radius = get_segment_radius()

    # 首先，最高优先级：避免撞到玩家身体（所有模式通用）
    if will_collide_with_player(head, old_dir, radius, check_dist=30):
        evade = get_evade_direction(head, all_segments, old_dir, radius)
        if evade is not None:
            return evade

    # ========== 淘汰之王模式 ==========
    if game_mode == "timed":
        # 获取高分敌人数量
        high_score_count = sum(1 for e in enemies if e['score'] >= 20)

        # 决定当前AI的状态（使用敌人字段中的 'state'，默认为 'idle'）
        if 'state' not in enemy:
            enemy['state'] = 'idle'

        # 全局攻击阶段判定
        global global_attack_phase
        if not global_attack_phase and high_score_count >= attack_trigger_count:
            global_attack_phase = True
            for e in enemies:
                if e['score'] >= 20:
                    e['state'] = 'preparing'

        # 根据状态处理
        if enemy_score < 20:
            # 低分敌人始终躲避
            evade = get_evade_direction(head, all_segments, old_dir, radius)
            if evade is not None:
                return evade
        else:
            # 高分敌人
            if enemy['state'] == 'idle':
                evade = get_evade_direction(head, all_segments, old_dir, radius)
                if evade is not None:
                    return evade
            elif enemy['state'] == 'preparing':
                # 准备阶段：缓慢靠近玩家
                player_head = snake[0]
                dx = player_head[0] - head[0]
                dy = player_head[1] - head[1]
                length = math.hypot(dx, dy)
                if length > 1e-6:
                    desired_dir = (dx / length, dy / length)
                    if direction_will_collide(head, desired_dir, all_segments, radius):
                        evade = get_evade_direction(head, all_segments, old_dir, radius)
                        if evade is not None:
                            return evade
                    if not (desired_dir[0] == -old_dir[0] and desired_dir[1] == -old_dir[1]):
                        return desired_dir
            elif enemy['state'] == 'attacking':
                # 攻击阶段：采用10种策略之一
                name_hash = int(hashlib.md5(enemy['name'].encode()).hexdigest(), 16)
                tactic = name_hash % 10

                player_head = snake[0]
                player_dir = direction
                player_speed = get_current_speed()
                predicted_player = predict_player_position()

                # 基础绕前距离
                base_ahead_dist = 150 + player_speed * 15

                # 初始化目标点
                target_x, target_y = player_head

                if tactic == 0:  # 前锋
                    ahead_dist = base_ahead_dist
                    target_x = predicted_player[0] + player_dir[0] * ahead_dist
                    target_y = predicted_player[1] + player_dir[1] * ahead_dist
                elif tactic == 1:  # 侧翼左
                    perp_x = -player_dir[1]
                    perp_y = player_dir[0]
                    offset = 200
                    ahead_dist = base_ahead_dist * 0.8
                    base_target = (predicted_player[0] + player_dir[0] * ahead_dist,
                                   predicted_player[1] + player_dir[1] * ahead_dist)
                    target_x = base_target[0] + perp_x * offset
                    target_y = base_target[1] + perp_y * offset
                elif tactic == 2:  # 侧翼右
                    perp_x = -player_dir[1]
                    perp_y = player_dir[0]
                    offset = -200
                    ahead_dist = base_ahead_dist * 0.8
                    base_target = (predicted_player[0] + player_dir[0] * ahead_dist,
                                   predicted_player[1] + player_dir[1] * ahead_dist)
                    target_x = base_target[0] + perp_x * offset
                    target_y = base_target[1] + perp_y * offset
                elif tactic == 3:  # 后卫
                    behind_dist = 200
                    target_x = predicted_player[0] - player_dir[0] * behind_dist
                    target_y = predicted_player[1] - player_dir[1] * behind_dist
                elif tactic == 4:  # 诱饵
                    away_dist = 250
                    target_x = player_head[0] - player_dir[0] * away_dist
                    target_y = player_head[1] - player_dir[1] * away_dist
                elif tactic == 5:  # 协同夹击
                    perp_x = -player_dir[1]
                    perp_y = player_dir[0]
                    t = (name_hash % 1000) / 500.0 - 1.0
                    offset = t * 250
                    ahead_dist = base_ahead_dist * 0.7
                    base_target = (predicted_player[0] + player_dir[0] * ahead_dist,
                                   predicted_player[1] + player_dir[1] * ahead_dist)
                    target_x = base_target[0] + perp_x * offset
                    target_y = base_target[1] + perp_y * offset
                elif tactic == 6:  # 扇形包围
                    spread = 250
                    angle = (name_hash % 100) / 100.0 * math.pi * 2
                    offset_x = math.cos(angle) * spread
                    offset_y = math.sin(angle) * spread
                    ahead_dist = base_ahead_dist
                    base_target = (predicted_player[0] + player_dir[0] * ahead_dist,
                                   predicted_player[1] + player_dir[1] * ahead_dist)
                    target_x = base_target[0] + offset_x
                    target_y = base_target[1] + offset_y
                elif tactic == 7:  # 等待
                    wait_dist = 300
                    target_x = predicted_player[0] + player_dir[0] * wait_dist
                    target_y = predicted_player[1] + player_dir[1] * wait_dist
                elif tactic == 8:  # 利用障碍
                    ahead_dist = base_ahead_dist
                    base_target = (predicted_player[0] + player_dir[0] * ahead_dist,
                                   predicted_player[1] + player_dir[1] * ahead_dist)
                    jitter = (name_hash % 200) - 100
                    perp_x = -player_dir[1]
                    perp_y = player_dir[0]
                    target_x = base_target[0] + perp_x * jitter
                    target_y = base_target[1] + perp_y * jitter
                else:  # 9: 假动作
                    ahead_dist = base_ahead_dist
                    target_x = predicted_player[0] + player_dir[0] * ahead_dist
                    target_y = predicted_player[1] + player_dir[1] * ahead_dist

                dx = target_x - head[0]
                dy = target_y - head[1]
                length = math.hypot(dx, dy)
                if length > 1e-6:
                    desired_dir = (dx / length, dy / length)

                    if will_collide_with_player(head, desired_dir, radius, check_dist=30):
                        evade = get_evade_direction(head, all_segments, old_dir, radius)
                        if evade is not None:
                            return evade

                    if direction_will_collide(head, desired_dir, all_segments, radius):
                        best_dir = None
                        best_dot = -float('inf')
                        for angle_offset in [-1.2, -0.9, -0.6, -0.3, 0.3, 0.6, 0.9, 1.2]:
                            cos_a = math.cos(angle_offset)
                            sin_a = math.sin(angle_offset)
                            test_x = desired_dir[0] * cos_a - desired_dir[1] * sin_a
                            test_y = desired_dir[0] * sin_a + desired_dir[1] * cos_a
                            test_dir = (test_x, test_y)
                            if test_dir[0] == -old_dir[0] and test_dir[1] == -old_dir[1]:
                                continue
                            if not direction_will_collide(head, test_dir, all_segments, radius):
                                dot = test_dir[0] * desired_dir[0] + test_dir[1] * desired_dir[1]
                                if dot > best_dot:
                                    best_dot = dot
                                    best_dir = test_dir
                        if best_dir is not None:
                            return best_dir
                    else:
                        if not (desired_dir[0] == -old_dir[0] and desired_dir[1] == -old_dir[1]):
                            return desired_dir

    # ========== 搜打撤模式（新增容器搜索） ==========
    elif game_mode == "mojin":
        global MOJIN_PHASE, MOJIN_TIMER
        MOJIN_TIMER += 1
        if MOJIN_TIMER >= MOJIN_PHASE_DURATION:
            MOJIN_TIMER = 0
            # 阶段循环：search -> strike -> withdraw -> search
            if MOJIN_PHASE == "search":
                MOJIN_PHASE = "strike"
            elif MOJIN_PHASE == "strike":
                MOJIN_PHASE = "withdraw"
            else:
                MOJIN_PHASE = "search"

        player_head = snake[0]
        player_dir = direction
        player_speed = get_current_speed()
        predicted_player = predict_player_position()

        # 根据阶段决定目标
        if MOJIN_PHASE == "search":
            # 搜索阶段：优先寻找最近的容器，如果没有容器则随机探索
            if containers:
                # 找到最近的容器
                min_dist = float('inf')
                nearest_container = None
                for cx, cy, cr, _, _ in containers:
                    dist = (head[0] - cx) ** 2 + (head[1] - cy) ** 2
                    if dist < min_dist:
                        min_dist = dist
                        nearest_container = (cx, cy)
                if nearest_container:
                    target_x, target_y = nearest_container
                else:
                    # 没有容器，随机探索
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(100, 300)
                    target_x = player_head[0] + math.cos(angle) * radius
                    target_y = player_head[1] + math.sin(angle) * radius
            else:
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(100, 300)
                target_x = player_head[0] + math.cos(angle) * radius
                target_y = player_head[1] + math.sin(angle) * radius
            # 限制在世界范围内
            target_x = max(WORLD_MIN_X + 50, min(WORLD_MAX_X - 50, target_x))
            target_y = max(WORLD_MIN_Y + 50, min(WORLD_MAX_Y - 50, target_y))
        elif MOJIN_PHASE == "strike":
            # 打击阶段：全力攻击玩家预测位置前方
            ahead_dist = 100 + player_speed * 10
            target_x = predicted_player[0] + player_dir[0] * ahead_dist
            target_y = predicted_player[1] + player_dir[1] * ahead_dist
        else:  # withdraw
            # 撤离阶段：远离玩家，向地图边界移动
            dx = head[0] - player_head[0]
            dy = head[1] - player_head[1]
            length = math.hypot(dx, dy)
            if length > 0:
                target_x = head[0] + (dx / length) * 500
                target_y = head[1] + (dy / length) * 500
            else:
                target_x = head[0] + random.choice([-500, 500])
                target_y = head[1] + random.choice([-500, 500])
            target_x = max(WORLD_MIN_X + 50, min(WORLD_MAX_X - 50, target_x))
            target_y = max(WORLD_MIN_Y + 50, min(WORLD_MAX_Y - 50, target_y))

        dx = target_x - head[0]
        dy = target_y - head[1]
        length = math.hypot(dx, dy)
        if length > 1e-6:
            desired_dir = (dx / length, dy / length)

            # 碰撞检测与绕行
            if direction_will_collide(head, desired_dir, all_segments, radius):
                best_dir = None
                best_dot = -float('inf')
                for angle_offset in [-0.8, -0.4, 0.4, 0.8]:
                    cos_a = math.cos(angle_offset)
                    sin_a = math.sin(angle_offset)
                    test_x = desired_dir[0] * cos_a - desired_dir[1] * sin_a
                    test_y = desired_dir[0] * sin_a + desired_dir[1] * cos_a
                    test_dir = (test_x, test_y)
                    if test_dir[0] == -old_dir[0] and test_dir[1] == -old_dir[1]:
                        continue
                    if not direction_will_collide(head, test_dir, all_segments, radius):
                        dot = test_dir[0] * desired_dir[0] + test_dir[1] * desired_dir[1]
                        if dot > best_dot:
                            best_dot = dot
                            best_dir = test_dir
                if best_dir is not None:
                    return best_dir
            else:
                if not (desired_dir[0] == -old_dir[0] and desired_dir[1] == -old_dir[1]):
                    return desired_dir

    # ========== 经典模式 ==========
    else:
        avoid_threshold_sq = (radius * 4) ** 2
        if enemy_score < 15:
            repulsion = [0.0, 0.0]
            for sx, sy in all_segments:
                dx = head[0] - sx
                dy = head[1] - sy
                dist_sq = dx*dx + dy*dy
                if dist_sq < avoid_threshold_sq and dist_sq > 0:
                    force = 1.0 / (dist_sq + 1e-6)
                    length = math.sqrt(dist_sq)
                    norm_dx = dx / length
                    norm_dy = dy / length
                    repulsion[0] += norm_dx * force
                    repulsion[1] += norm_dy * force
            rep_length = math.hypot(repulsion[0], repulsion[1])
            if rep_length > 1e-6:
                new_dir = (repulsion[0] / rep_length, repulsion[1] / rep_length)
                if not (new_dir[0] == -old_dir[0] and new_dir[1] == -old_dir[1]):
                    return new_dir
        else:
            # 追击最近的敌人
            target_enemy = None
            min_dist_sq = float('inf')
            for other in enemies:
                if other is enemy:
                    continue
                other_head = other['body'][0]
                dx = other_head[0] - head[0]
                dy = other_head[1] - head[1]
                dist_sq = dx*dx + dy*dy
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    target_enemy = other
            if target_enemy is not None:
                target_head = target_enemy['body'][0]
                target_dir = target_enemy['dir']
                ahead_dist = 50
                target_ahead = (target_head[0] + target_dir[0] * ahead_dist,
                                target_head[1] + target_dir[1] * ahead_dist)
                dx = target_ahead[0] - head[0]
                dy = target_ahead[1] - head[1]
                length = math.hypot(dx, dy)
                if length > 1e-6:
                    new_dir = (dx / length, dy / length)
                    if not (new_dir[0] == -old_dir[0] and new_dir[1] == -old_dir[1]):
                        return new_dir
                dx = target_head[0] - head[0]
                dy = target_head[1] - head[1]
                length = math.hypot(dx, dy)
                if length > 1e-6:
                    new_dir = (dx / length, dy / length)
                    if not (new_dir[0] == -old_dir[0] and new_dir[1] == -old_dir[1]):
                        return new_dir

    # 尝试吃食物（所有模式通用）
    if foods_list and random.random() < ENEMY_FOOD_SEEK_PROB:
        min_dist_sq = float('inf')
        target_food = None
        for fx, fy, _, _ in foods_list:
            d_sq = (head[0] - fx) ** 2 + (head[1] - fy) ** 2
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                target_food = (fx, fy)
        if target_food:
            dx = target_food[0] - head[0]
            dy = target_food[1] - head[1]
            length = math.hypot(dx, dy)
            if length > 1e-6:
                new_dir = (dx / length, dy / length)
                if not (new_dir[0] == -old_dir[0] and new_dir[1] == -old_dir[1]):
                    return new_dir

    # 随机方向
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

# ========== 生成障碍物和容器（修复版） ==========
def generate_obstacles_and_containers():
    """在地图中生成障碍物和可搜索容器，确保有足够空间"""
    global obstacles, containers
    obstacles.clear()
    containers.clear()

    # 辅助函数：检查位置是否与已有元素重叠
    def is_overlap(x, y, radius, existing_list, exclude_self=False):
        for (ox, oy, orad) in existing_list:
            if (x - ox) ** 2 + (y - oy) ** 2 < (radius + orad) ** 2:
                return True
        return False

    # 生成障碍物
    for _ in range(OBSTACLE_COUNT):
        placed = False
        for attempt in range(200):  # 增加尝试次数
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            # 避免与蛇重叠
            overlap = False
            for sx, sy in snake:
                if (x - sx) ** 2 + (y - sy) ** 2 < (OBSTACLE_RADIUS + get_segment_radius()) ** 2:
                    overlap = True
                    break
            if overlap:
                continue
            # 避免与敌人重叠
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if (x - sx) ** 2 + (y - sy) ** 2 < (OBSTACLE_RADIUS + get_segment_radius()) ** 2:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            # 避免与其他障碍物重叠
            if is_overlap(x, y, OBSTACLE_RADIUS, obstacles):
                continue
            # 避免与现有容器重叠（防止生成时重叠）
            if is_overlap(x, y, OBSTACLE_RADIUS, containers):
                continue
            obstacles.append((x, y, OBSTACLE_RADIUS))
            placed = True
            break
        if not placed:
            # 如果实在找不到位置，随机放置在角落
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            obstacles.append((x, y, OBSTACLE_RADIUS))

    # 生成容器
    for _ in range(CONTAINER_COUNT):
        placed = False
        for attempt in range(200):
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            # 避免与蛇重叠
            overlap = False
            for sx, sy in snake:
                if (x - sx) ** 2 + (y - sy) ** 2 < (CONTAINER_RADIUS + get_segment_radius()) ** 2:
                    overlap = True
                    break
            if overlap:
                continue
            # 避免与敌人重叠
            for enemy in enemies:
                for sx, sy in enemy['body']:
                    if (x - sx) ** 2 + (y - sy) ** 2 < (CONTAINER_RADIUS + get_segment_radius()) ** 2:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            # 避免与障碍物重叠
            if is_overlap(x, y, CONTAINER_RADIUS, obstacles):
                continue
            # 避免与其他容器重叠
            if is_overlap(x, y, CONTAINER_RADIUS, containers):
                continue
            reward_type = random.choice([REWARD_SCORE, REWARD_FOOD, REWARD_BOOST])
            reward_value = 1 if reward_type == REWARD_SCORE else (random.randint(1, 3) if reward_type == REWARD_FOOD else 120)
            containers.append((x, y, CONTAINER_RADIUS, reward_type, reward_value))
            placed = True
            break
        if not placed:
            # 如果实在找不到位置，随机放置
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            containers.append((x, y, CONTAINER_RADIUS, REWARD_SCORE, 1))

# ========== 处理容器搜索 ==========
def handle_container_collision(segment):
    """检查蛇头或AI头部是否碰到容器，并处理奖励"""
    global score, foods, temp_boost_remaining
    head = segment
    for i, (cx, cy, cr, reward_type, reward_val) in enumerate(containers):
        if (head[0] - cx) ** 2 + (head[1] - cy) ** 2 < (cr + get_segment_radius()) ** 2:
            # 移除容器
            del containers[i]
            # 根据奖励类型给予效果
            if reward_type == REWARD_SCORE:
                score += reward_val
                # 显示加分特效（可选）
            elif reward_type == REWARD_FOOD:
                for _ in range(reward_val):
                    # 生成额外食物
                    new_food = create_food(random.choice(FOOD_COLORS), FOOD_RADIUS)
                    if new_food:
                        foods.append(new_food)
            elif reward_type == REWARD_BOOST:
                temp_boost_remaining = reward_val
            return True
    return False

# ========== 绘制函数 ==========
def draw_circle(x, y, color, radius):
    """直接绘制圆到screen"""
    sx, sy = world_to_screen(x, y)
    pygame.draw.circle(screen, color, (sx, sy), radius)

def draw_background():
    """绘制背景（直接到screen）"""
    bg_value = BACKGROUND_STYLE_VALUES[background_style]
    if bg_value == BLACK:
        screen.fill(BLACK)
    elif bg_value == WHITE:
        screen.fill(WHITE)
    elif bg_value == "grid":
        screen.fill(WHITE)
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
    elif bg_value == "stars":
        screen.fill(BLACK)
        for _ in range(100):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, HEIGHT)
            brightness = random.randint(100, 255)
            screen.set_at((sx, sy), (brightness, brightness, brightness))

# ========== 排行榜相关函数 ==========
def load_scores():
    if not os.path.exists(HIGHSCORE_FILE):
        return []
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except:
        return []

def save_scores(scores):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except:
        pass

def add_score(name, score_value):
    scores = load_scores()
    scores.append([name, score_value])
    scores.sort(key=lambda x: x[1], reverse=True)
    save_scores(scores)

def get_rank(score_value):
    scores = load_scores()
    scores.sort(key=lambda x: x[1], reverse=True)
    for i, (_, s) in enumerate(scores):
        if s <= score_value:
            return i + 1
    return len(scores) + 1

def get_current_rank():
    all_scores = [score] + [e['score'] for e in enemies]
    all_scores.sort(reverse=True)
    for i, s in enumerate(all_scores):
        if s == score:
            return i + 1
    return 1

def get_sorted_rankings():
    rankings = [(player_name, score)] + [(e['name'], e['score']) for e in enemies]
    rankings.sort(key=lambda x: x[1], reverse=True)
    return rankings

def show_rankings():
    font_title = get_font(48)
    font_entry = get_font(24)
    font_button = get_font(24)

    title = font_title.render("淘汰之王历史排行榜", True, BLACK)
    back_button_text = "返回 (ESC)"

    button_rect = pygame.Rect(WIDTH//2 - BUTTON_HALF_WIDTH, HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)

    all_scores = load_scores()
    top10 = all_scores[:10]
    while len(top10) < 10:
        top10.append(["---", 0])

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
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    waiting = False

        screen.fill(START_BG)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        y = 200
        for i, (name, score_val) in enumerate(top10):
            if name == "---":
                line = f"{i+1}.  ---"
            else:
                line = f"{i+1}. {name} ({score_val})"
            rendered = font_entry.render(line, True, BLACK)
            screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, y))
            y += 35
        pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
        pygame.draw.rect(screen, GRAY, button_rect, 2)
        btn_text = font_button.render(back_button_text, True, BLACK)
        screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))
        pygame.display.flip()
        clock.tick(FPS)

# ========== 首次启动名称输入界面 ==========
def show_name_input_screen():
    font_title = get_font(48)
    font_prompt = get_font(24)
    font_input = get_font(24)
    font_button = get_font(24)

    title = font_title.render("欢迎来到自由贪吃蛇", True, BLACK)
    prompt = font_prompt.render("请输入你的名字 (最多20字符):", True, BLACK)
    button_text = "确认 (Enter)"

    input_text = ""
    input_active = True
    waiting = True

    button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 50)

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip():
                            name = input_text.strip()
                        else:
                            name = "玩家"
                        return name
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if event.unicode.isprintable() and len(input_text) < 20:
                            input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    if input_text.strip():
                        name = input_text.strip()
                    else:
                        name = "玩家"
                    return name

        screen.fill(START_BG)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 300))

        input_box_rect = pygame.Rect(WIDTH//2 - 200, 350, 400, 50)
        pygame.draw.rect(screen, WHITE, input_box_rect)
        pygame.draw.rect(screen, BLACK, input_box_rect, 2)

        text_surface = font_input.render(input_text, True, BLACK)
        screen.blit(text_surface, (input_box_rect.x + 10, input_box_rect.y + 10))

        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = input_box_rect.x + 10 + text_surface.get_width()
            pygame.draw.line(screen, BLACK, (cursor_x, input_box_rect.y + 5),
                             (cursor_x, input_box_rect.y + input_box_rect.height - 5), 2)

        pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
        pygame.draw.rect(screen, GRAY, button_rect, 2)
        btn_surface = font_button.render(button_text, True, BLACK)
        screen.blit(btn_surface, (button_rect.centerx - btn_surface.get_width()//2,
                                   button_rect.centery - btn_surface.get_height()//2))
        pygame.display.flip()
        clock.tick(FPS)

# ========== 其他窗口函数 ==========
def show_full_changelog():
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

        screen.fill(START_BG)
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
            scroll_hint = font_content.render(f"第 {scroll_offset+1}-{end_idx} 行 / 共 {total_lines} 行", True, DARK_GRAY)
            screen.blit(scroll_hint, (WIDTH//2 - scroll_hint.get_width()//2, HEIGHT - 150))

        pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
        pygame.draw.rect(screen, GRAY, button_rect, 2)
        btn_text = font_button.render(back_button_text, True, BLACK)
        screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))
        pygame.display.flip()
        clock.tick(FPS)

def show_credits():
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
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    waiting = False

        screen.fill(START_BG)
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
                if event.button == 1 and button_rect.collidepoint(event.pos):
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

# ========== 主绘制函数 ==========
def draw():
    global setting_option_rects, back_button_hover, mode_hover, gameover_killer_name

    # ========== 设置界面 ==========
    if settings_mode:
        screen.fill(START_BG)
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

    # ========== 开始界面 ==========
    elif not game_started:
        screen.fill(START_BG)
        font_title = get_font(48)
        font_small = get_font(18)

        title = font_title.render(f"自由贪吃蛇 {VERSION}", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        # 模式按钮
        mode_font = get_font(24)
        if game_mode == "timed":
            mode_text = "模式: 淘汰之王  (M键切换)"
            mode_color = YELLOW
        elif game_mode == "mojin":
            mode_text = "模式: 搜打撤  (M键切换)"
            mode_color = ORANGE
        else:
            mode_text = "模式: 经典  (M键切换)"
            mode_color = BLACK
        mode_rendered = mode_font.render(mode_text, True, mode_color)
        mode_rect = pygame.Rect(WIDTH//2 - mode_rendered.get_width()//2 - 10,
                                HEIGHT//2 + MODE_BUTTON_Y - mode_rendered.get_height()//2 - 10,
                                mode_rendered.get_width() + 20, mode_rendered.get_height() + 20)
        mode_hover = mode_rect.collidepoint(mouse_x, mouse_y)
        if mode_hover:
            mode_color = GRAY
            mode_rendered = mode_font.render(mode_text, True, mode_color)
        screen.blit(mode_rendered, (WIDTH//2 - mode_rendered.get_width()//2, HEIGHT//2 + MODE_BUTTON_Y))

        # 主按钮
        button_texts = ["开始游戏 (SPACE)", "设置 (S)", "退出 (Q)"]
        button_fonts = [get_font(24), get_font(18), get_font(18)]
        for i, (y, text) in enumerate(zip(BUTTON_Y_POS, button_texts)):
            screen_y = HEIGHT//2 + y
            if hover_button == i:
                text_color = GRAY
            else:
                text_color = BLACK
            rendered = button_fonts[i].render(text, True, text_color)
            screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, screen_y - rendered.get_height()//2 - 2))

        hint_text = "按 H 查看历史排行榜"
        hint_rendered = font_small.render(hint_text, True, DARK_GRAY)
        screen.blit(hint_rendered, (WIDTH//2 - hint_rendered.get_width()//2, HEIGHT - 80))

    # ========== 游戏进行中 ==========
    else:
        # 绘制背景
        draw_background()

        # 绘制障碍物
        for ox, oy, orad in obstacles:
            draw_circle(ox, oy, BROWN, orad)

        # 绘制容器
        for cx, cy, cr, reward_type, _ in containers:
            if reward_type == REWARD_SCORE:
                color = (255, 215, 0)  # 金色
            elif reward_type == REWARD_FOOD:
                color = (0, 255, 0)    # 绿色
            else:
                color = (0, 255, 255)  # 青色
            draw_circle(cx, cy, color, cr)

        # 绘制游戏元素
        head_color = HEAD_COLOR_OPTIONS[head_color_index]
        body_color = BODY_COLOR_OPTIONS[body_color_index]
        current_radius = get_segment_radius()

        # 绘制蛇
        for i, (x, y) in enumerate(snake):
            color = head_color if i == 0 else body_color
            draw_circle(x, y, color, current_radius)

        # 绘制敌人
        for enemy in enemies:
            for i, (x, y) in enumerate(enemy['body']):
                color = RED if i == 0 else DARK_RED
                draw_circle(x, y, color, current_radius)

        # 绘制食物
        for fx, fy, fcolor, fr in foods:
            draw_circle(fx, fy, fcolor, fr)

        # 绘制世界边界
        left, bottom = world_to_screen(WORLD_MIN_X + current_radius, WORLD_MIN_Y + current_radius)
        right, top = world_to_screen(WORLD_MAX_X - current_radius, WORLD_MAX_Y - current_radius)
        pygame.draw.rect(screen, RED, (left, bottom, right - left, top - bottom), 2)

        # 确定文字颜色（根据背景）
        bg_value = BACKGROUND_STYLE_VALUES[background_style]
        if bg_value == BLACK:
            text_color = WHITE
        else:
            text_color = BLACK

        font_info = get_font(16)
        font_small = get_font(12)

        # 分数
        score_text = font_info.render(f"Score: {score}", True, text_color)
        screen.blit(score_text, (WIDTH - 200, 30))

        # 速度
        speed_val = get_current_speed()
        speed_text = f"Speed: {speed_val:.1f}"
        if boosting and (time.time() - boost_start_time) < BOOST_DURATION:
            remaining = BOOST_DURATION - (time.time() - boost_start_time)
            speed_text += f" (Boost: {remaining:.1f}s)"
        if temp_boost_remaining > 0:
            speed_text += f" (Temp Boost: {temp_boost_remaining//60}s)"
        speed_rend = font_small.render(speed_text, True, text_color)
        screen.blit(speed_rend, (20, 30))

        boost_hint = font_small.render("长按Ctrl加速(5s限时)", True, text_color)
        screen.blit(boost_hint, (20, 50))

        # 敌人数量
        if game_mode == "timed":
            max_enemies = TIMED_ENEMY_COUNT
        else:
            max_enemies = ENEMY_COUNT
        enemy_count = font_small.render(f"敌人: {len(enemies)}/{max_enemies}", True, text_color)
        screen.blit(enemy_count, (20, 70))

        # 狂暴计数器（仅淘汰之王）
        if game_mode == "timed":
            high_score_count = sum(1 for e in enemies if e['score'] >= 20)
            rage_color = RED if high_score_count > attack_trigger_count else text_color
            rage_text = font_small.render(f"狂暴敌人: {high_score_count}/{attack_trigger_count}", True, rage_color)
            screen.blit(rage_text, (20, 90))

        # 实时排名（淘汰之王和搜打撤模式）
        if game_mode in ("timed", "mojin"):
            rankings = get_sorted_rankings()
            rank_font = get_font(14)
            rank_surface = pygame.Surface((200, 350), pygame.SRCALPHA)
            rank_surface.fill((0, 0, 0, 100))
            screen.blit(rank_surface, (WIDTH - 220, 120))
            rank_title = rank_font.render("实时排名", True, WHITE)
            screen.blit(rank_title, (WIDTH - 220 + 10, 130))

            y_offset = 160
            max_display = 15
            for i, (name, scr) in enumerate(rankings[:max_display]):
                if i == 0:
                    color = YELLOW
                elif name == player_name:
                    color = LIGHT_GREEN
                else:
                    color = WHITE
                display_name = name if len(name) <= 12 else name[:9] + "..."
                line = f"{i+1}. {display_name} {scr}"
                rendered = rank_font.render(line, True, color)
                screen.blit(rendered, (WIDTH - 220 + 10, y_offset))
                y_offset += 20
            if len(rankings) > max_display:
                more_text = rank_font.render(f"... 共 {len(rankings)} 名", True, WHITE)
                screen.blit(more_text, (WIDTH - 220 + 10, y_offset))

        # 搜打撤模式阶段显示
        if game_mode == "mojin":
            phase_font = get_font(20)
            phase_colors = {"search": CYAN, "strike": RED, "withdraw": ORANGE}
            phase_names = {"search": "搜索", "strike": "打击", "withdraw": "撤离"}
            phase_text = phase_font.render(f"阶段: {phase_names[MOJIN_PHASE]}", True, phase_colors[MOJIN_PHASE])
            screen.blit(phase_text, (20, 120))

        # FPS显示
        if show_fps:
            fps = int(clock.get_fps())
            fps_text = font_small.render(f"FPS: {fps}", True, text_color)
            screen.blit(fps_text, (WIDTH - 100, HEIGHT - 30))

        # 版本号
        ver_text = font_small.render(VERSION, True, text_color)
        screen.blit(ver_text, (WIDTH - 150, HEIGHT - 60))

        # ===== 游戏结束界面 =====
        if not game_active:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((128, 128, 128, 200))
            screen.blit(overlay, (0, 0))

            go_font = get_font(48)
            go_title = go_font.render("游戏结束", True, WHITE)
            screen.blit(go_title, (WIDTH//2 - go_title.get_width()//2, 200))

            if game_mode == "timed" and gameover_killer_name:
                current_rank = get_current_rank()
                rank_text = f"本局排名第 {current_rank}"
                killer_font = get_font(24)
                killer_text = f"被 {gameover_killer_name} 淘汰，{rank_text}"
                killer_rendered = killer_font.render(killer_text, True, WHITE)
                screen.blit(killer_rendered, (WIDTH//2 - killer_rendered.get_width()//2, 270))
            elif game_mode == "timed":
                current_rank = get_current_rank()
                rank_font = get_font(24)
                rank_text = f"本局排名第 {current_rank}"
                rank_rendered = rank_font.render(rank_text, True, WHITE)
                screen.blit(rank_rendered, (WIDTH//2 - rank_rendered.get_width()//2, 270))

            score_font = get_font(32)
            score_display = score_font.render(f"最终得分: {score}", True, WHITE)
            screen.blit(score_display, (WIDTH//2 - score_display.get_width()//2, 320))

            option_font = get_font(36)
            option_y_start = 400
            for i, opt in enumerate(GAMEOVER_OPTIONS):
                if i == gameover_selection:
                    text = "▶ " + opt + " ◀"
                    color = YELLOW
                else:
                    text = opt
                    color = WHITE
                rendered = option_font.render(text, True, color)
                screen.blit(rendered, (WIDTH//2 - rendered.get_width()//2, option_y_start + i * 60))

            hint = font_small.render("↑↓选择  Enter确认  鼠标点击选择  H键查看历史排行榜", True, LIGHT_GRAY)
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 150))

        # ===== 暂停界面 =====
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

    pygame.display.flip()

def restart_game():
    global snake, direction, foods, score, game_active, boosting, color_centers, enemies, gameover_killer_name, global_attack_phase, MOJIN_PHASE, MOJIN_TIMER, temp_boost_remaining, obstacles, containers
    snake = [(0, 0), (-16, 0), (-32, 0), (-48, 0), (-64, 0)]
    direction = (1, 0)
    score = 0
    game_active = True
    boosting = False
    color_centers.clear()
    enemies = []
    gameover_killer_name = None
    global_attack_phase = False
    MOJIN_PHASE = "search"
    MOJIN_TIMER = 0
    temp_boost_remaining = 0
    generate_foods(FOOD_COUNT)

    if game_mode == "timed":
        enemy_count = TIMED_ENEMY_COUNT
    else:
        enemy_count = ENEMY_COUNT

    min_dist_sq = (get_segment_radius() * 4) ** 2
    for i in range(enemy_count):
        placed = False
        for attempt in range(500):
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
            if not overlap:
                body = [(x, y), (x - 16, y), (x - 32, y)]
                dir_options = [(1,0), (-1,0), (0,1), (0,-1)]
                dir = random.choice(dir_options)
                if game_mode == "timed":
                    name = random.choice(ENEMY_NAMES)
                else:
                    name = "Enemy"
                enemies.append({'body': body, 'dir': dir, 'score': 0, 'name': name, 'state': 'idle'})
                placed = True
                break
        if not placed:
            x = random.randint(WORLD_MIN_X + 100, WORLD_MAX_X - 100)
            y = random.randint(WORLD_MIN_Y + 100, WORLD_MAX_Y - 100)
            body = [(x, y), (x - 16, y), (x - 32, y)]
            dir_options = [(1,0), (-1,0), (0,1), (0,-1)]
            dir = random.choice(dir_options)
            if game_mode == "timed":
                name = random.choice(ENEMY_NAMES)
            else:
                name = "Enemy"
            enemies.append({'body': body, 'dir': dir, 'score': 0, 'name': name, 'state': 'idle'})

    # 生成障碍物和容器（仅在搜打撤模式）
    if game_mode == "mojin":
        generate_obstacles_and_containers()
    else:
        obstacles.clear()
        containers.clear()

def new_game():
    restart_game()

def restart():
    global game_started, settings_mode, gameover_screen, paused
    new_game()
    game_started = False
    settings_mode = False
    gameover_screen = False
    paused = False

def start_game():
    global game_started, settings_mode
    if not game_started and not settings_mode:
        new_game()
        game_started = True

# 设置函数
def settings_up():
    global selected_setting
    if not settings_mode:
        return
    selected_setting = (selected_setting - 1) % 5

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
    dt = time.time() - last_time
    last_time = time.time()
    current_time = pygame.time.get_ticks()

    # 更新临时加速剩余时间
    if temp_boost_remaining > 0:
        temp_boost_remaining -= 1

    if game_started and game_active and not paused and not gameover_screen:
        player_pos_history.append(snake[0])
        player_dir_history.append(direction)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_started and not settings_mode:
                    if gameover_screen:
                        gameover_screen = False
                        game_started = False
                        settings_mode = False
                    elif paused:
                        paused = False
                    else:
                        paused = True
                elif settings_mode:
                    settings_cancel()
            elif event.key == pygame.K_SPACE:
                if not game_started and not settings_mode:
                    start_game()
            elif event.key == pygame.K_r:
                if game_started and not settings_mode and not paused and not gameover_screen:
                    restart_game()
                elif not game_started and not settings_mode:
                    restart()
            elif event.key == pygame.K_s:
                if not game_started and not settings_mode:
                    enter_settings()
            elif event.key == pygame.K_q:
                if not game_started and not settings_mode:
                    quit_game()
            elif event.key == pygame.K_m:
                if not game_started and not settings_mode:
                    # 循环切换三个模式
                    if game_mode == "classic":
                        game_mode = "timed"
                    elif game_mode == "timed":
                        game_mode = "mojin"
                    else:
                        game_mode = "classic"
                    # 重新生成障碍物和容器
                    if game_mode == "mojin":
                        generate_obstacles_and_containers()
                    else:
                        obstacles.clear()
                        containers.clear()
            elif event.key == pygame.K_h:
                if not game_started and not settings_mode:
                    show_rankings()
                elif gameover_screen and game_mode == "timed":
                    show_rankings()
            elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                if game_started and game_active and not paused and not gameover_screen:
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
            if gameover_screen:
                if event.key == pygame.K_UP:
                    gameover_selection = (gameover_selection - 1) % 2
                elif event.key == pygame.K_DOWN:
                    gameover_selection = (gameover_selection + 1) % 2
                elif event.key == pygame.K_RETURN:
                    if gameover_selection == 0:
                        restart_game()
                        gameover_screen = False
                    elif gameover_selection == 1:
                        game_started = False
                        settings_mode = False
                        gameover_screen = False
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
                mode_font = get_font(24)
                if game_mode == "timed":
                    mode_text = "模式: 淘汰之王  (M键切换)"
                elif game_mode == "mojin":
                    mode_text = "模式: 搜打撤  (M键切换)"
                else:
                    mode_text = "模式: 经典  (M键切换)"
                mode_rendered = mode_font.render(mode_text, True, BLACK)
                mode_rect = pygame.Rect(WIDTH//2 - mode_rendered.get_width()//2 - 10,
                                        HEIGHT//2 + MODE_BUTTON_Y - mode_rendered.get_height()//2 - 10,
                                        mode_rendered.get_width() + 20, mode_rendered.get_height() + 20)
                mode_hover = mode_rect.collidepoint(mouse_x, mouse_y)
            else:
                hover_button = None
                mode_hover = False

            if settings_mode:
                for i, rect in enumerate(setting_option_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        if selected_setting != i:
                            selected_setting = i
                        break
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

            if gameover_screen:
                option_y_start = 400
                for i in range(2):
                    opt_text = GAMEOVER_OPTIONS[i]
                    font = get_font(36)
                    rendered = font.render(opt_text, True, WHITE)
                    rect = pygame.Rect(WIDTH//2 - rendered.get_width()//2 - 10, option_y_start + i * 60 - 10,
                                       rendered.get_width() + 20, rendered.get_height() + 20)
                    if rect.collidepoint(mouse_x, mouse_y):
                        gameover_selection = i
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
                    mode_font = get_font(24)
                    if game_mode == "timed":
                        mode_text = "模式: 淘汰之王  (M键切换)"
                    elif game_mode == "mojin":
                        mode_text = "模式: 搜打撤  (M键切换)"
                    else:
                        mode_text = "模式: 经典  (M键切换)"
                    mode_rendered = mode_font.render(mode_text, True, BLACK)
                    mode_rect = pygame.Rect(WIDTH//2 - mode_rendered.get_width()//2 - 10,
                                            HEIGHT//2 + MODE_BUTTON_Y - mode_rendered.get_height()//2 - 10,
                                            mode_rendered.get_width() + 20, mode_rendered.get_height() + 20)
                    if mode_rect.collidepoint(mouse_x, mouse_y):
                        if game_mode == "classic":
                            game_mode = "timed"
                        elif game_mode == "timed":
                            game_mode = "mojin"
                        else:
                            game_mode = "classic"
                        # 切换模式时重新生成障碍物/容器
                        if game_mode == "mojin":
                            generate_obstacles_and_containers()
                        else:
                            obstacles.clear()
                            containers.clear()
                elif settings_mode:
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
                                    if i == 0:
                                        settings_right()
                                    elif i == 1:
                                        settings_right()
                                    elif i == 2:
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
                elif gameover_screen:
                    option_y_start = 400
                    for i in range(2):
                        opt_text = GAMEOVER_OPTIONS[i]
                        font = get_font(36)
                        rendered = font.render(opt_text, True, WHITE)
                        rect = pygame.Rect(WIDTH//2 - rendered.get_width()//2 - 10, option_y_start + i * 60 - 10,
                                           rendered.get_width() + 20, rendered.get_height() + 20)
                        if rect.collidepoint(event.pos):
                            if i == 0:
                                restart_game()
                                gameover_screen = False
                            elif i == 1:
                                game_started = False
                                settings_mode = False
                                gameover_screen = False
                            break

    if game_started and not settings_mode and game_active and not paused and not gameover_screen:
        wx, wy = screen_to_world(mouse_x, mouse_y)
        hx, hy = snake[0]
        dx = wx - hx
        dy = wy - hy
        if abs(dx) > 1 or abs(dy) > 1:
            length = math.hypot(dx, dy)
            direction = (dx / length, dy / length)

    if game_started and not settings_mode and game_active and not paused and not gameover_screen:
        current_speed = get_current_speed()
        current_radius = get_segment_radius()
        eat_threshold_sq = (current_radius + FOOD_RADIUS) ** 2
        large_eat_threshold_sq = (current_radius + LARGE_FOOD_RADIUS) ** 2
        collision_threshold_sq = (current_radius * 2) ** 2

        old_head = snake[0]
        new_head = (old_head[0] + direction[0] * current_speed,
                    old_head[1] + direction[1] * current_speed)

        # 玩家与容器碰撞处理
        handle_container_collision(new_head)

        new_enemy_heads = []
        for enemy in enemies:
            old_enemy_head = enemy['body'][0]
            # 计算敌人速度（根据模式和阶段）
            enemy_speed = get_base_speed()
            if game_mode == "timed" and enemy['score'] >= 20 and enemy.get('state') == 'attacking':
                enemy_speed *= 4.0
            elif game_mode == "mojin":
                if MOJIN_PHASE == "strike":
                    enemy_speed *= MOJIN_STRIKE_SPEED
                elif MOJIN_PHASE == "withdraw":
                    enemy_speed *= MOJIN_WITHDRAW_SPEED
                else:  # search
                    enemy_speed *= MOJIN_SEARCH_SPEED
            new_dir = get_enemy_new_direction(enemy, foods)
            enemy['dir'] = new_dir
            new_enemy_head = (old_enemy_head[0] + new_dir[0] * enemy_speed,
                              old_enemy_head[1] + new_dir[1] * enemy_speed)
            new_enemy_heads.append((enemy, old_enemy_head, new_enemy_head))

        if check_boundary(new_head):
            game_active = False
            gameover_screen = True
            if game_mode == "timed" and score > 0:
                add_score(player_name, score)
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
                # 敌人与容器碰撞处理
                handle_container_collision(new_head_pos)

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

        if ate_index is not None:
            score += 1

        enemy_ate_info = []
        for enemy, old_enemy_head, new_enemy_head in surviving_enemy_heads:
            for i, (fx, fy, _, fr) in enumerate(foods):
                threshold = large_eat_threshold_sq if fr == LARGE_FOOD_RADIUS else eat_threshold_sq
                if (new_enemy_head[0] - fx) ** 2 + (new_enemy_head[1] - fy) ** 2 < threshold:
                    enemy_ate_info.append((enemy, i))
                    enemy['score'] += 1
                    break
                mid_x = (old_enemy_head[0] + new_enemy_head[0]) / 2
                mid_y = (old_enemy_head[1] + new_enemy_head[1]) / 2
                if (mid_x - fx) ** 2 + (mid_y - fy) ** 2 < threshold:
                    enemy_ate_info.append((enemy, i))
                    enemy['score'] += 1
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
                    gameover_screen = True
                    gameover_killer_name = enemy['name']
                    if game_mode == "timed" and score > 0:
                        add_score(player_name, score)
                    break
            if not game_active:
                break

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

        if game_mode == "classic" and len(enemies) < ENEMY_COUNT:
            for _ in range(5):
                if len(enemies) >= ENEMY_COUNT:
                    break
                placed = False
                min_dist_sq = (get_segment_radius() * 4) ** 2
                for attempt in range(50):
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
                    if not overlap:
                        body = [(x, y), (x - 16, y), (x - 32, y)]
                        dir_options = [(1,0), (-1,0), (0,1), (0,-1)]
                        dir = random.choice(dir_options)
                        enemies.append({'body': body, 'dir': dir, 'score': 0, 'name': "Enemy", 'state': 'idle'})
                        placed = True
                        break
                if not placed:
                    break

        # 更新全局攻击阶段（仅淘汰之王）
        if game_mode == "timed":
            high_score_count = sum(1 for e in enemies if e['score'] >= 20)
            if global_attack_phase:
                if high_score_count < attack_trigger_count * 0.7:
                    global_attack_phase = False
                    for e in enemies:
                        e['state'] = 'idle'
            else:
                if high_score_count >= attack_trigger_count:
                    global_attack_phase = True
                    for e in enemies:
                        if e['score'] >= 20:
                            e['state'] = 'preparing'
            if global_attack_phase:
                preparing_count = sum(1 for e in enemies if e.get('state') == 'preparing')
                if preparing_count > attack_trigger_count * 0.8 and random.random() < 0.02:
                    for e in enemies:
                        if e['state'] == 'preparing':
                            e['state'] = 'attacking'

        update_camera(snake[0][0], snake[0][1])

    draw()
    clock.tick(FPS)

pygame.quit()