import random

from src.referee.referee import Referee, Player
from src.gui.shapes import *
import math

# Constants

# Referee constants
GRID_SIZE = 4

PAINTING_ZONE_TYPE = 0
ISOLATION_ZONE_TYPE = 1
PLUMBING_ZONE_TYPE = 2
ELECTRICITY_ZONE_TYPE = 3

DURATIONS = [11, 6, 4, 3, 2, 2, 2, 1, 1]
# For each duration d, DURATIONS[d - 1] is the number of jobs with that duration

FIRST_JOB = 0
SECOND_JOB = 1

WIN_SCORE = GRID_SIZE * GRID_SIZE

NB_WORKERS = 2

LAST_TURN = 200

# Messages
LAST_TURN_MSG = 'Last turn reached'
COMMAND_ERROR = "The must be PASS or 3 integers separated by space."
WORKER_MAN_ERROR = "Worker man is not available."
WORKER_WOMAN_ERROR = "Worker woman is not available."
OUT_OF_THE_GRID_ERROR = "No zone exists at coordinates Line %d Column %d)."
NO_JOB_ERROR = "Job %d does not exist."
JOB_DONE_ERROR = "Zone Line %d Column %d Job %d : The job was already started or finished."
PAINTING_JOB_ERROR = ("Zone Line %d Column %d : The second job of painting work cannot start before the end of the "
                      "first job.")
ISOLATION_JOB_ERROR = "Zone Line %d Column %d : The two jobs of isolation work cannot occur at the same time."
PLUMBING_JOB_ERROR = "Zone Line %d Column %d : The second job of plumbing work should occur during the first job."
ELECTRICITY_FIRST_JOB_ERROR = ("Zone Line %d Column %d : First job of electricity work should start before the end of "
                               "the first job of each neighbor zone.")
ELECTRICITY_SECOND_JOB_ERROR = ("Zone Line %d Column %d : Second job of electricity work should start before the "
                                "beginning of the second job of each neighbor zone.")
ONE_PLAYER_LEFT = "Last player in game. You won. "
WINNING_SCORE_MSG = 'You finished your construction site. You won.'
WINNING_END_MSG = 'Other players finished their construction site.'

# Drawing constants
XMIN = 0
XMAX = 1000
YMIN = 0
YMAX = 600

# Grid constants
GRID_WIDTH = 250
GRID_MARGIN = 50
LEFT_GRID = (XMIN + XMAX) / 2 - GRID_WIDTH - GRID_MARGIN / 2
RIGHT_GRID = LEFT_GRID + 2 * GRID_WIDTH + GRID_MARGIN
TOP_GRID = (YMIN + YMAX) / 2 - GRID_WIDTH - GRID_MARGIN / 2
BOTTOM_GRID = TOP_GRID + 2 * GRID_WIDTH + GRID_MARGIN
CELL_WIDTH = GRID_WIDTH / GRID_SIZE

# Players names constants
PLAYERS_NAME_MARGIN = 10
PLAYERS_NAME_WIDTH = 200
PLAYERS_NAME_HEIGHT = 60
PLAYERS_NAME_RECT_STROKE_WIDTH = 5
PLAYERS_NAME_RECT_RADIUS = 10
PLAYERS_NAME_PADDING = 10
PLAYERS_NAME_MAX_CHAR = 8

# Left abscissa for players names rectangles
PLAYERS_NAME_RECT_LEFTS = [XMIN + PLAYERS_NAME_MARGIN, XMAX - PLAYERS_NAME_WIDTH - PLAYERS_NAME_MARGIN,
                           XMIN + PLAYERS_NAME_MARGIN, XMAX - PLAYERS_NAME_WIDTH - PLAYERS_NAME_MARGIN]
# Top ordinates for players names rectangles
PLAYERS_NAME_RECT_TOPS = [YMIN + PLAYERS_NAME_MARGIN, YMIN + PLAYERS_NAME_MARGIN,
                          YMAX - PLAYERS_NAME_HEIGHT - PLAYERS_NAME_MARGIN,
                          YMAX - PLAYERS_NAME_HEIGHT - PLAYERS_NAME_MARGIN]

# Colors of the four players
PLAYERS_COLORS = [(213, 94, 0), (204, 121, 167), (0, 114, 178), (0, 158, 115)]

# Timings
SCORES_SAVE_TIME = 0.8
SCORES_UPDATE_TIME = 0.9

JOB_SLIDERS_SAVE_TIME = 0.2
JOB_SLIDERS_UPDATE_TIME = 0.6
JOB_APPEAR_SAVE_TIME = 0.1
JOB_APPEAR_UPDATE_TIME = 0.5
JOB_DISAPPEAR_SAVE_TIME = 0.6
JOB_DISAPPEAR_UPDATE_TIME = 0.9

JOB_INCREASE_DURATION_SAVE_TIME = 0.8
JOB_INCREASE_DURATION_UPDATE_TIME = 0.9


