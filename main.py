import pygame
import random

pygame.font.init()

# Константы
BLOCK_SIZE = 30
COLUMNS = 10
ROWS = 20
SIDEBAR_WIDTH = 250  
GAME_WIDTH = COLUMNS * BLOCK_SIZE
SCREEN_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = ROWS * BLOCK_SIZE

# Современная яркая палитра
COLORS = [
    (0, 230, 254),   # Голубой
    (255, 213, 0),   # Желтый
    (184, 56, 204),  # Фиолетовый
    (106, 219, 45),  # Зеленый
    (255, 60, 60),   # Красный
    (41, 121, 255),  # Синий
    (255, 140, 0)    # Оранжевый
]

BG_COLOR = (25, 25, 35)       
GRID_BG_COLOR = (15, 15, 20)  
GRID_LINE_COLOR = (40, 40, 50) 
TEXT_COLOR = (255, 255, 255)

SHAPES = [
    [[1, 5, 9, 13], [4, 5, 6, 7]], # I
    [[4, 5, 9, 10], [2, 6, 5, 9]], # Z
    [[6, 7, 9, 10], [1, 5, 6, 10]], # S
    [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 8, 9], [4, 5, 6, 10]], # J
    [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]], # L
    [[1, 4, 5, 6], [1, 5, 6, 9], [4, 5, 6, 9], [1, 4, 5, 9]], # T
    [[1, 2, 5, 6]], # O
]

class Piece:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shape = random.choice(SHAPES)
        self.color = random.choice(COLORS)
        self.rotation = 0

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

def draw_bubble_block(surface, x, y, color, is_ghost=False, is_flash=False):
    bx = x * BLOCK_SIZE
    by = y * BLOCK_SIZE
    rect = (bx, by, BLOCK_SIZE, BLOCK_SIZE)
    
    # Режим белой вспышки (для анимации)
    if is_flash:
        pygame.draw.rect(surface, (255, 255, 255), rect, border_radius=8)
        pygame.draw.rect(surface, (200, 255, 255), rect, 2, border_radius=8)
        return

    if is_ghost:
        ghost_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(ghost_surf, (*color, 80), (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2, border_radius=8)
        surface.blit(ghost_surf, (bx, by))
        return

    pygame.draw.rect(surface, color, rect, border_radius=8)
    
    shadow = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), (0, BLOCK_SIZE//2, BLOCK_SIZE, BLOCK_SIZE//2), border_radius=8)
    surface.blit(shadow, (bx, by))

    glare = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.ellipse(glare, (255, 255, 255, 180), (BLOCK_SIZE*0.15, BLOCK_SIZE*0.05, BLOCK_SIZE*0.7, BLOCK_SIZE*0.35))
    surface.blit(glare, (bx, by))
    
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=8)

