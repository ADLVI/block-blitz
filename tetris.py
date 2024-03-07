import copy
import curses
import random as rand
import time

import numpy as np

scr = curses.initscr()
curses.noecho()
curses.cbreak()
curses.start_color()
scr.keypad(True)
scr.nodelay(True)
LINE_PER_LEVEL = 1

MAXY, MAXX = scr.getmaxyx()
MAXY = MAXY - 1
MAXX = MAXX // 2 - 1
WINX, WINY = 30, int(0.95 * MAXY)  # MAXX - 4, MAXY - 2
XOFFSET = 15
YOFFSET = 2
EMPTY = " "
BREAK = "#"  # curses.ACS_CKBOARD
INIT_OFFSET = WINX // 4 * 2  # SHOULD ALEAYS BE EVEN
SAMPLE_XOFFSET = XOFFSET + WINX * 2 + 2
SAMPLE_YOFFSET = 4
INFO_XOFFSET = XOFFSET + WINX * 2 + 2
INFO_YOFFSET = 13
# scr.addch(MAXY // 2, MAXX // 2, "X")  # curses.ACS_CKBOARD)
scr.scrollok(False)
SPEED = 2
MAX_TEMP_IN_END = 2
MOVE_BLOCKS = 2
sample_box = scr.subwin(10, 10 *2, SAMPLE_YOFFSET - 1, SAMPLE_XOFFSET - 1)
sample_box.box()
game_box = scr.subwin(WINY,WINX*2,YOFFSET, XOFFSET)
game_box.box()
for color in [curses.COLOR_BLUE,curses.COLOR_MAGENTA, curses.COLOR_GREEN,curses.COLOR_RED,curses.COLOR_CYAN]:
    curses.init_pair(color, color, color)
ACTIONS = {
        curses.KEY_RIGHT:">",
        curses.KEY_LEFT:"<",
        curses.KEY_UP:'^',
        curses.KEY_DOWN:'v',
        " ":'@'
        }
DESIGN_LOCATIONS = {
        'action': [0,WINX * 2],
        'temp': [0, 0],
        'info': [MAXY-1, 0]
        }
def show_info(stack,data):
    try:
        # check is stack is string
        #location = stack
        if isinstance(stack, str):
            stack = DESIGN_LOCATIONS[stack]
        stack = [min(stack[0], MAXY - 1), min(stack[1], MAXX - 1)]
        scr.addstr(*stack, str(data).replace("\n", " ") )
    except Exception as e:
        scr.addstr(1, 0, str(e))


def rotate(p, origin=(0, 0), degrees=0):
    angle = np.deg2rad(degrees)
    R = np.array(
        [
            [int(np.cos(angle)), -int(np.sin(angle))],
            [int(np.sin(angle)), int(np.cos(angle))],
        ]
    )
    o = np.atleast_2d(origin)
    p = np.atleast_2d(p)
    return np.squeeze((R.dot(p.T - o.T) + o.T).T)


def diff(li1, li2):
    temp3 = []
    for element in li1:
        if element not in li2:
            temp3.append(element)
    return temp3


def get_first_not_present(ls):
    a = ls[0]
    for num in ls[1:]:
        if num != a - 1:
            return num
        a = num
    return a - 1



