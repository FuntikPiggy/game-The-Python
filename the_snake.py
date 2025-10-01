import os
import shelve
import sys
from random import choice, choices, randint

import pygame as pg

from sounds import play_music, play_sound, prodigy


try:
   wd = sys._MEIPASS
except AttributeError:
   wd = os.getcwd()
file_path = os.path.join(wd,)

# Константы для размеров поля и сетки:
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
CENTER_GRID = (GRID_WIDTH // 2 * GRID_SIZE, GRID_HEIGHT // 2 * GRID_SIZE)
ALL_CELLS = set(
    (x * GRID_SIZE, y * GRID_SIZE)
    for x in range(GRID_WIDTH)
    for y in range(GRID_HEIGHT)
)

# Направления движения:
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRS_N_REVERSES = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
BOARD_BACKGROUND_COLOR = (150, 150, 150)
BORDER_COLOR = (0, 0, 0)
APPLE_COLOR = (153, 24, 24)
UNRIPE_COLOR = (100, 25, 100)
SNAKE_COLOR = (40, 138, 68)
HEAD_COLOR = tuple(int(i // 4 * 3) for i in SNAKE_COLOR)
EYE_C1 = GRID_SIZE // 4
EYE_C2 = GRID_SIZE // 4 * 3
EYES_COLOR = BORDER_COLOR
EYES_GOOD_BLINK_COLOR = (255, 255, 0)
EYES_BAD_BLINK_COLOR = (255, 0, 0)
CRASH_COLOR = (87, 2, 2)
FONT_COLOR = (255, 136, 0)
SPEED = 10
FONT_NAME = os.path.join(wd, 'fonts', 'SmallestPixel7.ttf')
BG_IMAGE = os.path.join(wd, 'images', 'background.png')
LOGO_IMAGE = os.path.join(wd, 'images', 'Funtik_ava.gif')

game_type = 1
is_action = False  # Процесс игры / меню
is_welcome = False  # Меню начальное / нет
is_game_over = False  # Меню gameover / нет
# Настройка игрового окна:
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
background = pg.image.load(BG_IMAGE)
background = pg.transform.smoothscale(background, screen.get_size())
screen.blit(background, (0, 0))


def save_record(record: int) -> None:
    """Сохраняет новый рекорд"""
    with shelve.open('record.txt') as ofl:
        if game_type == 1:
            ofl['record1'] = record
        else:
            ofl['record2'] = record


def load_record() -> int:
    """Загружает рекорд из файла"""
    try:
        with shelve.open('record.txt') as ifl:
            if game_type == 1:
                record = ifl['record1']
            else:
                record = ifl['record2']
    except KeyError:
        record = 0
    return record


def modify_caption(record: int, g_type: int = 1) -> None:
    """Изменяет заголовок окна"""
    pg.display.set_caption(
        '-=ПиТоН=-  | "Esc" - выход | '
        '"r" - сброс | "m" - музыка | '
        f'режим игры - {g_type} | Рекорд - {record}'
    )


top_scores = load_record()
modify_caption(top_scores)

# Настройка времени:
clock = pg.time.Clock()


class GameObject:
    """Класс описывает объекты игры. Абстрактный класс"""

    def __init__(self, color: tuple = BORDER_COLOR) -> None:
        self.position: tuple = CENTER_GRID
        self.body_color = color
        self.to_erase: set = set()

    def draw(self) -> None:
        """Отрисовывает экземпляр класса."""

    def erase(self) -> None:
        """Восстанавливает фон под устаревшими сегментами экземпляра класса."""
        for i in self.to_erase:
            self.erase_one_cell(i)
        self.to_erase.clear()

    def draw_one_cell(self, position: tuple, color=None) -> None:
        """Отрисовывает один сегмент (клетка поля) экземпляра класса."""
        color = color or self.body_color
        rect = pg.Rect(*position, *(GRID_SIZE,) * 2)
        pg.draw.rect(screen, color, rect)
        pg.draw.rect(screen, BORDER_COLOR, rect, 2)

    @staticmethod
    def erase_one_cell(position: tuple) -> None:
        """Восстанавливает фон под одним сегментом экземпляра класса."""
        sprite_rect = pg.Rect(*position, *(GRID_SIZE,) * 2)
        sprite_image = background.subsurface(sprite_rect)
        screen.blit(sprite_image, position)


class Apple(GameObject):
    """Класс описывает объект игры яблоко."""

    def __init__(self, busy_cells: set = None,
                 is_unripe: bool = False) -> None:
        super().__init__([APPLE_COLOR, UNRIPE_COLOR][is_unripe])
        busy_cells = busy_cells or set()
        self.randomize_position(busy_cells)
        self.is_unripe = is_unripe

    def randomize_position(self, busy_cells):
        """Задаёт случайную позицию яблоку."""
        self.position = choice(tuple(ALL_CELLS - busy_cells))

    def draw(self):
        """Отрисовывает яблоко."""
        self.draw_one_cell(self.position)


class Snake(GameObject):
    """Класс описывает объект игры змейку."""

    def __init__(self, color: tuple = SNAKE_COLOR) -> None:
        super().__init__(color)
        self.reset()

    def reset(self) -> None:
        """Сбрасывает змейку в начальное состояние."""
        self.length: int = 1
        self.positions: list = [self.position]  # , None]
        self.direction: tuple[int, int] = choice(list(DIRS_N_REVERSES))
        self.eye_color: tuple = EYES_COLOR
        self.redir_available = True

    def add_sub_apple(self, is_unripe: bool):
        """Изменяет длину при съедении яблока."""
        if is_unripe:
            self.eye_color = EYES_BAD_BLINK_COLOR
            if randint(1, 20) == 20:
                self.positions.extend([self.get_head_position()] * 5)
                quantity = 0
            else:
                quantity = -min(randint(2, 3), self.length - 1)
        else:
            quantity = 1
            self.eye_color = EYES_GOOD_BLINK_COLOR
        self.length += quantity

    def update_direction(self, next_direction: tuple[int, int],
                         forced: bool = False) -> None:
        """Изменяет направление движения змейки."""
        if (self.redir_available
                and self.direction != DIRS_N_REVERSES[next_direction]
                or forced):
            self.direction = next_direction
            self.redir_available = False

    @staticmethod
    def next_position(x, y, dir_x, dir_y) -> tuple:
        """Возвращает координаты следующей ячейки"""
        return ((x + dir_x * GRID_SIZE) % SCREEN_WIDTH,
                (y + dir_y * GRID_SIZE) % SCREEN_HEIGHT)

    def move(self) -> None:
        """Движение змейки. Изменяет координаты элементов змейки."""
        self.position = self.next_position(*self.position, *self.direction)
        self.positions.insert(0, self.position)
        self.redir_available = True

    def draw(self) -> None:
        """Отрисовывает змейку."""
        if len(self.positions) > self.length:
            for _ in range(len(self.positions) - self.length):
                self.erase_one_cell(self.positions.pop(-1))
        self.draw_one_cell(self.position, HEAD_COLOR)  # Отрисовка головы
        if self.length > 1:
            self.draw_one_cell(self.positions[1])
        headx, heady = self.position
        eye1_pos = (headx + [EYE_C1, EYE_C2][self.direction in (RIGHT, DOWN)],
                    heady + [EYE_C1, EYE_C2][self.direction in (LEFT, DOWN)])
        eye2_pos = (headx + [EYE_C1, EYE_C2][self.direction in (RIGHT, UP)],
                    heady + [EYE_C1, EYE_C2][self.direction in (RIGHT, DOWN)])
        pg.draw.circle(screen, self.eye_color, eye1_pos, 3)
        pg.draw.circle(screen, self.eye_color, eye2_pos, 3)
        self.eye_color = EYES_COLOR

    def crash(self) -> None:
        """Эффект ухода из жизни нашего героя."""

        for position in self.positions:
            self.draw_one_cell(position, color=CRASH_COLOR)
            pg.time.delay(30)
            pg.display.update()
        pg.time.delay(100)

    def get_head_position(self) -> tuple:
        """Возвращает координаты головы змейки."""
        return self.positions[0]


class AppleCart:
    """Корзина для яблок - когда их много во втором режиме игры"""

    def __init__(self, apple: Apple | None = None) -> None:
        self.cart = []
        if apple:
            self.cart.append(apple)

    def add_apple(self, apple: Apple):
        """Добавляет конкретное яблоко в корзину"""
        self.cart.append(apple)

    def create_apple(self, occupied_cells: list,
                     is_unripe: bool = False, quantity: int = 1):
        """Создаёт яблоко и добавляет в корзину"""
        for _ in range(quantity):
            self.cart.append(
                Apple(set(self.get_cells()) | set(occupied_cells), is_unripe)
            )

    def clear_cart(self):
        """Очищает корзину"""
        self.cart = []

    def get_cells(self):
        """Возвращает множество занятых яблоками ячеек"""
        return {i.position: i for i in self.cart}


class Button:
    """Класс описывает объект меню кнопка."""

    def __init__(self, x, y, width, height, text, t_size) -> None:
        self.x = x - width // 2
        self.y = y - height // 2
        self.onePress = True
        self.alreadyPressed = False
        self.alpha = {'normal': 110, 'hover': 5, 'pressed': 200}
        self.sprite_rect = pg.Rect(self.x, self.y, width, height)
        self.buttonSurface = pg.Surface(
            (self.sprite_rect.width, self.sprite_rect.height)
        )
        self.line_width = height // 7
        self.bord_radius = self.line_width * 2
        self.btn_rect = self.sprite_rect.inflate(*[height // 2.5] * 2)
        font = pg.font.Font(FONT_NAME, t_size)
        self.text = font.render(text, True, FONT_COLOR)
        self.text_x = x - self.text.get_rect().width // 2
        self.text_y = y - self.text.get_rect().height // 2

    def process(self):
        """Анимирует кнопку."""
        mouse_pos = pg.mouse.get_pos()
        self.buttonSurface.set_alpha(self.alpha['normal'])
        pg.draw.rect(
            screen, FONT_COLOR, self.btn_rect,
            self.line_width, self.bord_radius
        )
        screen.blit(self.text, (self.text_x, self.text_y))
        if self.sprite_rect.collidepoint(mouse_pos):
            self.buttonSurface.set_alpha(self.alpha['hover'])
            if pg.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.set_alpha(self.alpha['pressed'])
        screen.blit(self.buttonSurface, self.sprite_rect)


def change_game_type(key, apple_cart, occupied_cells):
    """Изменяет режим игры."""
    global game_type
    global top_scores
    ex_game_type = game_type
    if game_type == 1 and key == pg.K_2:
        game_type = 2
        apple_cart.create_apple(occupied_cells, quantity=2)
        apple_cart.create_apple(occupied_cells, True, 4)
    elif game_type == 2 and key == pg.K_1:
        game_type = 1
        apple_cart.clear_cart()
        apple_cart.create_apple(occupied_cells)
    if ex_game_type != game_type:
        top_scores = load_record()
        modify_caption(top_scores, game_type)


def handle_direction_keys(event, snake):
    """Функция обработки клавиш управления."""
    global is_action
    dir_keys_dict = {
        pg.K_UP: UP, pg.K_w: UP,
        pg.K_DOWN: DOWN, pg.K_s: DOWN,
        pg.K_LEFT: LEFT, pg.K_a: LEFT,
        pg.K_RIGHT: RIGHT, pg.K_d: RIGHT,
    }
    if event.key in dir_keys_dict and not is_game_over:
        snake.update_direction(dir_keys_dict[event.key], forced=is_welcome)
        if is_welcome:
            is_action = True


def handle_keys(snake: Snake, apple_cart: AppleCart,
                fade_surface=None, func=lambda x: None):
    """Функция обработки действий пользователя."""
    for event in pg.event.get():
        if (event.type == pg.QUIT
                or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)):
            pg.quit()
            raise SystemExit
        elif event.type == pg.KEYDOWN:
            handle_direction_keys(event, snake)
            if event.key == pg.K_r and is_action:
                play_sound('crash')
                snake.crash()
                snake.reset()
                show_game_over(fade_surface, background, snake, apple_cart)
            elif event.key in (pg.K_1, pg.K_2) and not is_action:
                change_game_type(event.key, apple_cart, snake.positions)
            elif event.key == pg.K_m:
                play_music()
            elif event.key == pg.K_p and pg.key.get_mods() & pg.KMOD_SHIFT:
                prodigy()  # Пасхалочка - смена музыки
        else:
            func(event)


def fade_in_out(fade_surface, background, x: int = 0, y: int = 0,
                is_fade_in: bool = True) -> None:
    """Выполняет плавное затемнение-осветление экрана"""
    fade_dest = [(0, 200, 10), (200, 0, -10)][is_fade_in]
    for alpha in range(*fade_dest):
        screen.blit(background, (x, y))
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (x, y))
        pg.display.update()
        pg.time.delay(50)


def show_text(text, size, x=SCREEN_WIDTH // 2,
              y=SCREEN_HEIGHT // 2, color=FONT_COLOR) -> None:
    """Формирует текстовые объекты для отображения на экране"""
    font = pg.font.Font(FONT_NAME, size)
    text = font.render(text, True, color)
    text_rect = text.get_rect()
    text_rect.center = (x, y)
    screen.blit(text, text_rect)


def show_welcome(fade_surface, background, snake, apple_cart) -> None:
    """Окно приветствия"""
    def welcome_handles(event):
        global is_action
        if (event.type == pg.MOUSEBUTTONDOWN
                and start_btn.sprite_rect.collidepoint(mouse_pos)):
            play_sound('click')
            snake.update_direction(choice(list(DIRS_N_REVERSES)))
            is_action = True

    global is_action
    global is_welcome
    is_welcome = True
    show_text('-=Питон=-', 140, y=SCREEN_HEIGHT // 9 * 2)
    start_btn = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                       450, 50, 'Нажимай и погнали!', 45)
    show_text('( Или нажми одну из кнопок управления )',
              20, y=SCREEN_HEIGHT // 8 * 5)
    show_text('Управление:   "W-A-S-D"   или стрелки   "UP-LEFT-DOWN-RIGHT"',
              20, y=SCREEN_HEIGHT // 14 * 10)
    show_text('Выбрать режим игры - кнопки "1-2"',
              20, y=SCREEN_HEIGHT // 14 * 11)
    show_text('Плохим яблоком можно слегка отравиться, а можно и ...',
              20, y=SCREEN_HEIGHT // 14 * 12)
    show_text('Также загляни в заголовок окна', 20, y=SCREEN_HEIGHT // 14 * 13)
    logo = pg.image.load(LOGO_IMAGE)
    logo = pg.transform.scale(logo, (50, 50))
    screen.blit(logo, (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 60))
    btn_hover_flag = True
    while not is_action:
        start_btn.process()
        mouse_pos = pg.mouse.get_pos()
        if start_btn.sprite_rect.collidepoint(mouse_pos) and btn_hover_flag:
            play_sound('hover')
            btn_hover_flag = False
        if not start_btn.sprite_rect.collidepoint(mouse_pos):
            btn_hover_flag = True
        handle_keys(snake, apple_cart, fade_surface, welcome_handles)
        pg.display.update()
    fade_in_out(fade_surface, background)
    is_welcome = False


def show_game_over(fade_surface, background, snake, apple_cart) -> None:
    """Окно окончания игры"""
    def game_over_handles(event):
        global is_action
        if (event.type == pg.MOUSEBUTTONDOWN
                and stop_btn.sprite_rect.collidepoint(mouse_pos)):
            play_sound('click')
            pg.time.delay(100)
            pg.quit()
            raise SystemExit
        if (event.type == pg.MOUSEBUTTONDOWN
                and start_btn.sprite_rect.collidepoint(mouse_pos)):
            play_sound('click')
            snake.update_direction(choice(list(DIRS_N_REVERSES)))
            fade_in_out(fade_surface, background)
            is_action = True

    global is_action
    global is_game_over
    global top_scores
    is_action = False
    is_game_over = True
    cnt = snake.length - 1
    snake.reset()
    fade_in_out(fade_surface, background, is_fade_in=False)
    show_text('Игра окончена', 90, y=SCREEN_HEIGHT // 4)
    show_text(f'Яблок съедено - {cnt} шт', 55, y=SCREEN_HEIGHT // 2)
    if cnt > top_scores:
        show_text(
            'Поздравляю тебя, это новый рекорд!!!', 20,
            y=SCREEN_HEIGHT // 5 * 3, color=APPLE_COLOR)
        save_record(cnt)
        top_scores = load_record()
        modify_caption(top_scores, game_type)
        play_sound('ta_dam')
    start_btn = Button(SCREEN_WIDTH // 9 * 2, SCREEN_HEIGHT // 4 * 3,
                       150, 30, 'Повторим!', 25)
    stop_btn = Button(SCREEN_WIDTH // 19 * 13, SCREEN_HEIGHT // 4 * 3,
                      300, 30, 'Хватит, заканчиваем!', 25)
    pg.display.update()
    btn_hover_flag = True
    while not is_action:
        start_btn.process()
        stop_btn.process()
        mouse_pos = pg.mouse.get_pos()
        if ((start_btn.sprite_rect.collidepoint(mouse_pos)
            or stop_btn.sprite_rect.collidepoint(mouse_pos))
                and btn_hover_flag):
            play_sound('hover')
            btn_hover_flag = False
        if not (stop_btn.sprite_rect.collidepoint(mouse_pos)
                or start_btn.sprite_rect.collidepoint(mouse_pos)):
            btn_hover_flag = True
        handle_keys(snake, apple_cart, fade_surface, game_over_handles)
        pg.display.update()
    is_game_over = False


def replace_apples(iter_num, occupied_cells, snake, apple_cart):
    """Периодическое изменение позиций яблок"""
    if iter_num < 200:
        return iter_num, occupied_cells
    rand_apples = choices(apple_cart.cart, k=3)
    for rand_apple in rand_apples:
        rand_apple.erase_one_cell(rand_apple.position)
        rand_apple.randomize_position(occupied_cells)
        occupied_cells = (set(apple_cart.get_cells())
                          | set(snake.positions))
    iter_num = randint(1, 100)
    return iter_num, occupied_cells


def main():
    """Основной игровой цикл"""
    pg.init()
    iter_num = randint(1, 100)
    snake = Snake()
    occupied_cells = set(snake.positions)
    apple = Apple(busy_cells=occupied_cells)
    occupied_cells |= {apple.position}
    apple_cart = AppleCart(apple)
    fade_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill(BORDER_COLOR)
    fade_surface.set_alpha(200)
    screen.blit(fade_surface, (0, 0))
    show_welcome(fade_surface, background, snake, apple_cart)
    while True:
        clock.tick(SPEED)
        handle_keys(snake, apple_cart, fade_surface)
        snake.move()
        if snake.get_head_position() in apple_cart.get_cells():
            occupied_cells = set(apple_cart.get_cells()) | set(snake.positions)
            eaten_apple = apple_cart.get_cells()[snake.get_head_position()]
            play_sound(['eat', 'cut'][eaten_apple.is_unripe])
            snake.add_sub_apple(eaten_apple.is_unripe)
            eaten_apple.randomize_position(occupied_cells)
        if snake.get_head_position() in snake.positions[4:]:
            play_sound('crash')
            snake.crash()
            show_game_over(fade_surface, background, snake, apple_cart)
        iter_num, occupied_cells = replace_apples(iter_num, occupied_cells,
                                                  snake, apple_cart)
        snake.draw()
        [apple.draw() for apple in apple_cart.cart]
        if iter_num % 2:
            play_sound(choice(['step1', 'step2']))
        iter_num += 1
        pg.display.update()


if __name__ == '__main__':
    main()
