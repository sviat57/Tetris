import pygame
import random
import os

pygame.font.init()

# Константы
BLOCK_SIZE = 30
COLUMNS = 10
ROWS = 20
SIDEBAR_WIDTH = 250  
GAME_WIDTH = COLUMNS * BLOCK_SIZE
SCREEN_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = ROWS * BLOCK_SIZE

# Нежная, пастельная палитра
COLORS = [
    (142, 220, 229),  # Мягкий голубой (I)
    (247, 230, 151),  # Кремово-желтый (O)
    (200, 168, 226),  # Нежный лавандовый (T)
    (165, 223, 178),  # Мятный зеленый (S)
    (243, 163, 163),  # Пастельный красный (Z)
    (155, 184, 237),  # Приглушенный синий (J)
    (248, 194, 145)   # Персиковый (L)
]

BG_COLOR = (248, 249, 250)         
GRID_BG_COLOR = (238, 240, 243)    
GRID_LINE_COLOR = (225, 228, 233)  
PANEL_BG = (255, 255, 255)         
TEXT_TITLE = (150, 155, 165)       
TEXT_VAL = (80, 85, 95)            

SHAPES = [
    [[1, 5, 9, 13], [4, 5, 6, 7]], # I
    [[4, 5, 9, 10], [2, 6, 5, 9]], # Z
    [[6, 7, 9, 10], [1, 5, 6, 10]], # S
    [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 8, 9], [4, 5, 6, 10]], # J
    [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]], # L
    [[1, 4, 5, 6], [1, 5, 6, 9], [4, 5, 6, 9], [1, 4, 5, 9]], # T
    [[1, 2, 5, 6]], # O
]

# --- Функции Рекордов ---
def get_max_score():
    if not os.path.exists('highscore.txt'):
        with open('highscore.txt', 'w') as f:
            f.write('0')
    with open('highscore.txt', 'r') as f:
        try: return int(f.read())
        except: return 0

def update_max_score(score):
    high = get_max_score()
    if score > high:
        with open('highscore.txt', 'w') as f:
            f.write(str(score))
# -------------------------

class Piece:
    def __init__(self, x, y, exclude_color=None):
        self.x = x
        self.y = y
        self.shape = random.choice(SHAPES)
        self.rotation = 0
        if exclude_color:
            available_colors = [c for c in COLORS if c != exclude_color]
            self.color = random.choice(available_colors)
        else:
            self.color = random.choice(COLORS)

    def image(self):
        return self.shape[self.rotation % len(self.shape)]

def create_grid(locked_pos={}):
    grid = [[(0,0,0) for _ in range(COLUMNS)] for _ in range(ROWS)]
    for y in range(ROWS):
        for x in range(COLUMNS):
            if (x, y) in locked_pos:
                grid[y][x] = locked_pos[(x, y)]
    return grid

def valid_space(piece, grid):
    accepted_pos = [[(j, i) for j in range(COLUMNS) if grid[i][j] == (0,0,0)] for i in range(ROWS)]
    accepted_pos = [item for sublist in accepted_pos for item in sublist]
    formatted = []
    shape_format = piece.image()
    for i in range(4):
        for j in range(4):
            if (i * 4 + j) in shape_format:
                formatted.append((piece.x + j, piece.y + i))
    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True

def clear_rows(grid, locked):
    inc = 0
    for i in range(len(grid)-1, -1, -1):
        row = grid[i]
        if (0, 0, 0) not in row:
            inc += 1
            for j in range(len(row)):
                try: del locked[(j, i)]
                except: continue
        elif inc > 0:
            for j in range(len(row)):
                if (j, i) in locked:
                    color = locked.pop((j, i))
                    locked[(j, i + inc)] = color
    return inc

