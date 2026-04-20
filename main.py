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
    (142, 220, 229), (247, 230, 151), (200, 168, 226),
    (165, 223, 178), (243, 163, 163), (155, 184, 237), (248, 194, 145)
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

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-7, -2)
        self.color = color
        self.life = 255
        self.size = random.randint(4, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.35  # Гравитация частицы
        self.life -= 8   # Скорость исчезновения

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

class TetrisGame:
    def __init__(self):
        self.locked_vertices = {}
        self.grid = self.create_grid()
        self.current_piece = Piece(3, 0)
        self.next_piece = Piece(3, 0, exclude_color=self.current_piece.color)
        self.score = 0
        self.high_score = self.get_max_score()
        self.level = 1
        self.fall_speed = 0.35
        self.lines_cleared_total = 0
        self.game_over = False
        self.floating_texts = []
        self.particles = []
        self.shake_timer = 0
        self.hard_dropped = False

    def create_grid(self):
        grid = [[(0,0,0) for _ in range(COLUMNS)] for _ in range(ROWS)]
        for y in range(ROWS):
            for x in range(COLUMNS):
                if (x, y) in self.locked_vertices:
                    grid[y][x] = self.locked_vertices[(x, y)]
        return grid

    def get_max_score(self):
        if not os.path.exists('highscore.txt'):
            with open('highscore.txt', 'w') as f:
                f.write('0')
        with open('highscore.txt', 'r') as f:
            try:
                content = f.read().strip()
                if ']' in content:
                    return int(content.split(']')[-1].strip())
                return int(content)
            except: return 0

    def update_max_score(self):
        if self.score > self.high_score:
            with open('highscore.txt', 'w') as f:
                f.write(str(self.score))

    def valid_space(self, piece):
        shape_format = piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in shape_format:
                    x = piece.x + j
                    y = piece.y + i
                    if x < 0 or x >= COLUMNS or y >= ROWS:
                        return False
                    if (x, y) in self.locked_vertices and y > -1:
                        return False
        return True

    def clear_rows(self):
        inc = 0
        full_rows = []
        
        # Находим полные ряды и генерируем частицы
        for i in range(ROWS - 1, -1, -1):
            row = self.grid[i]
            if (0, 0, 0) not in row:
                inc += 1
                full_rows.append(i)
                for j in range(COLUMNS):
                    try: 
                        color = self.locked_vertices[(j, i)]
                        # Создаем 4 частицы для каждого удаляемого блока
                        for _ in range(4):
                            px = j * BLOCK_SIZE + random.randint(5, BLOCK_SIZE - 5)
                            py = i * BLOCK_SIZE + random.randint(5, BLOCK_SIZE - 5)
                            self.particles.append(Particle(px, py, color))
                        
                        del self.locked_vertices[(j, i)]
                    except: continue
            elif inc > 0:
                for j in range(COLUMNS):
                    if (j, i) in self.locked_vertices:
                        color = self.locked_vertices.pop((j, i))
                        self.locked_vertices[(j, i + inc)] = color

        if inc > 0:
            self.lines_cleared_total += inc
            scores_by_lines = {1: 100, 2: 300, 3: 500, 4: 800}
            points_gained = scores_by_lines.get(inc, 0)
            self.score += points_gained

            text_str = f"+{points_gained}"
            if inc == 4:
                text_str = "TETRIS! " + text_str

            text_y = full_rows[len(full_rows)//2] * BLOCK_SIZE
            self.floating_texts.append({
                'x': GAME_WIDTH // 2,
                'y': text_y,
                'text': text_str,
                'alpha': 255
            })

            if self.score > self.high_score:
                self.high_score = self.score

            self.level = (self.lines_cleared_total // 10) + 1
            self.fall_speed = max(0.05, 0.35 - (self.level - 1) * 0.025)

            if self.hard_dropped:
                self.shake_timer = 10

        return inc, full_rows

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
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Minimalist Pastel Tetris")
    
    display_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    game = TetrisGame()
    fall_time = 0
    run = True
    change_piece = False

    while run:
        game.grid = game.create_grid()
        fall_time += clock.get_rawtime()
        clock.tick(60)

        if fall_time / 1000 >= game.fall_speed:
            fall_time = 0
            game.current_piece.y += 1
            if not game.valid_space(game.current_piece) and game.current_piece.y > 0:
                game.current_piece.y -= 1
                change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN and not game.game_over:
                if event.key == pygame.K_LEFT:
                    game.current_piece.x -= 1
                    if not game.valid_space(game.current_piece): game.current_piece.x += 1
                if event.key == pygame.K_RIGHT:
                    game.current_piece.x += 1
                    if not game.valid_space(game.current_piece): game.current_piece.x -= 1
                if event.key == pygame.K_DOWN:
                    game.current_piece.y += 1
                    if not game.valid_space(game.current_piece): game.current_piece.y -= 1
                
                if event.key == pygame.K_UP:
                    game.current_piece.rotation += 1
                    if not game.valid_space(game.current_piece):
                        game.current_piece.x -= 1 
                        if not game.valid_space(game.current_piece):
                            game.current_piece.x += 2 
                            if not game.valid_space(game.current_piece):
                                game.current_piece.x -= 1 
                                game.current_piece.y -= 1 
                                if not game.valid_space(game.current_piece):
                                    game.current_piece.y += 1 
                                    game.current_piece.rotation -= 1 

                if event.key == pygame.K_SPACE:
                    while game.valid_space(game.current_piece):
                        game.current_piece.y += 1
                    game.current_piece.y -= 1
                    change_piece = True
                    game.hard_dropped = True

        ghost_piece = Piece(game.current_piece.x, game.current_piece.y)
        ghost_piece.shape = game.current_piece.shape
        ghost_piece.rotation = game.current_piece.rotation
        ghost_piece.color = game.current_piece.color
        
        while game.valid_space(ghost_piece):
            ghost_piece.y += 1
        ghost_piece.y -= 1 

        if change_piece:
            shape_format = game.current_piece.image()
            for i in range(4):
                for j in range(4):
                    if (i * 4 + j) in shape_format:
                        game.locked_vertices[(game.current_piece.x + j, game.current_piece.y + i)] = game.current_piece.color
            
            game.grid = game.create_grid()
            lines_cleared, full_rows = game.clear_rows()
            
            if full_rows:
                draw_window(display_surf, game.grid, game.score, game.level, game.next_piece, game.high_score)
                for row in full_rows:
                    for col in range(COLUMNS):
                        draw_square_block(display_surf, col * BLOCK_SIZE, row * BLOCK_SIZE, (255,255,255), is_flash=True)
                screen.blit(display_surf, (0, 0))
                pygame.display.update()
                pygame.time.delay(120)
                
            game.current_piece = game.next_piece
            game.next_piece = Piece(3, 0, exclude_color=game.current_piece.color)
            change_piece = False
            game.hard_dropped = False

            if any(y < 1 for (x, y) in game.locked_vertices):
                game.game_over = True

        draw_window(display_surf, game.grid, game.score, game.level, game.next_piece, game.high_score)

        ghost_format = ghost_piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in ghost_format and ghost_piece.y + i > -1:
                    draw_square_block(display_surf, (ghost_piece.x + j) * BLOCK_SIZE, (ghost_piece.y + i) * BLOCK_SIZE, ghost_piece.color, is_ghost=True)

        # Вычисляем плавное падение для текущей фигуры
        smooth_y_offset = 0
        test_piece = Piece(game.current_piece.x, game.current_piece.y)
        test_piece.shape = game.current_piece.shape
        test_piece.rotation = game.current_piece.rotation
        test_piece.y += 1
        # Если блок внизу пустой — делаем смещение
        if game.valid_space(test_piece) and not game.game_over:
            smooth_y_offset = (fall_time / (game.fall_speed * 1000)) * BLOCK_SIZE

        shape_format = game.current_piece.image()
        for i in range(4):
            for j in range(4):
                if (i * 4 + j) in shape_format and game.current_piece.y + i > -1:
                    draw_square_block(display_surf, 
                                      (game.current_piece.x + j) * BLOCK_SIZE, 
                                      (game.current_piece.y + i) * BLOCK_SIZE + smooth_y_offset, 
                                      game.current_piece.color)

        # Отрисовка частиц
        for p in game.particles[:]:
            p.update()
            if p.life <= 0:
                game.particles.remove(p)
            else:
                p_surf = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                p_surf.fill((*p.color, max(0, int(p.life))))
                display_surf.blit(p_surf, (p.x, p.y))

        # Отрисовка текста очков
        font_float = pygame.font.SysFont('arial', 28, bold=True)
        for ft in game.floating_texts[:]:
            ft['y'] -= 1.5      
            ft['alpha'] -= 4    
            
            if ft['alpha'] <= 0:
                game.floating_texts.remove(ft)
            else:
                text_surface = font_float.render(ft['text'], True, (130, 195, 150))
                text_surface.set_alpha(ft['alpha'])
                display_surf.blit(text_surface, (ft['x'] - text_surface.get_width()//2, ft['y']))

        dx, dy = 0, 0
        if game.shake_timer > 0:
            dx = random.randint(-2, 2)
            dy = random.randint(-2, 2)
            game.shake_timer -= 1

        screen.fill(BG_COLOR)
        screen.blit(display_surf, (dx, dy))

        if game.game_over:
            game.update_max_score()
            
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
                            game = TetrisGame()
                            fall_time = 0
                            change_piece = False
                            waiting = False 

        if not game.game_over:
            pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()