def draw_ui(surface, score, level, next_piece):
    font_main = pygame.font.SysFont('arial', 30, bold=True)
    font_score = pygame.font.SysFont('arial', 40, bold=True)

    label_score_text = font_main.render('SCORE', 1, (150, 160, 180))
    label_score_val = font_score.render(str(score), 1, (0, 230, 254))
    surface.blit(label_score_text, (GAME_WIDTH + 30, 50))
    surface.blit(label_score_val, (GAME_WIDTH + 30, 90))

    label_lvl_text = font_main.render('LEVEL', 1, (150, 160, 180))
    label_lvl_val = font_score.render(str(level), 1, (106, 219, 45))
    surface.blit(label_lvl_text, (GAME_WIDTH + 30, 160))
    surface.blit(label_lvl_val, (GAME_WIDTH + 30, 200))

    label_next = font_main.render('NEXT', 1, (150, 160, 180))
    surface.blit(label_next, (GAME_WIDTH + 30, 300))
    
    shape_format = next_piece.image()
    sx = GAME_WIDTH + 30
    sy = 350
    for i in range(4):
        for j in range(4):
            if (i * 4 + j) in shape_format:
                draw_bubble_block(surface, (sx // BLOCK_SIZE) + j, (sy // BLOCK_SIZE) + i, next_piece.color)

def draw_window(surface, grid, score, level, next_piece):
    surface.fill(BG_COLOR)
    pygame.draw.rect(surface, GRID_BG_COLOR, (0, 0, GAME_WIDTH, SCREEN_HEIGHT))
    
    for i in range(ROWS):
        pygame.draw.line(surface, GRID_LINE_COLOR, (0, i * BLOCK_SIZE), (GAME_WIDTH, i * BLOCK_SIZE))
    for j in range(COLUMNS):
        pygame.draw.line(surface, GRID_LINE_COLOR, (j * BLOCK_SIZE, 0), (j * BLOCK_SIZE, SCREEN_HEIGHT))

    for y in range(ROWS):
        for x in range(COLUMNS):
            if grid[y][x] != (0,0,0):
                draw_bubble_block(surface, x, y, grid[y][x])
    
    pygame.draw.rect(surface, (100, 110, 130), (0, 0, GAME_WIDTH, SCREEN_HEIGHT), 2)
    draw_ui(surface, score, level, next_piece)

def main():
    locked_vertices = {}
    grid = create_grid(locked_vertices)
    change_piece = False
    run = True
    
    current_piece = Piece(3, 0)
    next_piece = Piece(3, 0)
    
    clock = pygame.time.Clock()
    fall_time = 0
    score = 0
    level = 1
    fall_speed = 0.35

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
                    if not valid_space(current_piece, grid): current_piece.rotation -= 1
                if event.key == pygame.K_SPACE:
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    change_piece = True

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
            
            # === АНИМАЦИЯ УДАЛЕНИЯ ЛИНИИ ===
            # 1. Сначала находим линии, которые полностью заполнены
            full_rows = []
            for i in range(ROWS):
                if (0, 0, 0) not in grid[i]:
                    full_rows.append(i)

            # 2. Если есть заполненные линии, рисуем анимацию вспышки
            if full_rows:
                draw_window(screen, grid, score, level, next_piece) # Отрисовываем актуальное поле
                
                # Рисуем белые блоки поверх полных линий
                for row in full_rows:
                    for col in range(COLUMNS):
                        draw_bubble_block(screen, col, row, (255,255,255), is_flash=True)
                
                pygame.display.update() # Обновляем экран со вспышкой
                pygame.time.delay(120)  # Замираем на 120 миллисекунд (эффект удара/вспышки)
            # ===============================

            lines_cleared = clear_rows(grid, locked_vertices)
            
            if lines_cleared > 0:
                scores_by_lines = {1: 100, 2: 300, 3: 500, 4: 800}
                score += scores_by_lines.get(lines_cleared, 0)
                level = (score // 1000) + 1
                fall_speed = max(0.05, 0.35 - (level - 1) * 0.025)
                grid = create_grid(locked_vertices)
                
            current_piece = next_piece
            next_piece = Piece(3, 0)
            change_piece = False

        draw_window(screen, grid, score, level, next_piece)

        ghost_format = ghost_piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in ghost_format and ghost_piece.y + i > -1:
                    draw_bubble_block(screen, ghost_piece.x + j, ghost_piece.y + i, ghost_piece.color, is_ghost=True)

        shape_format = current_piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in shape_format and current_piece.y + i > -1:
                    draw_bubble_block(screen, current_piece.x + j, current_piece.y + i, current_piece.color)

        pygame.display.update()

        if any(y < 1 for (x, y) in locked_vertices):
            dark_surface = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_surface.fill((0, 0, 0, 180))
            screen.blit(dark_surface, (0, 0))

            font_go = pygame.font.SysFont('arial', 50, bold=True)
            label_go = font_go.render("GAME OVER", 1, (255, 60, 60))
            screen.blit(label_go, (GAME_WIDTH/2 - label_go.get_width()/2, SCREEN_HEIGHT/2 - 50))
            
            font_restart = pygame.font.SysFont('arial', 24, bold=True)
            label_restart = font_restart.render("Press SPACE to Restart", 1, (255, 255, 255))
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
                            current_piece = Piece(3, 0)
                            next_piece = Piece(3, 0)
                            fall_time = 0
                            waiting = False 

    pygame.quit()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bubble Tetris")
main()