def draw_square_block(surface, bx, by, color, is_ghost=False, is_flash=False, is_locked=False):
    rect = (bx, by, BLOCK_SIZE, BLOCK_SIZE)
    rad = 6 
    
    if is_flash:
        pygame.draw.rect(surface, (255, 255, 255), rect, border_radius=rad)
        return
    if is_ghost:
        pygame.draw.rect(surface, color, rect, 2, border_radius=rad)
        return

    shadow_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 25), (0, 0, BLOCK_SIZE, BLOCK_SIZE), border_radius=rad)
    surface.blit(shadow_surf, (bx + 3, by + 4))

    pygame.draw.rect(surface, color, rect, border_radius=rad)
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=rad)

    if is_locked:
        pygame.draw.rect(surface, (255, 255, 255), rect, 3, border_radius=rad)

def draw_ui_panel(surface, x, y, width, height, title, value):
    pygame.draw.rect(surface, PANEL_BG, (x, y, width, height), border_radius=12)
    shadow = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 10), (0, 0, width, height), border_radius=12)
    surface.blit(shadow, (x + 2, y + 4))
    pygame.draw.rect(surface, (235, 238, 245), (x, y, width, height), 1, border_radius=12)
    
    font_main = pygame.font.SysFont('arial', 14, bold=True)
    font_val = pygame.font.SysFont('arial', 28, bold=True)
    
    lbl_title = font_main.render(title, 1, TEXT_TITLE)
    lbl_val = font_val.render(str(value), 1, TEXT_VAL)
    
    surface.blit(lbl_title, (x + (width - lbl_title.get_width()) // 2, y + 10))
    surface.blit(lbl_val, (x + (width - lbl_val.get_width()) // 2, y + 35))

def draw_ui(surface, score, level, next_piece, high_score):
    ui_x = GAME_WIDTH + 25
    ui_w = SIDEBAR_WIDTH - 50
    
    draw_ui_panel(surface, ui_x, 30, ui_w, 75, 'BEST SCORE', high_score)
    draw_ui_panel(surface, ui_x, 120, ui_w, 75, 'SCORE', score)
    draw_ui_panel(surface, ui_x, 210, ui_w, 75, 'LEVEL', level)

    font_main = pygame.font.SysFont('arial', 16, bold=True)
    label_next = font_main.render('NEXT PIECE', 1, TEXT_TITLE)
    surface.blit(label_next, (ui_x + (ui_w - label_next.get_width()) // 2, 315))

    box_w = 4 * BLOCK_SIZE + 20
    box_h = 4 * BLOCK_SIZE + 20
    box_x = GAME_WIDTH + (SIDEBAR_WIDTH - box_w) // 2
    box_y = 345

    shadow = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 10), (0, 0, box_w, box_h), border_radius=12)
    surface.blit(shadow, (box_x + 2, box_y + 4))

    pygame.draw.rect(surface, PANEL_BG, (box_x, box_y, box_w, box_h), border_radius=12)
    pygame.draw.rect(surface, (235, 238, 245), (box_x, box_y, box_w, box_h), 1, border_radius=12)

    grid_start_x = box_x + 10
    grid_start_y = box_y + 10
    for i in range(4):
        for j in range(4):
            rect = (grid_start_x + j * BLOCK_SIZE, grid_start_y + i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, (245, 246, 248), rect, 1)

    shape_format = next_piece.image()
    blocks = [(j, i) for i in range(4) for j in range(4) if (i * 4 + j) in shape_format]

    if blocks:
        min_x = min(b[0] for b in blocks)
        max_x = max(b[0] for b in blocks)
        min_y = min(b[1] for b in blocks)
        max_y = max(b[1] for b in blocks)

        piece_pixel_w = (max_x - min_x + 1) * BLOCK_SIZE
        piece_pixel_h = (max_y - min_y + 1) * BLOCK_SIZE

        offset_x = box_x + (box_w - piece_pixel_w) // 2 - min_x * BLOCK_SIZE
        offset_y = box_y + (box_h - piece_pixel_h) // 2 - min_y * BLOCK_SIZE

        for j, i in blocks:
            draw_square_block(surface, offset_x + j * BLOCK_SIZE, offset_y + i * BLOCK_SIZE, next_piece.color)

def draw_window(surface, grid, score, level, next_piece, high_score):
    surface.fill(BG_COLOR)
    pygame.draw.rect(surface, GRID_BG_COLOR, (0, 0, GAME_WIDTH, SCREEN_HEIGHT))
    
    for i in range(ROWS):
        pygame.draw.line(surface, GRID_LINE_COLOR, (0, i * BLOCK_SIZE), (GAME_WIDTH, i * BLOCK_SIZE))
    for j in range(COLUMNS):
        pygame.draw.line(surface, GRID_LINE_COLOR, (j * BLOCK_SIZE, 0), (j * BLOCK_SIZE, SCREEN_HEIGHT))

    for y in range(ROWS):
        for x in range(COLUMNS):
            if grid[y][x] != (0,0,0):
                draw_square_block(surface, x * BLOCK_SIZE, y * BLOCK_SIZE, grid[y][x])
    
    pygame.draw.rect(surface, (210, 215, 225), (0, 0, GAME_WIDTH, SCREEN_HEIGHT), 2)
    draw_ui(surface, score, level, next_piece, high_score)

def main():
    locked_vertices = {}
    grid = create_grid(locked_vertices)
    change_piece = False
    run = True
    
    current_piece = Piece(3, 0)
    next_piece = Piece(3, 0, exclude_color=current_piece.color)
    
    clock = pygame.time.Clock()
    fall_time = 0
    score = 0
    high_score = get_max_score()
    level = 1
    fall_speed = 0.35

    shake_timer = 0
    floating_texts = [] 
    
    # Флаг для отслеживания, была ли фигура брошена Пробелом
    hard_dropped = False

    display_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    while run:
        grid = create_grid(locked_vertices)
        fall_time += clock.get_rawtime()
        clock.tick(60)

        if fall_time / 1000 >= fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid): current_piece.x += 1
                if event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid): current_piece.x -= 1
                if event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not valid_space(current_piece, grid): current_piece.y -= 1
                
                if event.key == pygame.K_UP:
                    current_piece.rotation += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1 
                        if not valid_space(current_piece, grid):
                            current_piece.x += 2 
                            if not valid_space(current_piece, grid):
                                current_piece.x -= 1 
                                current_piece.y -= 1 
                                if not valid_space(current_piece, grid):
                                    current_piece.y += 1 
                                    current_piece.rotation -= 1 

                if event.key == pygame.K_SPACE:
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    change_piece = True
                    # Запоминаем, что игрок использовал жесткий сброс
                    hard_dropped = True

        ghost_piece = Piece(current_piece.x, current_piece.y)
        ghost_piece.shape = current_piece.shape
        ghost_piece.rotation = current_piece.rotation
        ghost_piece.color = current_piece.color
        
        while valid_space(ghost_piece, grid):
            ghost_piece.y += 1
        ghost_piece.y -= 1 

        if change_piece:
            shape_format = current_piece.image()
            
            for i in range(4):
                for j in range(4):
                    if (i * 4 + j) in shape_format:
                        locked_vertices[(current_piece.x + j, current_piece.y + i)] = current_piece.color
            
            grid = create_grid(locked_vertices)
            
            full_rows = []
            for i in range(ROWS):
                if (0, 0, 0) not in grid[i]:
                    full_rows.append(i)

            if full_rows:
                draw_window(display_surf, grid, score, level, next_piece, high_score)
                for row in full_rows:
                    for col in range(COLUMNS):
                        draw_square_block(display_surf, col * BLOCK_SIZE, row * BLOCK_SIZE, (255,255,255), is_flash=True)
                screen.blit(display_surf, (0, 0))
                pygame.display.update()
                pygame.time.delay(120)

            lines_cleared = clear_rows(grid, locked_vertices)
            
            if lines_cleared > 0:
                scores_by_lines = {1: 100, 2: 300, 3: 500, 4: 800}
                points_gained = scores_by_lines.get(lines_cleared, 0)
                score += points_gained
                
                text_str = f"+{points_gained}"
                if lines_cleared == 4:
                    text_str = "TETRIS! " + text_str
                
                text_y = full_rows[len(full_rows)//2] * BLOCK_SIZE
                floating_texts.append({
                    'x': GAME_WIDTH // 2, 
                    'y': text_y, 
                    'text': text_str, 
                    'alpha': 255
                })

                if score > high_score:
                    high_score = score
                
                level = (score // 1000) + 1
                fall_speed = max(0.05, 0.35 - (level - 1) * 0.025)
                grid = create_grid(locked_vertices)
                
                # Трясем экран ТОЛЬКО если был Пробел + собрана линия
                if hard_dropped:
                    shake_timer = 10
                
            current_piece = next_piece
            next_piece = Piece(3, 0, exclude_color=current_piece.color)
            change_piece = False
            # Сбрасываем флажок для следующей фигуры
            hard_dropped = False

        draw_window(display_surf, grid, score, level, next_piece, high_score)

        ghost_format = ghost_piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in ghost_format and ghost_piece.y + i > -1:
                    draw_square_block(display_surf, (ghost_piece.x + j) * BLOCK_SIZE, (ghost_piece.y + i) * BLOCK_SIZE, ghost_piece.color, is_ghost=True)

        shape_format = current_piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in shape_format and current_piece.y + i > -1:
                    draw_square_block(display_surf, (current_piece.x + j) * BLOCK_SIZE, (current_piece.y + i) * BLOCK_SIZE, current_piece.color)

        font_float = pygame.font.SysFont('arial', 28, bold=True)
        for ft in floating_texts[:]:
            ft['y'] -= 1.5      
            ft['alpha'] -= 4    
            
            if ft['alpha'] <= 0:
                floating_texts.remove(ft)
            else:
                text_surface = font_float.render(ft['text'], True, (130, 195, 150))
                text_surface.set_alpha(ft['alpha'])
                display_surf.blit(text_surface, (ft['x'] - text_surface.get_width()//2, ft['y']))

        # Уменьшенная амплитуда тряски (от -2 до 2 пикселей)
        dx, dy = 0, 0
        if shake_timer > 0:
            dx = random.randint(-2, 2)
            dy = random.randint(-2, 2)
            shake_timer -= 1

        screen.fill(BG_COLOR)
        screen.blit(display_surf, (dx, dy))

        pygame.display.update()

        if any(y < 1 for (x, y) in locked_vertices):
            update_max_score(score) 
            
            light_surface = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            light_surface.fill((255, 255, 255, 210)) 
            screen.blit(light_surface, (0, 0))

            font_go = pygame.font.SysFont('arial', 50, bold=True)
            label_go = font_go.render("GAME OVER", 1, (243, 100, 100))
            screen.blit(label_go, (GAME_WIDTH/2 - label_go.get_width()/2, SCREEN_HEIGHT/2 - 50))
            
            font_restart = pygame.font.SysFont('arial', 24, bold=True)
            label_restart = font_restart.render("Press SPACE to Restart", 1, TEXT_VAL)
            screen.blit(label_restart, (GAME_WIDTH/2 - label_restart.get_width()/2, SCREEN_HEIGHT/2 + 20))
            
            pygame.display.update()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        waiting = False
                        run = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            locked_vertices.clear()
                            grid = create_grid(locked_vertices)
                            score = 0
                            level = 1
                            fall_speed = 0.35
                            floating_texts.clear()
                            current_piece = Piece(3, 0)
                            next_piece = Piece(3, 0, exclude_color=current_piece.color)
                            fall_time = 0
                            hard_dropped = False
                            waiting = False 

    pygame.quit()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Minimalist Pastel Tetris")
main()