def get_painting_shape():
    path = Path("painting-icon", 0, CELL_WIDTH * 3 // 7)
    path.add_arc_element(True, CELL_WIDTH // 10, CELL_WIDTH // 10, 90,
                         False, True, -CELL_WIDTH * 0.5 // 7, CELL_WIDTH * 2.5 // 7)
    path.add_line_element(True, -CELL_WIDTH * 0.5 // 7, 0)
    path.add_arc_element(True, CELL_WIDTH // 10, CELL_WIDTH // 10, 90,
                         False, False, -CELL_WIDTH * 1 // 7, -CELL_WIDTH * 0.5 // 7)
    path.add_line_element(True, -CELL_WIDTH * 1.75 // 7, -CELL_WIDTH * 0.5 // 7)
    path.add_arc_element(True, CELL_WIDTH // 10, CELL_WIDTH // 10, 90,
                         False, True, -CELL_WIDTH * 2 // 7, -CELL_WIDTH * 1 // 7)
    path.add_line_element(True, -CELL_WIDTH * 2 // 7, -CELL_WIDTH * 3 // 7)
    path.add_line_element(True, CELL_WIDTH * 2 // 7, -CELL_WIDTH * 3 // 7)
    path.add_move_element(True, 0, CELL_WIDTH * 3 // 7)
    path.add_arc_element(True, CELL_WIDTH // 10, CELL_WIDTH // 10, 90,
                         False, False, CELL_WIDTH * 0.5 // 7, CELL_WIDTH * 2.5 // 7)
    path.add_line_element(True, CELL_WIDTH * 0.5 // 7, 0)
    path.add_arc_element(True, CELL_WIDTH // 10, CELL_WIDTH // 10, 90,
                         False, True, CELL_WIDTH * 1 // 7, -CELL_WIDTH * 0.5 // 7)
    path.add_line_element(True, CELL_WIDTH * 1.75 // 7, -CELL_WIDTH * 0.5 // 7)
    path.add_arc_element(True, CELL_WIDTH // 10, CELL_WIDTH // 10, 90,
                         False, False, CELL_WIDTH * 2 // 7, -CELL_WIDTH * 1 // 7)
    path.add_line_element(True, CELL_WIDTH * 2 // 7, -CELL_WIDTH * 3 // 7)

    for i in range(3):
        x = (-CELL_WIDTH * 2 // 7) * (i + 1) // 4 + (CELL_WIDTH * 2 // 7) * (4 - i - 1) // 4
        y = -CELL_WIDTH * 3 // 7
        path.add_move_element(True, x, y)
        path.add_line_element(True, x, y + CELL_WIDTH * 1.5 // 7)
    return path


def get_isolation_shape():
    g = Group("isolation-icon")

    gsun = Group("isolation-icon-sun")
    g.add_child(gsun)

    p = Path("isolation-icon-sun-path", -CELL_WIDTH * 1 // 7, -CELL_WIDTH * 1 // 7)
    p.add_arc_element(True, CELL_WIDTH // 7, CELL_WIDTH // 7, 180,
                      True, True, CELL_WIDTH * 1 // 7, CELL_WIDTH * 1 // 7)
    gsun.add_child(p)

    alpha0 = math.pi / 12
    delta = -math.pi / 6
    for i in range(5):
        alpha = alpha0 + i * delta
        x1 = 1.5 * CELL_WIDTH // 7 * math.cos(alpha)
        y1 = 1.5 * CELL_WIDTH // 7 * math.sin(alpha)
        x2 = 3 * CELL_WIDTH // 7 * math.cos(alpha)
        y2 = 3 * CELL_WIDTH // 7 * math.sin(alpha)
        gsun.add_child(Line('isolation-icon-sun-line', x1, y1, x2, y2))

    gsun.fill_color = (255, 255, 0)
    gsun.stroke_color = (200, 200, 0)

    gice = Group("isolation-icon-ice")
    g.add_child(gice)

    ice_alpha = math.pi / 2
    x1 = 1.25 * CELL_WIDTH // 7
    y1 = 1.25 * CELL_WIDTH // 7
    x2 = x1 + 1.5 * CELL_WIDTH // 7 * math.cos(ice_alpha - 0.1)
    y2 = y1 + 1.5 * CELL_WIDTH // 7 * math.sin(ice_alpha - 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    x1 = 0
    y1 = 0
    x2 = x1 + 3 * CELL_WIDTH // 7 * math.cos(ice_alpha + 0.1)
    y2 = y1 + 3 * CELL_WIDTH // 7 * math.sin(ice_alpha + 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    ice_alpha = math.pi / 2 + math.pi / 3
    x1 = (x1 * 0.45 + x2 * 0.55)
    y1 = (y1 * 0.45 + y2 * 0.55)
    x2 = x1 + 1.2 * CELL_WIDTH // 7 * math.cos(ice_alpha + 0.1)
    y2 = y1 + 1.2 * CELL_WIDTH // 7 * math.sin(ice_alpha + 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    ice_alpha = math.pi / 2 - math.pi / 3
    x2 = x1 + 1.2 * CELL_WIDTH // 7 * math.cos(ice_alpha + 0.1)
    y2 = y1 + 1.2 * CELL_WIDTH // 7 * math.sin(ice_alpha + 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    ice_alpha = math.pi
    x1 = -1.25 * CELL_WIDTH // 7
    y1 = -1.25 * CELL_WIDTH // 7
    x2 = x1 + 1.5 * CELL_WIDTH // 7 * math.cos(ice_alpha + 0.1)
    y2 = y1 + 1.5 * CELL_WIDTH // 7 * math.sin(ice_alpha + 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    x1 = 0
    y1 = 0
    x2 = x1 + 3 * CELL_WIDTH // 7 * math.cos(ice_alpha - 0.1)
    y2 = y1 + 3 * CELL_WIDTH // 7 * math.sin(ice_alpha - 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    ice_alpha = math.pi + math.pi / 3
    x1 = (x1 * 0.45 + x2 * 0.55)
    y1 = (y1 * 0.45 + y2 * 0.55)
    x2 = x1 + 1.2 * CELL_WIDTH // 7 * math.cos(ice_alpha + 0.1)
    y2 = y1 + 1.2 * CELL_WIDTH // 7 * math.sin(ice_alpha + 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    ice_alpha = math.pi - math.pi / 3
    x2 = x1 + 1.2 * CELL_WIDTH // 7 * math.cos(ice_alpha + 0.1)
    y2 = y1 + 1.2 * CELL_WIDTH // 7 * math.sin(ice_alpha + 0.1)
    gice.add_child(Line('isolation-icon-ice-line', x1, y1, x2, y2))

    gice.stroke_color = (100, 100, 255)

    line = Line('isolation-icon-line', -CELL_WIDTH * 3 // 7, -CELL_WIDTH * 3 // 7,
                CELL_WIDTH * 3 // 7, CELL_WIDTH * 3 // 7)
    line.stroke_color = (100, 100, 100)
    line.stroke_width = 3
    g.add_child(line)

    gsun.stroke_width = 3
    gice.stroke_width = 3

    return g


def get_plumbing_shape():
    polyline = PolyLine("plumbing-icon", closed=True, coordinates=[
        -CELL_WIDTH * 0.5 // 9, CELL_WIDTH * 4 // 9,
        -CELL_WIDTH * 0.5 // 9, -CELL_WIDTH * 1 // 9,
        -CELL_WIDTH * 1.35 // 9, -CELL_WIDTH * 2 // 9,
        -CELL_WIDTH * 1.5 // 9, -CELL_WIDTH * 3 // 9,
        -CELL_WIDTH * 0.75 // 9, -CELL_WIDTH * 3.5 // 9,
        -CELL_WIDTH * 0.75 // 9, -CELL_WIDTH * 2 // 9,
        0, -CELL_WIDTH * 1.5 // 9,
        CELL_WIDTH * 0.75 // 9, -CELL_WIDTH * 2 // 9,
        CELL_WIDTH * 0.75 // 9, -CELL_WIDTH * 3.5 // 9,
        CELL_WIDTH * 1.5 // 9, -CELL_WIDTH * 3 // 9,
        CELL_WIDTH * 1.35 // 9, -CELL_WIDTH * 2 // 9,
        CELL_WIDTH * 0.5 // 9, -CELL_WIDTH * 1 // 9,
        CELL_WIDTH * 0.5 // 9, CELL_WIDTH * 4 // 9,
    ])
    polyline.fill_color = (0, 0, 255)
    return polyline


def get_electricity_shape():
    polyline = PolyLine("electricity-icon", closed=True, coordinates=[
        CELL_WIDTH // 9, 4 * CELL_WIDTH // 9,
        -2 * CELL_WIDTH // 9, - CELL_WIDTH // 18,
        0, - CELL_WIDTH // 18,
        -CELL_WIDTH // 9, -4 * CELL_WIDTH // 9,
        2 * CELL_WIDTH // 9, CELL_WIDTH // 18,
        0, CELL_WIDTH // 18,
    ])

    polyline.fill_color = (255, 255, 0)

    return polyline


def get_workerwoman_shape():
    group = Group("workerwoman")
    group.add_child(Oval("workerwoman-head", 0, 0, CELL_WIDTH // 4, CELL_WIDTH // 4))
    group.add_child(Oval("workerwoman-head-eye", CELL_WIDTH // 8 * math.cos(math.pi / 4),
                         -CELL_WIDTH // 8 * math.sin(math.pi / 4), CELL_WIDTH // 16, CELL_WIDTH // 16))
    group.add_child(Oval("workerwoman-head-eye", CELL_WIDTH // 8 * math.cos(3 * math.pi / 4),
                         -CELL_WIDTH // 8 * math.sin(3 * math.pi / 4), CELL_WIDTH // 16, CELL_WIDTH // 16))

    for i in range(3):
        x1 = CELL_WIDTH // 8 * math.cos(3 * math.pi / 4) + CELL_WIDTH // 16 * math.cos(
            2 * math.pi / 3 - i * math.pi / 6)
        y1 = -CELL_WIDTH // 8 * math.sin(3 * math.pi / 4) - CELL_WIDTH // 16 * math.sin(
            2 * math.pi / 3 - i * math.pi / 6)
        x2 = x1 + CELL_WIDTH // 16 * math.cos(2 * math.pi / 3 - i * math.pi / 6)
        y2 = y1 - CELL_WIDTH // 16 * math.sin(2 * math.pi / 3 - i * math.pi / 6)
        group.add_child(Line("workerwoman-head-eye", x1, y1, x2, y2))

        x1 = CELL_WIDTH // 8 * math.cos(math.pi / 4) + CELL_WIDTH // 16 * math.cos(2 * math.pi / 3 - i * math.pi / 6)
        y1 = -CELL_WIDTH // 8 * math.sin(math.pi / 4) - CELL_WIDTH // 16 * math.sin(2 * math.pi / 3 - i * math.pi / 6)
        x2 = x1 + CELL_WIDTH // 16 * math.cos(2 * math.pi / 3 - i * math.pi / 6)
        y2 = y1 - CELL_WIDTH // 16 * math.sin(2 * math.pi / 3 - i * math.pi / 6)
        group.add_child(Line("workerwoman-head-eye", x1, y1, x2, y2))

    path = Path("workerwoman-head-smile",
                CELL_WIDTH // 8 * math.cos(math.pi / 4), CELL_WIDTH // 8 * math.sin(math.pi / 4))
    path.add_arc_element(True, CELL_WIDTH // 8, CELL_WIDTH // 8, math.pi / 2, False, True,
                         CELL_WIDTH // 8 * math.cos(3 * math.pi / 4), CELL_WIDTH // 8 * math.sin(3 * math.pi / 4))
    group.add_child(path)
    return group


def get_workerman_shape():
    group = Group("workerman")
    group.add_child(Oval("workerman-head", 0, 0, CELL_WIDTH // 4, CELL_WIDTH // 4))
    group.add_child(Oval("workerman-head-eye", CELL_WIDTH // 8 * math.cos(math.pi / 4),
                         -CELL_WIDTH // 8 * math.sin(math.pi / 4), CELL_WIDTH // 16, CELL_WIDTH // 16))
    group.add_child(Oval("workerman-head-eye", CELL_WIDTH // 8 * math.cos(3 * math.pi / 4),
                         -CELL_WIDTH // 8 * math.sin(3 * math.pi / 4), CELL_WIDTH // 16, CELL_WIDTH // 16))

    path = Path("workerman-head-smile",
                CELL_WIDTH // 8 * math.cos(math.pi / 4), CELL_WIDTH // 8 * math.sin(math.pi / 4))
    path.add_arc_element(True, CELL_WIDTH // 8, CELL_WIDTH // 8, math.pi / 2, False, True,
                         CELL_WIDTH // 8 * math.cos(3 * math.pi / 4), CELL_WIDTH // 8 * math.sin(3 * math.pi / 4))
    group.add_child(path)
    return group


class GuiManager:
    _inst = None

    @staticmethod
    def get_gui_manager():
        return GuiManager._inst

    def __init__(self, referee):
        self._referee = referee
        GuiManager._inst = self

        self._players_colors = dict()
        self._players_scores_texts = dict()

        self._players_workers_pauses_zones = dict()
        self._players_left_grids = dict()
        self._players_top_grids = dict()

        self._players_working_jobs_sliders = []
        self._players_working_jobs_rectangles = []

        self._zones_durations_texts = []

        self._players_workers = dict()

    def clear(self):
        self._players_colors.clear()
        self._players_scores_texts.clear()
        self._players_workers_pauses_zones.clear()
        self._players_left_grids.clear()
        self._players_top_grids.clear()
        self._players_working_jobs_sliders.clear()
        self._players_working_jobs_rectangles.clear()
        self._players_workers.clear()
        del self._zones_durations_texts[:]

    def _get_cell_x_center(self, player, x):
        return self._players_left_grids[player] + CELL_WIDTH / 2 + x * CELL_WIDTH

    def _get_cell_y_center(self, player, y):
        return self._players_top_grids[player] + CELL_WIDTH / 2 + y * CELL_WIDTH

    def _build_grid_lines(self):

        for i, player in enumerate(self._referee.players):
            x0 = LEFT_GRID + (i % 2) * (GRID_WIDTH + GRID_MARGIN)
            y0 = TOP_GRID + (i // 2) * (GRID_WIDTH + GRID_MARGIN)

            self._players_left_grids[player] = x0
            self._players_top_grids[player] = y0

            for index in range(GRID_SIZE + 1):
                x = self._get_cell_x_center(player, index) - CELL_WIDTH // 2
                y = self._get_cell_y_center(player, index) - CELL_WIDTH // 2
                for coords, stroke_width in [
                    ((x, y0, x, y0 + GRID_WIDTH), 3),
                    ((x0, y, x0 + GRID_WIDTH, y), 3),
                    ((x0, y + CELL_WIDTH // 2, x0 + GRID_WIDTH, y + CELL_WIDTH // 2), 2),
                ]:
                    if index != GRID_SIZE or stroke_width == 3:
                        line = Line('grid-line', *coords)
                        line.stroke_width = stroke_width
                        self._referee.add_graphic(line)

    def _build_players_names(self):
        for i, player in enumerate(self._referee.players):
            group = Group('player-name-group')

            x = PLAYERS_NAME_RECT_LEFTS[i]
            y = PLAYERS_NAME_RECT_TOPS[i]

            rect = Rectangle('player-name-rectangle', x, y, PLAYERS_NAME_WIDTH, PLAYERS_NAME_HEIGHT)
            rect.stroke_width = PLAYERS_NAME_RECT_STROKE_WIDTH
            rect.rx = PLAYERS_NAME_RECT_RADIUS
            rect.ry = PLAYERS_NAME_RECT_RADIUS
            rect.stroke_color = PLAYERS_COLORS[i]
            rect.fill_color = PLAYERS_COLORS[i]

            text = Text('player-name-text', x + PLAYERS_NAME_PADDING, y + PLAYERS_NAME_HEIGHT / 2,
                        text=player.name[:PLAYERS_NAME_MAX_CHAR], font_size=25, font_family="Arial")
            text.set_horizontal_left_align()
            text.set_vertical_center_align()

            group.add_children([rect, text])
            self._referee.add_graphic(group)

    def build_static_graphics(self):
        self._build_grid_lines()
        self._build_players_names()

    def build_construction_sites(self, construction_site):
        for row in range(GRID_SIZE):
            self._zones_durations_texts.append([])
            self._players_working_jobs_sliders.append([])
            self._players_working_jobs_rectangles.append([])
            for column in range(GRID_SIZE):
                zone = construction_site.zones[row][column]
                d1 = zone.get_duration(FIRST_JOB)
                d2 = zone.get_duration(SECOND_JOB)
                zones_durations_texts = dict()
                players_working_jobs_sliders = dict()
                players_working_jobs_rectangles = dict()
                self._zones_durations_texts[-1].append(zones_durations_texts)
                self._players_working_jobs_sliders[-1].append(players_working_jobs_sliders)
                self._players_working_jobs_rectangles[-1].append(players_working_jobs_rectangles)
                for player in self._referee.players:
                    zonex = self._get_cell_x_center(player, column)
                    zoney = self._get_cell_y_center(player, row)

                    x = zonex + 3 * CELL_WIDTH // 8
                    y1 = zoney - CELL_WIDTH // 4
                    y2 = zoney + CELL_WIDTH // 4
                    t1 = Text('zone-duration', x, y1, text=str(d1), font_size=15, font_family="Arial")
                    t2 = Text('zone-duration', x, y2, text=str(d2), font_size=15, font_family="Arial")
                    t1.stroke_color = (100, 100, 100)
                    t2.stroke_color = (100, 100, 100)
                    zones_durations_texts[player] = [t1, t2]
                    self._referee.add_graphic(t1)
                    self._referee.add_graphic(t2)

                    x1 = zonex - CELL_WIDTH // 2
                    y1 = zoney - CELL_WIDTH // 2
                    y2 = zoney
                    width = CELL_WIDTH
                    height = CELL_WIDTH // 2

                    r1 = Rectangle("job-rect", x1, y1, width, height)
                    r2 = Rectangle("job-rect", x1, y2, width, height)
                    r1.stroke_color = (255, 0, 0)
                    r2.stroke_color = (255, 0, 0)
                    r1.opacity = 0
                    r2.opacity = 0
                    r1.stroke_width = 5
                    r2.stroke_width = 5

                    players_working_jobs_rectangles[player] = [r1, r2]
                    self._referee.add_graphic(r1)
                    self._referee.add_graphic(r2)

                    r1 = Rectangle("job-slider", 0, 0, width, height)
                    r2 = Rectangle("job-slider", 0, 0, width, height)
                    r1.translate_x = x1
                    r1.translate_y = y1
                    r2.translate_x = x1
                    r2.translate_y = y2
                    r1.fill_color = (0, 155, 0)
                    r2.fill_color = (0, 155, 0)
                    r1.scale_x = 0
                    r2.scale_x = 0

                    players_working_jobs_sliders[player] = [r1, r2]
                    self._referee.add_graphic(r1)
                    self._referee.add_graphic(r2)

                    p = None
                    if zone.type == PAINTING_ZONE_TYPE:
                        p = get_painting_shape()
                    elif zone.type == ISOLATION_ZONE_TYPE:
                        p = get_isolation_shape()
                    elif zone.type == PLUMBING_ZONE_TYPE:
                        p = get_plumbing_shape()
                    elif zone.type == ELECTRICITY_ZONE_TYPE:
                        p = get_electricity_shape()

                    if p is not None:
                        p.opacity = 0.15
                        p.translate_x = zonex
                        p.translate_y = zoney
                        self._referee.add_graphic(p)

    def build_pauses_zones(self):
        for i, player in enumerate(self._referee.players):
            x = self._players_left_grids[player] + (
                (- CELL_WIDTH - GRID_MARGIN) if (i % 2 == 0) else (GRID_WIDTH + GRID_MARGIN))
            y = self._players_top_grids[player] + CELL_WIDTH
            width = CELL_WIDTH
            height = 2 * CELL_WIDTH

            self._referee.add_graphic(Rectangle("pause-rect", x, y, width, height, rx=5, ry=5))
            self._players_workers_pauses_zones[player] = (
                (x + CELL_WIDTH // 2, y + CELL_WIDTH // 2),
                (x + CELL_WIDTH // 2, y + 3 * CELL_WIDTH // 2)
            )

    def add_workers(self, player):
        workerwoman = get_workerwoman_shape()
        workerman = get_workerman_shape()
        self._players_workers[player] = [workerwoman, workerman]
        for worker, coords in zip(self._players_workers[player], self._players_workers_pauses_zones[player]):
            worker.translate_x, worker.translate_y = coords
        self._referee.add_graphic(workerman)
        self._referee.add_graphic(workerwoman)

    def build_scores(self):
        for i, player in enumerate(self._referee.players):
            x = PLAYERS_NAME_RECT_LEFTS[i]
            y = PLAYERS_NAME_RECT_TOPS[i]
            t = Text('player-score', x + PLAYERS_NAME_WIDTH - PLAYERS_NAME_PADDING, y + PLAYERS_NAME_HEIGHT / 2,
                     text='0', font_size=25, font_family="Arial")

            t.set_horizontal_right_align()
            t.set_vertical_center_align()

            self._referee.add_graphic(t)
            self._players_scores_texts[player] = t

    def edit_score(self, turn, player, score):
        t = self._players_scores_texts[player]
        t.save_state(turn + SCORES_SAVE_TIME)
        t.text = str(score)
        t.save_state(turn + SCORES_UPDATE_TIME)

    def update_job_slider(self, turn, player, zone, job):
        duration = zone.get_duration(job)
        r = self._players_working_jobs_sliders[zone.row][zone.column][player][job]
        r.save_state(turn + JOB_SLIDERS_SAVE_TIME)
        r.scale_x += 1 / duration
        r.save_state(turn + JOB_SLIDERS_UPDATE_TIME)

    def start_job(self, turn, player, zone, job, worker, starting):
        r = self._players_working_jobs_rectangles[zone.row][zone.column][player][job]
        r.save_state(turn + (JOB_APPEAR_SAVE_TIME if starting else JOB_DISAPPEAR_SAVE_TIME))
        r.stroke_opacity = 1 if starting else 0
        r.save_state(turn + (JOB_APPEAR_UPDATE_TIME if starting else JOB_DISAPPEAR_UPDATE_TIME))

        worker_index = 0 if worker.is_woman else 1
        worker_shape = self._players_workers[player][worker_index]

        worker_shape.save_state(turn + (JOB_APPEAR_SAVE_TIME if starting else JOB_DISAPPEAR_SAVE_TIME))
        if not starting:
            worker_shape.translate_x, worker_shape.translate_y = self._players_workers_pauses_zones[player][
                worker_index]
        else:
            x = self._get_cell_x_center(player, zone.column)
            y = self._get_cell_y_center(player, zone.row) + CELL_WIDTH // 4 * (2 * job - 1)
            worker_shape.translate_x, worker_shape.translate_y = x, y
        worker_shape.save_state(turn + (JOB_APPEAR_UPDATE_TIME if starting else JOB_DISAPPEAR_UPDATE_TIME))

    def increase_job_duration(self, turn, player, zone, job, ):
        duration = zone.get_duration(job)

        t = self._zones_durations_texts[zone.row][zone.column][player][job]
        t.save_state(turn + JOB_INCREASE_DURATION_SAVE_TIME)
        t.text = str(duration)
        t.save_state(turn + JOB_INCREASE_DURATION_UPDATE_TIME)

        if zone.is_started(job):
            r = self._players_working_jobs_sliders[zone.row][zone.column][player][job]
            r.save_state(turn + JOB_INCREASE_DURATION_SAVE_TIME)
            r.scale_x = (turn - zone.start_turn(job) + 1) / duration
            r.save_state(turn + JOB_INCREASE_DURATION_UPDATE_TIME)


class Worker:
    def __init__(self, is_woman):
        self.current_working_zone = None
        self.current_working_job = None
        self._is_woman = is_woman

    def work(self, zone, job):
        self.current_working_zone = zone
        self.current_working_job = job

    def stop_working(self):
        self.current_working_job = None
        self.current_working_job = None

    @property
    def is_woman(self):
        return self._is_woman

    @property
    def is_working(self):
        return self.current_working_job is not None


class Zone:
    def __init__(self, row, column, type, duration1, duration2):
        self._type = type
        self._row = row
        self._column = column

        # If plumbing and duration 2 is greater than duration 1, exchange
        if type == PLUMBING_ZONE_TYPE and duration2 > duration1:
            duration1, duration2 = duration2, duration1

        self._durations = [duration1, duration2]
        self._start_turns = [None, None]
        self._finished = False


    @property
    def row(self):
        return self._row

    @property
    def column(self):
        return self._column

    @property
    def type(self):
        return self._type

    def get_duration(self, job):
        return self._durations[job]

    def increase_duration(self, job):
        self._durations[job] += 1

    def start(self, job, turn):
        self._start_turns[job] = turn

    def is_started(self, job):
        return self._start_turns[job] is not None

    def start_turn(self, job):
        return self._start_turns[job]

    def last_turn(self, job):
        if self._start_turns[job] is None:
            return None
        return self._start_turns[job] + self._durations[job] - 1

    def is_ended(self, turn, job):
        return self.is_started(job) and self.last_turn(job) <= turn

    def is_all_jobs_ended(self, turn):
        return self.is_ended(turn, FIRST_JOB) and self.is_ended(turn, SECOND_JOB)

    def is_finished_for_the_first_time(self, turn):
        if self._finished:
            return False
        if self.is_all_jobs_ended(turn):
            self._finished = True
            return True
        return False

    def check_constraint(self, turn, neighbor_zones):
        if self._type == PAINTING_ZONE_TYPE:
            if not self.is_started(SECOND_JOB):
                return None
            if self.is_started(FIRST_JOB) and self.start_turn(SECOND_JOB) > self.last_turn(FIRST_JOB):
                return None
            return PAINTING_JOB_ERROR % (self.row, self.column)

        elif self._type == ISOLATION_ZONE_TYPE:
            if not self.is_started(FIRST_JOB):
                return None
            if not self.is_started(SECOND_JOB):
                return None
            if self.start_turn(SECOND_JOB) > self.last_turn(FIRST_JOB):
                return None
            if self.start_turn(FIRST_JOB) > self.last_turn(SECOND_JOB):
                return None
            return ISOLATION_JOB_ERROR % (self.row, self.column)

        elif self._type == PLUMBING_ZONE_TYPE:
            if not self.is_started(SECOND_JOB) and not self.is_ended(turn, FIRST_JOB):
                return None
            if (self.is_started(FIRST_JOB) and self.is_started(SECOND_JOB)
                    and self.start_turn(SECOND_JOB) >= self.start_turn(FIRST_JOB) and
                    self.last_turn(SECOND_JOB) <= self.last_turn(FIRST_JOB)):
                return None
            return PLUMBING_JOB_ERROR % (self.row, self.column)

        elif self._type == ELECTRICITY_ZONE_TYPE:
            for zone in neighbor_zones:
                if not zone.is_started(FIRST_JOB):
                    continue
                if self.is_started(FIRST_JOB) and self.start_turn(FIRST_JOB) <= zone.last_turn(FIRST_JOB):
                    continue
                return ELECTRICITY_FIRST_JOB_ERROR % (self.row, self.column)
            for zone in neighbor_zones:
                if not zone.is_started(SECOND_JOB):
                    continue
                if self.is_started(SECOND_JOB) and self.start_turn(SECOND_JOB) <= zone.start_turn(SECOND_JOB):
                    continue
                return ELECTRICITY_SECOND_JOB_ERROR % (self.row, self.column)
        return None

    def paste(self, zone):
        self._type = zone._type
        self._durations = [d for d in zone._durations]


class ConstructionSite:
    """
    Class representing a construction site with 16 zones
    When initialized, the construction site is initialized at random.
    """

    def __init__(self):
        #  Partition of the 16 zones
        types = [t for t in [PAINTING_ZONE_TYPE, ISOLATION_ZONE_TYPE, PLUMBING_ZONE_TYPE, ELECTRICITY_ZONE_TYPE]
                 for _ in range(GRID_SIZE)]
        while True:
            random.shuffle(types)
            if any(types[row * GRID_SIZE + column] == ELECTRICITY_ZONE_TYPE
                   and types[row * GRID_SIZE + column + 1] == ELECTRICITY_ZONE_TYPE
                   for row in range(GRID_SIZE) for column in range(GRID_SIZE - 1)):
                        continue
            if any(types[row * GRID_SIZE + column] == ELECTRICITY_ZONE_TYPE
                   and types[(row + 1) * GRID_SIZE + column] == ELECTRICITY_ZONE_TYPE
                   for row in range(GRID_SIZE - 1) for column in range(GRID_SIZE)):
                        continue
            break

        durations = [d for d in range(1, len(DURATIONS) + 1) for _ in range(DURATIONS[d - 1])]
        random.shuffle(durations)

        self.zones = [[Zone(row, column, types.pop(), durations.pop(), durations.pop()) for column in range(GRID_SIZE)]
                      for row in range(GRID_SIZE)]

    def is_ended(self, turn):
        return all(zone.is_all_jobs_ended(turn) for row in self.zones for zone in row)

    def copy(self):
        cs = ConstructionSite()
        for row in range(GRID_SIZE):
            for column in range(GRID_SIZE):
                cs.zones[row][column].paste(self.zones[row][column])
        return cs


class BeatThePlanReferee(Referee):
    """
    The game consists in a construction site fighting.
    2 or 4 players.

    Each player, has a construction site, cut in 4x4 zones. Each zone consists in two starting jobs of one of the four
    following types: painting, isolation, plumbing or electricity. Each player has 2 workers that can be assigned to a
    distinct job at the same time.

    The game is split into 200 turns.

    Each job has a duration between 1 and 10 turns. While a worker is assigned to a job, he or she must finish the job
    before starting another one. A player win if all the jobs of its construction site are finished first. Depending
    on the type of work, there is an additional constraint:
    - the first job of painting should end before the second one starts
    - the two jobs of isolation cannot occur at the same time
    - the second job of plumbing should occur between the start and the end of the first job
    - the first job of electricity should start before the end of the first job of each neighbor zone
    - the second job of electricity should start before the beginning of the second job of each neighbor zone

    When a player finishes the two jobs of a zone first, the duration of each unfinished job of the same zone in the
    construction sites of the other players is increased by 1.

    At each turn, the player must send two commands, one per worker, containing:
    - PASS, the worker do not start a new job
    - L C T, the worker starts the job T of the zone at coordinates L (row) and C (column)

    A player looses
    - if a worker is assigned while not available, if he or she is assigned to a non existing zone or a non existing
    job, or a job that is already started or finished,
    - if she does not send the two commands in time,
    - if she does send an incorrect command,
    - if the constraints of each type of work is not satisfied
    The score of the player is then -1.

    A player win if the construction site is finisehd, if all the other players loose the game or when all the turns are
    achieved. The score of the player is the number of achieved zones.

    """

    def __init__(self):

        super().__init__()

        # List of construction sites for each player
        self.construction_site = None

        # List of booleans for each zone, to check if the zone has already been ended by some player
        self.ended_zones = None

        # List of workers for each player
        self.workers = None

        # Score of each player
        self.scores = None

        # Build instance to manage the shapes of the game
        GuiManager(self)

    @staticmethod
    def get_author():
        return "Dimitri Watel"

    @staticmethod
    def get_description():
        return "A game where workers tries to finish a construction site before others."

    @staticmethod
    def allowed_number_of_players():
        return [2, 3, 4]

    def add_worker(self, player, is_woman):
        self.workers[player].append(Worker(is_woman))

    def _init(self):
        gm = GuiManager.get_gui_manager()
        gm.clear()

        cs = ConstructionSite()
        self.ended_zones = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.scores = {player: 0 for player in self.players}

        gm.build_static_graphics()
        gm.build_construction_sites(cs)
        gm.build_scores()
        gm.build_pauses_zones()

        self.construction_site = {player: ConstructionSite() for player in self.players}
        for player in self.players:
            self.construction_site[player] = cs.copy()

        self.workers = {player: [] for player in self.players}
        for player in self.players:
            for i in range(NB_WORKERS):
                self.add_worker(player, i % 2 == 0)
            gm.add_workers(player)

        for i, player in enumerate(self.players):
            player.send_input_line_nl(input_msg=[len(self.players), i + 1])

        for row in range(GRID_SIZE):
            for column in range(GRID_SIZE):
                zone = cs.zones[row][column]
                Player.send_input_line_nl_to_all_players(self.players, [row, column, zone.type,
                                                                             zone.get_duration(FIRST_JOB),
                                                                             zone.get_duration(SECOND_JOB)])

    def _end(self):
        """
        Nothing is done at the end of this referee
        :return:
        """
        pass

    def destroy(self, turn, player, message):
        if message.strip() != '':
            player.send_game_infos(message)
        player.loose()

    def end_all_players(self, msg):
        for player in self.players:
            if not player.is_playing:
                continue

            player.send_game_infos(msg)
            player.win(self.scores[player])

    def check_last_turn(self, turn):
        if turn <= LAST_TURN:
            return False

        self.end_all_players(LAST_TURN_MSG)
        return True

    def check_win(self):
        stop = False
        for player, score in self.scores.items():
            if player.is_playing and score >= WIN_SCORE:
                player.send_game_infos(WINNING_SCORE_MSG)
                player.win(self.scores[player])
                stop = True

        if stop:
            self.end_all_players(WINNING_END_MSG)

        return stop

    def update_scores(self, turn):
        gm = GuiManager.get_gui_manager()
        for player in self.players:
            if not player.is_playing:
                continue

            gm.edit_score(turn, player, self.scores[player])

    def read_player_output(self, turn, player, player_output, worker):
        """
        Read the player output and assign the worker accordingly.
        If the output is malformed, the player loose
        """
        outputs = player_output.strip()

        if outputs == "PASS":
            # No assignment
            return

        if worker.is_working:
            self.destroy(turn, player, WORKER_WOMAN_ERROR if worker.is_woman else WORKER_MAN_ERROR)
            return

        outputs = outputs.split(' ')
        if len(outputs) != 3:
            self.destroy(turn, player, COMMAND_ERROR)
            return

        try:
            outputs = [int(x) for x in outputs]
        except ValueError:
            self.destroy(turn, player, COMMAND_ERROR)
            return

        row, column, job = outputs
        if row < 0 or row > 3 or column < 0 or column > 3:
            self.destroy(turn, player, OUT_OF_THE_GRID_ERROR % (row, column))
            return
        if job < 0 or job > 1:
            self.destroy(turn, player, NO_JOB_ERROR % job)
            return

        cs = self.construction_site[player]
        zone = cs.zones[row][column]
        if zone.is_started(job):
            self.destroy(turn, player, JOB_DONE_ERROR % (row, column, job))
            return

        zone.start(job, turn)
        worker.work(zone, job)
        gm = GuiManager.get_gui_manager()
        gm.start_job(turn, player, zone, job, worker, True)

    def send_first_input_to_players(self):

        # Send, for each player, the number of the player, FALSE if the player has lost and TRUE otherwise, and
        # the score of the player
        # If a player has lost, send -1 instead of each coordinate
        for player in self.players:
            Player.send_input_line_nl_to_all_players(players=self.players,
                                                     input_msg=[player.id + 1, player.is_playing, self.scores[player]])

    def read_output_from_players(self, turn):
        """
        Read the output of all the players, assign workers accordingly
        """
        for player in self.players:
            if not player.is_playing:
                continue

            for worker in self.workers[player]:
                player_output = player.get_output_line()
                # If player returned no output
                if player_output is None:
                    break

                self.read_player_output(turn, player, player_output, worker)

    def send_second_input_to_players(self, turn):
        # Send the starting and ending jobs of each player
        gm = GuiManager.get_gui_manager()

        # List the starting and ending jobs
        starting_jobs = []
        ending_jobs = []

        for player in self.players:
            if not player.is_playing:
                continue

            for i, worker in enumerate(self.workers[player]):
                if not worker.is_working:
                    continue
                else:
                    zone = worker.current_working_zone
                    job = worker.current_working_job

                    gm.update_job_slider(turn, player, zone, job)

                    if zone.start_turn(job) == turn:
                        starting_jobs.append((player.id + 1, i, zone.row, zone.column, job))
                    if zone.last_turn(job) == turn:
                        ending_jobs.append((player.id + 1, i, zone.row, zone.column, job))

        Player.send_input_line_nl_to_all_players(players=self.players,
                                                 input_msg=[len(starting_jobs), len(ending_jobs)])

        for job_info in starting_jobs + ending_jobs:
            Player.send_input_line_nl_to_all_players(players=self.players,
                                                     input_msg=job_info)

    def check_zones_constraints(self, turn):
        for player in self.players:
            if not player.is_playing:
                continue
            cs = self.construction_site[player]
            for row in range(GRID_SIZE):
                for column in range(GRID_SIZE):
                    zone = cs.zones[row][column]
                    neighbor_zones = []
                    if row != 0:
                        neighbor_zones.append(cs.zones[row - 1][column])
                    if row != 3:
                        neighbor_zones.append(cs.zones[row + 1][column])
                    if column != 0:
                        neighbor_zones.append(cs.zones[row][column - 1])
                    if column != 3:
                        neighbor_zones.append(cs.zones[row][column + 1])
                    job_error = zone.check_constraint(turn, neighbor_zones)
                    if job_error is not None:
                        self.destroy(turn, player, job_error)
                        break
                if not player.is_playing:
                     break

    def end_finished_jobs(self, turn):
        # Stop all ending jobs and update the scores
        gm = GuiManager.get_gui_manager()

        for player in self.players:
            if not player.is_playing:
                continue

            for i, worker in enumerate(self.workers[player]):
                if not worker.is_working:
                    continue
                else:
                    zone = worker.current_working_zone
                    job = worker.current_working_job
                    if zone.last_turn(job) == turn:
                        worker.stop_working()
                        gm.start_job(turn, player, zone, job, worker, False)

                    # Update score if zone is finished
                    if zone.is_finished_for_the_first_time(turn):
                        self.scores[player] += 1
                        # Check if this is the first time the zone is ended and update duration of same jobs of other
                        # players
                        if self.ended_zones[zone.row][zone.column]:
                            continue

                        self.ended_zones[zone.row][zone.column] = True

                        # Increase duration of not ended jobs of same zone of other players
                        for player2 in self.players:
                            if player2 == player:
                                continue
                            cs = self.construction_site[player2]
                            ozone = cs.zones[zone.row][zone.column]
                            for ojob in [FIRST_JOB, SECOND_JOB]:
                                if not ozone.is_started(ojob) or ozone.last_turn(ojob) > turn:
                                    ozone.increase_duration(ojob)
                                    gm.increase_job_duration(turn, player2, ozone, ojob)

        # Update graphics
        self.update_scores(turn)

    def _game_turn(self, turn):

        # Check last turn
        if self.check_last_turn(turn):
            return

        final_players = [player for player in self.players if player.is_playing]
        if len(final_players) == 1:
            final_players[0].send_game_infos(ONE_PLAYER_LEFT)
            final_players[0].win(self.scores[final_players[0]])
            return

        if self.check_win():
            return

        # Send first part of the input to the players
        self.send_first_input_to_players()

        # Read the output of all the players, assign workers accordingly
        self.read_output_from_players(turn)

        # Check of constraints
        self.check_zones_constraints(turn)

        # Send second part of the input to the players
        self.send_second_input_to_players(turn)

        self.end_finished_jobs(turn)

    def _get_x_max(self):
        return XMAX

    def _get_y_max(self):
        return YMAX