class Shape:
    points = None
    rotate_offset = 0

    def __init__(self, label, points, color=None):
        self.points = points
        self.color = color if color else curses.COLOR_RED
        self.label = label
        #self.center_idx = center_idx if center_idx else len(points) // 2
        self.adjust()
        self.align()

    def draw(self):
        # scr.addstr(0, WINX, str(self))
        for point in self.points:
            low , _ = self.get_low_and_heigh()
            left , _ = self.get_left_and_right()
            if(point[1] > 0 and point[1] < WINY-1 and point[0] > 0 and point[0] < WINX -1):
                game_box.addch(point[1], point[0] * 2, BREAK, curses.color_pair(self.color))
                game_box.addch(point[1], point[0] * 2 +1, BREAK, curses.color_pair(self.color))
    def make_sample(self):
        sample_box.clear()
        sample_box.box()
        sample = copy.deepcopy(self.points)
        low , _ = self.get_low_and_heigh()
        left , right = self.get_left_and_right()
        sample_box.addstr("Next:")
        for point in sample:
            point[0] -= left[0]
            point[1] -= low[1]
            sample_box.addch(point[1]+1, point[0] *2+0+ left[0]//2, BREAK,curses.color_pair(self.color))
            sample_box.addch(point[1]+1, point[0] *2+1+ left[0]//2, BREAK,curses.color_pair(self.color))
    def fall(self):
        for point in self.points:
            point[1] += 1

    def get_low_and_heigh(self, temp = None):
        temp = self.points if temp is None else temp
        low = temp[0]
        heigh = temp[0]
        for point in temp:
            if point[1] < low[1]:
                low = point
            elif point[1] > heigh[1]:
                heigh = point
        return copy.deepcopy((low, heigh))

    def get_left_and_right(self, temp = None):
        temp = self.points if temp is None else temp
        left = temp[0]
        right = temp[0]
        for point in temp:
            if point[0] < left[0]:
                left = point
            elif point[0] > right[0]:
                right = point
        return copy.deepcopy((left, right))

    def rotate(self, apply=True, count = 1):
        if self.label == "O" or count % 4 == 0:
            copy.deepcopy(self.points)
        # Rotate 90 degrees about point in center_idx clockwise
        temp = copy.deepcopy(self.points)  # self.points.copy()
       # cx, cy = temp[self.center_idx]
        temp = (
            rotate(temp, self.get_center_point(), 90*count)
            .astype(np.int32)
            .__array__()
        )
        temp = self.adjust(temp)
        if apply:
            self.set_points(temp)
        return copy.deepcopy(temp)
    def get_center_point(self):
        left, right = self.get_left_and_right()
        low, heigh = self.get_low_and_heigh() 
        return [(right[0]+left[0])//2, (heigh[1]+low[1])//2]

    def shift(self, adjust=-1, temp=None):
        set_then = temp is  None
        temp = copy.deepcopy(self.points) if temp is None else temp
        for point in temp:
            point[0] += adjust
        if set_then:
            self.points = temp
        return temp

    def should_adjust(self, temp=None):
        temp = self.points if temp is None else temp
        _, right = self.get_left_and_right(temp)
        return right[0] % 2 == 1

    def can_adjust(self, adjust=-1, temp=None):
        temp = self.points if temp is None else temp
        for tmp in temp:
            if tmp[0] + adjust > WINX - 2 or tmp[0] + adjust < 1:
                return False
        return True

    def set_points(self, points):
        self.points = copy.deepcopy(points)
        if self.should_adjust():
            self.shift(-1)

    def adjust(self, temp=None):
        set_then = temp is None
        temp = copy.deepcopy(self.points) if temp is None else temp
        if self.should_adjust(temp):
            if self.can_adjust(-1, temp=temp):
                temp = self.shift(-1, temp=temp)
            elif self.can_adjust(1, temp=temp):
                temp = self.shift(1, temp=temp)
        if set_then:
            self.set_points(temp)
        return temp
    def align(self, temp = None):
        set_then = temp is None
        temp = copy.deepcopy(self.points) if temp is None else temp
        low, heigh = self.get_low_and_heigh()
        cnt = heigh[1] - low[1] -1
        for point in temp:
            point[1] -= cnt
        if set_then:
            self.points = temp
        return temp
    def __str__(self):
        return str(self.points)


class Game:
    trying_action = False
    game = None
    current_done = False
    last_lowest = None
    last_heighest = None
    temp = 0
    last_time = 0
    should_refresh = False
    lines = 0
    current = None
    next_shape = None

    def __init__(self):
        # init 2d list with char values struct
        self.game = [[[EMPTY, 0] for _ in range(WINX + 1)] for _ in range(WINY + 1)]
        self.current = self.get_random_shape()
        self.last_time = time.time()

    def frame(self):
        game_box.box()
        return
        i = 0
        for row in range(WINY):
            if row == 0 or row == WINY - 1:
                scr.addstr(YOFFSET + row, XOFFSET, "--" * (WINX))  #
            else:
                cr = '/' if i % 2 == 0 else '\\'
                # scr.addstr(
                #     0,
                #     0,
                #     f"maxx: {MAXX} maxy: {MAXY} yoffset: {YOFFSET} XOFFSET: {XOFFSET} y+row : {YOFFSET + row} ,x+winx: {XOFFSET + WINX * 2}",
                # )
                i += 1
                scr.addch(YOFFSET + row, XOFFSET, cr)
                scr.addch(YOFFSET + row, XOFFSET + WINX * 2, cr)

    def draw(self):
        self.frame()
        game_box.clear()
        game_box.box()
        for j, row in enumerate(self.game):
            for i, cell in enumerate(row):
                if 0 in [i, j] or j>= WINY-1 or i>= WINX - 1:
                    continue
                game_box.addch(j, i*2, cell[0], curses.color_pair(cell[1]))
                game_box.addch(j, i*2+1, cell[0], curses.color_pair(cell[1]))
        self.current.draw()
        self.draw_info()
        self.next_shape.make_sample()
        self.should_refresh = False
    def draw_info(self):
        scr.addstr(INFO_YOFFSET, INFO_XOFFSET , f"LINES : {self.lines}")
        scr.addstr(INFO_YOFFSET + 1, INFO_XOFFSET , f"LVL : {self.get_level()}")
    def update(self):
        # scr.addstr(MAXY // 2, MAXX * 3 // 2, str(self.dt()))
        # scr.addch(MAXY // 2, MAXX // 2, "X")
        if self.current_done:
            show_info('temp',f"Count Down: {MAX_TEMP_IN_END-self.temp}")
            if self.temp >= MAX_TEMP_IN_END and not self.can_fall():
                #MOVED FROM BELOW
                self.last_lowest, self.last_heighest = self.current.get_low_and_heigh()
                self.merge()
                self.tetris()

                self.get_random_shape()
                self.current_done = False
                self.temp = 0
            elif self.dt_passed():
                if not self.can_fall():
                    # Start count down because can fall any more
                    self.temp += 1
                else:
                    # fixed bug
                    self.current_done = False
                    self.temp = 0
                self.last_time = time.time()
            #self.get_random_shape()
            #self.current_done = False
        else:
            if self.current and self.can_fall():
                if self.dt_passed():
                    scr.addstr(1, 1, "True")
                    self.should_refresh = True
                    self.current.fall()
                    self.last_time = time.time()
            else:
                # DEBUG
                scr.addstr(1, 1, "False")
                self.current_done = True
                #self.last_time = time.time()
                # get lowset and heighes point logation of shape to chck that range for finding any tetris
        if self.dt_passed() or self.should_refresh:
            scr.clear()
            self.draw()
        # scr.addstr(MAXY // 2, MAXX // 2, "END OF UPDATE")

    def tetris(self):
        if self.current_done:
            to_tetris = []
            for row in range(self.last_lowest[1],self.last_heighest[1] +1 ):
                if all(self.game[row][col][0] == BREAK for col in range(1, WINX - 1)):
                    to_tetris.append(row)
                    del self.game[row]
                    del self.game[row] # to fix remove +1 -> because list keys reset in del
                    self.game.insert(1, [[EMPTY, 0]] * (WINX ))
                    self.game.insert(1, [[EMPTY, 0]] * (WINX ))
            if len(to_tetris) == 0:
                return False
            self.lines += len(to_tetris)

    def action(self, action):
        if self.trying_action:
            return False
        self.trying_action = True
        temp = copy.deepcopy(self.current.points)
        # self.should_refresh = False
        # DEBUG
        if action in ACTIONS:
            show_info('action', "ACTION : " + str(temp)[:10])
        if action == curses.KEY_RIGHT:
            for point in temp:
                if (
                    point[0] + MOVE_BLOCKS > WINX - 2
                    or self.game[point[1]][point[0] + MOVE_BLOCKS][0] == BREAK
                ):
                    scr.addstr(0, 0, str(point))
                    scr.refresh()
                    # exit()
                    return False
                point[0] += MOVE_BLOCKS
            self.current.set_points(temp)
        elif action == curses.KEY_LEFT:
            for point in temp:
                if (
                    point[0] - MOVE_BLOCKS < 1
                    or self.game[point[1]][point[0] - MOVE_BLOCKS][0] == BREAK
                ):
                    return False
                point[0] -= MOVE_BLOCKS
            self.current.set_points(temp)
        elif action == curses.KEY_DOWN:
            for point in temp:
                point[1] -= 1
                if point[1] > WINY - 2 or self.game[point[1]][point[0]][0] == BREAK:
                    return False
            self.current.set_points(temp)
        elif action == curses.KEY_UP:
            step = 0
            ok = True
            _ , heigh = self.current.get_low_and_heigh()
            curidx_y = heigh[1] #temp[self.current.center_idx][1]
            target = 0
            while ok and WINY - curidx_y - step:
                for point in temp:
                    if (
                        point[1] + step >= WINY - 2
                        or self.game[point[1] + step][point[0]][0] == BREAK
                    ):
                        target = step - 1
                        ok = False
                        break
                step += 1
            for point in self.current.points:
                point[1] += target
                point[1] = WINY - 2 if point[1] > WINY - 2 else point[1]
        # rotate with space

        elif action == ord(" "):
            temp = self.current.rotate(False)
            for point in temp:
                if (
                    #point[1] < 1
                    point[1] > WINY - 2
                    or point[0] > WINX - 2
                    or point[0] < 1
                    or self.game[point[1]][point[0]][0] == BREAK
                ):
                    return False
            # self.current.draw()
            self.current.set_points(temp)
            show_info("info", temp)
            #self.current.rotate_offset += 1
            #self.current.shift(-2)
        else:
            return False
        self.should_refresh = True

    def merge(self):
        for point in self.current.points:
            if point[1] > WINY - 2:
                point[1] = WINY
            if point[0] > WINX - 2:
                point[1] = WINX - 2
            elif point[0] < 1:
                point[1] = 1
            self.game[point[1]][point[0]] = [BREAK, self.current.color]

    def can_fall(self):
        for point in self.current.points:
            if (
                point[1] >= WINY - 2
                or (point[1] > 0 and self.game[point[1] + 1][point[0]][0] == BREAK)
            ):
                return False
        return True
    def get_level(self):
        return self.lines // LINE_PER_LEVEL
    def dt(self):
        return time.time() - self.last_time
    def dt_passed(self):
        return self.dt() > (1 / (SPEED + self.get_level()))

    def is_game_over(self):
        if not self.current_done or self.can_fall() :
            return False
        for point in self.current.points:
            if self.game[1][point[0]][0] == BREAK:
                # DEBUG
                show_info([2, 20], str(self.game[1][point[0]]) + " " + str(point))
                #self.game_dump()
                return True
        return False
    
    def game_dump(self):
        j = 0
        for r in self.game:
            i = 0
            for c in r:
                scr.addstr(j, i, c[0]+ " ")
                i += 1
            j +=1

    def get_random_shape(self):
        shapes = {
            "L": {
                "points": [
                    [0, 0],
                    [0, 1],
                    [0, 2],
                    [0, 3],
                    [0, 4],
                    [0, 5],
                    [1, 0],
                    [1, 1],
                    [1, 2],
                    [1, 3],
                    [1, 4],
                    [1, 5],
                    [2, 0],
                    [2, 1],
                    [3, 0],
                    [3, 1],
                ],
                "color": curses.COLOR_BLUE,
                #"center_idx": 1,
            },
            "J": {
                "points": [
                    [3, 0],
                    [3, 1],
                    [3, 2],
                    [3, 3],
                    [3, 4],
                    [3, 5],
                    [2, 0],
                    [2, 1],
                    [2, 2],
                    [2, 3],
                    [2, 4],
                    [2, 5],
                    [1, 0],
                    [1, 1],
                    [0, 0],
                    [0, 1],
                ],
                "color": curses.COLOR_CYAN,
                #"center_idx": 15,
            },
            "O": {
                "points": [
                    [0, 0],
                    [1, 0],
                    [2, 0],
                    [3, 0],
                    [0, 1],
                    [1, 1],
                    [2, 1],
                    [3, 1],
                    [0, 2],
                    [1, 2],
                    [2, 2],
                    [3, 2],
                    [0, 3],
                    [1, 3],
                    [2, 3],
                    [3, 3],
                ],
                "color": curses.COLOR_RED,
                #"center_idx": 6,
            },
            "S": {
                "points": [
                    [0, 0],
                    [1, 0],
                    [2, 0],
                    [3, 0],
                    [0, 1],
                    [1, 1],
                    [2, 1],
                    [3, 1],
                    [2, 2],
                    [3, 2],
                    [4, 2],
                    [5, 2],
                    [2, 3],
                    [3, 3],
                    [4, 3],
                    [5, 3],
                ],
                "color": curses.COLOR_GREEN,
                #"center_idx": 6,
            },
            "Z": {
                "points": [
                    [2, 0],
                    [3, 0],
                    [4, 0],
                    [5, 0],
                    [2, 1],
                    [3, 1],
                    [4, 1],
                    [5, 1],
                    [0, 2],
                    [1, 2],
                    [2, 2],
                    [3, 2],
                    [0, 3],
                    [1, 3],
                    [2, 3],
                    [3, 3],
                ],
                "color": curses.COLOR_MAGENTA,
                #"center_idx": 12,
            },
            "I": {
                "points": [
                    [0, 0],
                    [0, 1],
                    [0, 2],
                    [0, 3],
                    [0, 4],
                    [0, 5],
                    [0, 6],
                    [0, 7],
                    [1, 0],
                    [1, 1],
                    [1, 2],
                    [1, 3],
                    [1, 4],
                    [1, 5],
                    [1, 6],
                    [1, 7],
                ],
                "color": curses.COLOR_MAGENTA,
                #"center_idx": 3,
            },
            "T": {
                "points": [
                    [0, 0],
                    [0, 1],
                    [0, 2],
                    [0, 3],
                    [0, 4],
                    [0, 5],
                    [1, 0],
                    [1, 1],
                    [1, 2],
                    [1, 3],
                    [1, 4],
                    [1, 5],
                    [2, 2],
                    [2, 3],
                    [3, 2],
                    [3, 3]
                ],
                "color": curses.COLOR_MAGENTA,
                #"center_idx": 3,
            },
        }
        np.random.normal(0, 0.1, (MAXY, MAXX))
        # normal random choice from shapes
        
        label = None
        if self.next_shape is None:
            label = rand.choice(list(shapes.keys()))
            shape = copy.deepcopy(shapes[label])
            self.current = self.gen_normal_shape(label, shape)
        else:
            self.current = self.next_shape
        while True:
            label_next = rand.choice(list(shapes.keys()))
            if (label_next != label) or  rand.random() < 0.3:
                next_shape = copy.deepcopy(shapes[label_next])
                self.next_shape = self.gen_normal_shape(label_next, next_shape)
                break
        self.current_done = False
        return self.current
    def gen_normal_shape(self, label, data):
        data = copy.deepcopy(data)
        for point in data["points"]:
            point[0] += INIT_OFFSET
        shape = Shape(label, **data)
        shape.rotate(count = rand.randint(0, 4))
        return shape


def main():
    PLAYING = True
    scr.clear()
    game = Game()
    buffer_action = -1
    while PLAYING:
        game.update()
        if game.is_game_over():
            PLAYING = False
            scr.addstr(YOFFSET + WINY, XOFFSET + WINX, "GAME OVER")
            scr.refresh()
            break
        try:
            action = scr.getch()
            while aa := scr.getch() != -1:
                buffer_action = aa
            # purg buffer
            game.action(action)
            time.sleep(1 / 100)
            game.trying_action = False
        #     while not scr.getch():
        #         pass
        except KeyboardInterrupt:
            if buffer_action != -1:
                game.action(buffer_action)
                buffer_action = -1
            # if game.should_refresh:
        # paying = scr.getch() != -1
        time.sleep(1 / 100)


if __name__ == "__main__":
    main()
time.sleep(3)
curses.endwin()
scr.clear()
