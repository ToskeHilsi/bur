import pygame
import random
import math
import json
import os

pygame.init()
pygame.mixer.init()  # Initialize music system

WIDTH, HEIGHT = 1920, 1080 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("bur")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (100, 100, 255)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)

player_pos = [WIDTH // 2, HEIGHT - 50]
base_player_speed = 3.75  # Scaled by 0.75 from 5 to match size scaling
player_speed = base_player_speed
player_radius = 15  # Multiplied by 1.5 from 10

# Play area box
box_size = 450  # Multiplied by 1.5 from 300
box_x = WIDTH // 2 - box_size // 2
box_y = HEIGHT // 2 - box_size // 2

# Enemy definitions
ENEMIES = {
    1: {
        "name": "Comedy and Tragedy",
        "background": "stage",
        "music": "tv_world",  # Extension will be auto-detected
        "difficulty": 0.4,  # Easier than current
        "max_health": 80,
        "attacks": [0, 2, 4, 8, 12]  # Spiral, Targeted, Expanding Spiral, Lasers, Slashes
    },
    2: {
        "name": "Diego",
        "background": "desert",
        "music": "friend_inside_me",
        "difficulty": 0.6,
        "max_health": 85,
        "attacks": [2, 6, 9, 10, 12]  # Targeted, Random Rain, Cross, Zigzag, Slashes
    },
    3: {
        "name": "Cap'n Cakes",
        "background": "cyber_city",
        "music": "fandago",
        "difficulty": 0.8,
        "max_health": 90,
        "attacks": [1, 3, 5, 7, 11]  # Bouncing, Radial Burst, Double Spiral, Giant Explosive, Grid Rain
    },
    4: {
        "name": "Spamton NEO",
        "background": "queens_basement",
        "music": "big_shot",
        "difficulty": 1.0,  # Current difficulty
        "max_health": 100,
        "attacks": [0, 3, 4, 5, 7, 9]  # Spiral, Radial Burst, Expanding Spiral, Double Spiral, Giant Explosive, Cross
    },
    5: {
        "name": "The Roaring Knight",
        "background": "fountain",
        "music": "the_roaring_knight",
        "difficulty": 1.3,
        "max_health": 120,
        "attacks": [3, 7, 8, 12, 13]  # Radial Burst, Giant Explosive, Lasers, Slashes, Grid Slashes
    },
    6: {
        "name": "Sans",
        "background": "hall_of_judgment",
        "music": "musclememory",
        "difficulty": 1.6,
        "max_health": 1,  # Sans gimmick - 1 HP but very hard
        "attacks": [0, 4, 6, 10, 12]  # Spiral, Expanding Spiral, Random Rain, Zigzag, Slashes
    },
    7: {
        "name": "Susie",
        "background": "forest_light",
        "music": "megalovania_susie",
        "difficulty": 2.0,
        "max_health": 150,
        "attacks": [1, 5, 7, 9, 11, 12]  # Bouncing, Double Spiral, Giant Explosive, Cross, Grid Rain, Slashes
    },
    8: {
        "name": "???",
        "background": "forest_dark",
        "music": "fun_value",
        "difficulty": 2.5,
        "max_health": 200,
        "attacks": [0, 1, 3, 4, 5, 6, 7, 10, 11, 12, 13]  # Almost all attacks including Grid Slashes
    }
}

# Game state
current_enemy_id = 4  # Start with Spamton NEO
defeated_enemies = set()  # Track which enemies have been beaten
save_file = "bur_save.json"
hard_mode_active = False  # Track if we're in hard mode

# Character selection and stats - SIMPLIFIED TO ONE CHARACTER
selected_character = 0
character_stats = {
    0: {"name": "bur", "max_health": 8, "damage_multiplier": 1.0}
}

clock = pygame.time.Clock()
FPS = 60

bullets = []
particles = []
MAX_PARTICLES = 50  # Limit total particles to prevent crashes

player_health = 8
max_health = 8
invincible_timer = 0
INVINCIBLE_DURATION = FPS * 1.5
attack_active = False
max_health_upgrades = 0  # Track number of max health upgrades purchased

# Attack system variables
enemy_health = 100
max_enemy_health = 100
attack_flavor_texts = []  # Will be populated with loaded sprites

# Load attack flavor text sprites
flavor_text_num = 0
while True:
    try:
        flavor_sprite = pygame.image.load(f"attack_text_{flavor_text_num}.png").convert_alpha()
        # Scale to much bigger size - take up most of the screen
        original_width, original_height = flavor_sprite.get_size()
        # Scale to fit within 1400x800 (keeping aspect ratio)
        scale_factor = min(1400 / original_width, 800 / original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        flavor_sprite = pygame.transform.scale(flavor_sprite, (new_width, new_height))
        attack_flavor_texts.append(flavor_sprite)
        flavor_text_num += 1
    except:
        break

# Fallback if no custom sprites
if not attack_flavor_texts:
    fallback_texts = [
        "You focus your energy...",
        "A surge of power flows through you!",
        "Time to strike back!",
        "You prepare your counterattack!",
        "Your determination burns bright!",
        "You channel your strength!",
        "Ready to unleash fury!",
        "A moment of opportunity appears!"
    ]
    # Create simple text sprites as fallback
    for text in fallback_texts:
        text_sprite = pygame.Surface((1200, 400), pygame.SRCALPHA)
        pygame.draw.rect(text_sprite, (50, 50, 50), (0, 0, 1200, 400))
        pygame.draw.rect(text_sprite, WHITE, (0, 0, 1200, 400), 3)
        text_surface = shop_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(600, 200))
        text_sprite.blit(text_surface, text_rect)
        attack_flavor_texts.append(text_sprite)

# QTE (Quick Time Event) variables
qte_active = False
qte_position = 0  # 0-100, position along the rectangle
qte_speed = 2  # Pixels per frame
qte_direction = 1  # 1 or -1
qte_bar_length = 400
qte_target_position = 50  # Middle of the bar
qte_perfect_range = 5  # +/- range for perfect hit
qte_good_range = 15  # +/- range for good hit

font = pygame.font.SysFont(None, 36)
shop_font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 24)

# Custom text rendering with letter sprites
letter_sprites = {}
letter_width = 16  # Default width for each letter
letter_height = 24  # Default height for each letter
letter_spacing = 2  # Spacing between letters

def load_letter_sprites():
    """Load all letter sprites A-Z, 0-9, and special characters"""
    global letter_sprites, letter_width, letter_height
    
    import os
    
    # Check if letters folder exists
    if not os.path.exists('letters'):
        print("WARNING: 'letters' folder not found!")
        print(f"Current directory: {os.getcwd()}")
        print("Please create a 'letters' folder with letter sprite images.")
    else:
        print(f"Letters folder found at: {os.path.abspath('letters')}")
        files = os.listdir('letters')
        print(f"Files in letters folder: {len(files)} files")
        if len(files) > 0:
            print(f"Sample files: {files[:5]}")
    
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?.-:,'/() "
    
    # First try to load at least one letter to get dimensions
    first_loaded = False
    loaded_sprites = 0
    
    for char in characters:
        try:
            # Try loading individual letter files
            if char == ' ':
                filename = 'letters/space.png'
            elif char == '!':
                filename = 'letters/exclamation.png'
            elif char == '?':
                filename = 'letters/question.png'
            elif char == '.':
                filename = 'letters/period.png'
            elif char == '-':
                filename = 'letters/dash.png'
            elif char == ':':
                filename = 'letters/colon.png'
            elif char == ',':
                filename = 'letters/comma.png'
            elif char == "'":
                filename = 'letters/apostrophe.png'
            elif char == '/':
                filename = 'letters/slash.png'
            elif char == '(':
                filename = 'letters/lparen.png'
            elif char == ')':
                filename = 'letters/rparen.png'
            else:
                filename = f'letters/{char}.png'
            
            sprite = pygame.image.load(filename).convert_alpha()
            letter_sprites[char] = sprite
            loaded_sprites += 1
            
            # Update default dimensions based on first loaded sprite
            if not first_loaded:
                letter_width = sprite.get_width()
                letter_height = sprite.get_height()
                first_loaded = True
                print(f"✓ Letter sprites loaded! Size: {letter_width}x{letter_height}")
        except Exception as e:
            # Create fallback sprite with pygame font
            if not first_loaded:
                # Set default dimensions if nothing loaded yet
                letter_width = 16
                letter_height = 24
            
            fallback_surface = pygame.Surface((letter_width, letter_height), pygame.SRCALPHA)
            if char == ' ':
                # Space is just transparent
                pass
            else:
                # Render with pygame font as fallback
                fallback_text = font.render(char, True, WHITE)
                # Center it in the surface
                text_rect = fallback_text.get_rect(center=(letter_width // 2, letter_height // 2))
                fallback_surface.blit(fallback_text, text_rect)
            letter_sprites[char] = fallback_surface
    
    if not first_loaded:
        print("⚠ WARNING: No letter sprites found in letters/ folder!")
        print("   Using fallback pygame font rendering instead.")
        print("   Place letter sprite PNGs in a 'letters' folder to use custom fonts.")
    else:
        print(f"✓ Loaded {loaded_sprites} custom letter sprites")
    
    return loaded_sprites

def render_text(text, color=WHITE, scale=1.0):
    """Render text using letter sprites
    Returns a surface with the rendered text"""
    
    text = text.upper()  # Convert to uppercase
    
    # Calculate total width
    total_width = 0
    for char in text:
        if char in letter_sprites:
            total_width += int((letter_sprites[char].get_width() + letter_spacing) * scale)
        elif char == ' ':
            total_width += int((letter_width // 2 + letter_spacing) * scale)
    
    # Create surface
    height = int(letter_height * scale)
    surface = pygame.Surface((max(total_width, 1), height), pygame.SRCALPHA)
    
    # Draw each letter
    x_pos = 0
    for char in text:
        if char in letter_sprites:
            letter = letter_sprites[char]
            
            # Scale if needed
            if scale != 1.0:
                new_width = int(letter.get_width() * scale)
                new_height = int(letter.get_height() * scale)
                letter = pygame.transform.scale(letter, (new_width, new_height))
            
            # Apply color tint if not white
            if color != WHITE:
                colored_letter = letter.copy()
                color_overlay = pygame.Surface(colored_letter.get_size(), pygame.SRCALPHA)
                color_overlay.fill(color)
                colored_letter.blit(color_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                letter = colored_letter
            
            surface.blit(letter, (x_pos, 0))
            x_pos += int((letter_sprites[char].get_width() + letter_spacing) * scale)
        elif char == ' ':
            x_pos += int((letter_width // 2 + letter_spacing) * scale)
    
    return surface

# Load letter sprites on initialization
loaded_count = load_letter_sprites()

base_pattern_duration = 5000
pattern_duration = base_pattern_duration
last_pattern_switch = 0
current_pattern = 0
cycle_count = 1

spiral_angle = 0
expanding_spiral_angle = 0
double_spiral_angle = 0

# Pattern state tracking
pattern_bullets_spawned = 0
pattern_spawn_timer = 0

# Randomized pattern order for each cycle
current_cycle_patterns = []
current_pattern_index = 0

# Load bullet sprite (will be overridden per enemy)
bullet_img = pygame.image.load("bullet.png").convert_alpha()
bullet_img = pygame.transform.scale(bullet_img, (12, 12))

def load_enemy_assets(enemy_id):
    """Load all assets for a specific enemy"""
    global background_frames, enemy_frames, hard_enemy_frames, bullet_img
    global background_current_frame, background_frame_counter
    global enemy_current_frame, enemy_frame_counter
    
    enemy_data = ENEMIES[enemy_id]
    bg_name = enemy_data["background"]
    
    # Reset animation counters
    background_current_frame = 0
    background_frame_counter = 0
    enemy_current_frame = 0
    enemy_frame_counter = 0
    
    # Load background for this enemy
    background_frames = []
    frame_num = 0
    while True:
        try:
            frame = pygame.image.load(f"{bg_name}_{frame_num}.png").convert()
            frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))
            background_frames.append(frame)
            frame_num += 1
        except:
            break
    
    if not background_frames:
        try:
            bg = pygame.image.load(f"{bg_name}.png").convert()
            bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
            background_frames = [bg]
        except:
            bg = pygame.Surface((WIDTH, HEIGHT))
            bg.fill(BLACK)
            background_frames = [bg]
    
    # Load enemy sprite for this enemy
    enemy_frames = []
    frame_num = 0
    while True:
        try:
            frame = pygame.image.load(f"enemy{enemy_id}_{frame_num}.png").convert_alpha()
            original_width, original_height = frame.get_size()
            scale_factor = min(600 / original_width, 600 / original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            frame = pygame.transform.scale(frame, (new_width, new_height))
            enemy_frames.append(frame)
            frame_num += 1
        except:
            break
    
    if not enemy_frames:
        try:
            enemy_img = pygame.image.load(f"enemy{enemy_id}.png").convert_alpha()
            original_width, original_height = enemy_img.get_size()
            scale_factor = min(600 / original_width, 600 / original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            enemy_img = pygame.transform.scale(enemy_img, (new_width, new_height))
            enemy_frames = [enemy_img]
        except:
            enemy_img = pygame.Surface((600, 600), pygame.SRCALPHA)
            pygame.draw.circle(enemy_img, RED, (300, 300), 250)
            enemy_frames = [enemy_img]
    
    # Load hard mode enemy sprite
    hard_enemy_frames = []
    frame_num = 0
    while True:
        try:
            frame = pygame.image.load(f"hard_enemy{enemy_id}_{frame_num}.png").convert_alpha()
            original_width, original_height = frame.get_size()
            scale_factor = min(600 / original_width, 600 / original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            frame = pygame.transform.scale(frame, (new_width, new_height))
            hard_enemy_frames.append(frame)
            frame_num += 1
        except:
            break
    
    if not hard_enemy_frames:
        try:
            hard_enemy_img = pygame.image.load(f"hard_enemy{enemy_id}.png").convert_alpha()
            original_width, original_height = hard_enemy_img.get_size()
            scale_factor = min(600 / original_width, 600 / original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            hard_enemy_img = pygame.transform.scale(hard_enemy_img, (new_width, new_height))
            hard_enemy_frames = [hard_enemy_img]
        except:
            # Fallback - purple tint
            hard_enemy_frames = []
            for frame in enemy_frames:
                hard_frame = frame.copy()
                purple_overlay = pygame.Surface(hard_frame.get_size())
                purple_overlay.fill((128, 0, 128))
                hard_frame.blit(purple_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
                hard_enemy_frames.append(hard_frame)
    
    # Load bullet sprite for this enemy
    try:
        bullet_img = pygame.image.load(f"bullet{enemy_id}.png").convert_alpha()
        bullet_img = pygame.transform.scale(bullet_img, (12, 12))
    except:
        # Use default bullet
        bullet_img = pygame.image.load("bullet.png").convert_alpha()
        bullet_img = pygame.transform.scale(bullet_img, (12, 12))
    
    # Load and play music for this enemy
    music_name = enemy_data["music"]
    music_loaded = False
    
    # Try multiple formats in order of preference: .ogg (best quality/performance), .mp3, .wav
    for ext in ['.ogg', '.mp3', '.wav']:
        try:
            pygame.mixer.music.load(music_name + ext)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            music_loaded = True
            break
        except:
            continue
    
    if not music_loaded:
        # Try without extension (in case it's already included)
        try:
            pygame.mixer.music.load(music_name)
            pygame.mixer.music.play(-1)
        except:
            pass  # No music file found, continue without music

# Initial load will be done after enemy selection

# Placeholder variables (will be set by load_enemy_assets)
background_frames = []
background_animation_speed = 10
background_current_frame = 0
background_frame_counter = 0

enemy_frames = []
hard_enemy_frames = []
enemy_animation_speed = 10
enemy_current_frame = 0
enemy_frame_counter = 0

# Enemy position (right side of screen)
enemy_x = WIDTH - 650
enemy_y = HEIGHT // 2 - 250

# Character sprites - single character only
try:
    player_img = pygame.image.load("player.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (30, 30))
    player_imgs = [player_img]  # Keep as list for compatibility
except:
    player_img = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(player_img, BLUE, (15, 15), 12)
    player_imgs = [player_img]

# Ally player sprites (single character)
try:
    ally_img = pygame.image.load("ally.png").convert_alpha()
    original_width, original_height = ally_img.get_size()
    scale_factor = min(600 / original_width, 600 / original_height)
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    ally_img = pygame.transform.scale(ally_img, (new_width, new_height))
    ally_frames_list = [[ally_img]]
except:
    ally_img = pygame.Surface((600, 600), pygame.SRCALPHA)
    pygame.draw.circle(ally_img, BLUE, (300, 300), 250)
    ally_frames_list = [[ally_img]]

ally_animation_speed = 10
ally_current_frame = 0
ally_frame_counter = 0

# Ally position (left side of screen, mirrored from enemy)
ally_x = 50
ally_y = HEIGHT // 2 - 250

def save_game():
    """Save game progress to file"""
    save_data = {
        "defeated_enemies": list(defeated_enemies),
        "current_enemy": current_enemy_id
    }
    try:
        with open(save_file, 'w') as f:
            json.dump(save_data, f)
    except:
        pass  # Fail silently if save doesn't work

def load_game():
    """Load game progress from file"""
    global defeated_enemies, current_enemy_id
    try:
        if os.path.exists(save_file):
            with open(save_file, 'r') as f:
                save_data = json.load(f)
                defeated_enemies = set(save_data.get("defeated_enemies", []))
                current_enemy_id = save_data.get("current_enemy", 4)
                return True
    except:
        pass
    return False

def initialize_character_stats():
    """Initialize player stats based on selected character"""
    global max_health, player_health
    stats = character_stats[selected_character]
    max_health = stats["max_health"]
    player_health = max_health

def get_character_damage_multiplier():
    """Get the damage multiplier for the selected character"""
    return character_stats[selected_character]["damage_multiplier"]

def create_hit_particles(x, y, count=4):
    """Create particle effects when player is hit - with particle limit to prevent crashes"""
    global particles
    
    # Limit particle creation if we're at max capacity
    available_slots = MAX_PARTICLES - len(particles)
    if available_slots <= 0:
        return  # Don't create particles if at limit
    
    # Create fewer particles if we're close to the limit
    actual_count = min(count, available_slots)
    
    for i in range(actual_count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)  # Slightly slower for better performance
        lifetime = random.randint(20, 40)  # Shorter lifetime (0.33-0.67 seconds)
        
        particles.append({
            'x': x,
            'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'size': random.uniform(0.2, 0.35)  # Slightly smaller for better performance
        })

def update_particles():
    """Update and remove expired particles"""
    for particle in particles[:]:
        particle['x'] += particle['vx']
        particle['y'] += particle['vy']
        particle['vy'] += 0.1  # Slight gravity effect
        particle['lifetime'] -= 1
        
        if particle['lifetime'] <= 0:
            particles.remove(particle)

def draw_particles():
    """Draw all active particles - optimized for performance"""
    if not particles:  # Early exit if no particles
        return
        
    for particle in particles:
        # Fade out particles as they age
        alpha = particle['lifetime'] / particle['max_lifetime']
        size = int(bullet_img.get_width() * particle['size'])
        
        # Skip very small or very faded particles
        if size <= 1 or alpha < 0.1:
            continue
            
        # Create a faded version of the bullet sprite
        particle_img = pygame.transform.scale(bullet_img, (size, size))
        # Apply alpha by creating a surface with per-pixel alpha
        faded_img = particle_img.copy()
        faded_img.set_alpha(int(255 * alpha))
        screen.blit(faded_img, (int(particle['x'] - size//2), int(particle['y'] - size//2)))

def draw_player():
    player_img = player_imgs[selected_character]
    
    if invincible_timer > 0:
        if (invincible_timer // 5) % 2 == 0:
            screen.blit(player_img, (player_pos[0] - player_img.get_width() // 2,
                                     player_pos[1] - player_img.get_height() // 2))
    else:
        screen.blit(player_img, (player_pos[0] - player_img.get_width() // 2,
                                 player_pos[1] - player_img.get_height() // 2))

def draw_bullet(bullet):
    if bullet['type'] == 'laser':
        rect = pygame.Rect(bullet['x'], bullet['y'], bullet['width'], bullet['height'])
        
        # Handle different laser colors
        if bullet.get('color') == 'blue':
            color = (173, 216, 230)
        elif bullet.get('color') == 'orange':
            color = (255, 165, 0)
        else:
            color = (255, 165, 0)  # Default to orange
            
        pygame.draw.rect(screen, color, rect)
    elif bullet['type'] == 'slash_attack':
        # Draw slash attack
        if bullet['state'] == 'warning':
            # Draw warning indicator (red outline)
            color = (255, 100, 100, 100)  # Semi-transparent red
            # Create rotated rectangle for the slash warning
            cos_angle = math.cos(math.radians(bullet['angle']))
            sin_angle = math.sin(math.radians(bullet['angle']))
            
            # Calculate corner points of rotated rectangle
            half_width = bullet['width'] // 2
            half_height = bullet['height'] // 2
            
            corners = [
                (-half_width, -half_height),
                (half_width, -half_height),
                (half_width, half_height),
                (-half_width, half_height)
            ]
            
            rotated_corners = []
            for corner_x, corner_y in corners:
                rot_x = corner_x * cos_angle - corner_y * sin_angle + bullet['x']
                rot_y = corner_x * sin_angle + corner_y * cos_angle + bullet['y']
                rotated_corners.append((rot_x, rot_y))
            
            pygame.draw.polygon(screen, (255, 100, 100), rotated_corners, 2)  # Red outline
        elif bullet['state'] == 'active':
            # Draw active slash (solid red)
            cos_angle = math.cos(math.radians(bullet['angle']))
            sin_angle = math.sin(math.radians(bullet['angle']))
            
            # Calculate corner points of rotated rectangle
            half_width = bullet['width'] // 2
            half_height = bullet['height'] // 2
            
            corners = [
                (-half_width, -half_height),
                (half_width, -half_height),
                (half_width, half_height),
                (-half_width, half_height)
            ]
            
            rotated_corners = []
            for corner_x, corner_y in corners:
                rot_x = corner_x * cos_angle - corner_y * sin_angle + bullet['x']
                rot_y = corner_x * sin_angle + corner_y * cos_angle + bullet['y']
                rotated_corners.append((rot_x, rot_y))
            
            pygame.draw.polygon(screen, (255, 50, 50), rotated_corners)  # Solid red
    else:
        # Scale bullet sprite based on size
        size_multiplier = bullet.get('size', 1)
        scaled_size = (int(bullet_img.get_width() * size_multiplier), 
                      int(bullet_img.get_height() * size_multiplier))
        scaled_img = pygame.transform.scale(bullet_img, scaled_size)
        
        # Rotate the bullet sprite
        rotated_img = pygame.transform.rotate(scaled_img, bullet['rotation'])
        rotated_rect = rotated_img.get_rect()
        rotated_rect.center = (int(bullet['x']), int(bullet['y']))
        screen.blit(rotated_img, rotated_rect)

def move_bullets():
    for bullet in bullets[:]:
        # Update rotation for all non-laser bullets that have rotation (except giant explosive bullets)
        if bullet['type'] not in ['laser', 'slash_attack'] and 'rotation_speed' in bullet:
            # Giant explosive bullets rotate slowly, all others rotate at same speed (5)
            if bullet['type'] == 'giant_explosive':
                bullet['rotation'] += bullet['rotation_speed']  # Keep original slow speed
            else:
                bullet['rotation'] += 5  # Uniform rotation speed for all other bullets
            
        if bullet['type'] == 'spiral':
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
        elif bullet['type'] == 'bouncing':
            # Move bullet
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
            
            # Bounce off play area walls
            if bullet['x'] - 6 < box_x or bullet['x'] + 6 > box_x + box_size:
                bullet['vx'] *= -1
                # Clamp position
                bullet['x'] = max(box_x + 6, min(box_x + box_size - 6, bullet['x']))
            
            if bullet['y'] - 6 < box_y or bullet['y'] + 6 > box_y + box_size:
                bullet['vy'] *= -1
                # Clamp position
                bullet['y'] = max(box_y + 6, min(box_y + box_size - 6, bullet['y']))
            
            # Decrease lifetime
            bullet['life_time'] -= 1
            if bullet['life_time'] <= 0:
                bullets.remove(bullet)
        elif bullet['type'] == 'targeted':
            if bullet.get('homing_delay', 0) > 0:
                bullet['homing_delay'] -= 1
                bullet['x'] += bullet['vx']
                bullet['y'] += bullet['vy']
            else:
                dx = player_pos[0] - bullet['x']
                dy = player_pos[1] - bullet['y']
                dist = math.hypot(dx, dy)
                if dist != 0:
                    bullet['x'] += (dx / dist) * bullet['speed']
                    bullet['y'] += (dy / dist) * bullet['speed']
            bullet['life_time'] -= 1
            if bullet['life_time'] <= 0:
                bullets.remove(bullet)
        elif bullet['type'] == 'radial':
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
        elif bullet['type'] == 'expanding_spiral':
            bullet['angle'] += 0.05
            bullet['radius'] += 1
            bullet['x'] = bullet['center_x'] + math.cos(bullet['angle']) * bullet['radius']
            bullet['y'] = bullet['center_y'] + math.sin(bullet['angle']) * bullet['radius']
        elif bullet['type'] == 'double_spiral':
            bullet['angle'] += bullet['direction'] * 0.06  # Slowed down from 0.15 to 0.06
            max_radius = max(WIDTH, HEIGHT) // 2 + 50  # Extend to screen border
            bullet['radius'] = min(bullet['radius'] + 0.5, max_radius)
            bullet['x'] = bullet['center_x'] + math.cos(bullet['angle']) * bullet['radius']
            bullet['y'] = bullet['center_y'] + math.sin(bullet['angle']) * bullet['radius']
            # Remove double spiral bullets when they reach max radius
            if bullet['radius'] >= max_radius:
                bullets.remove(bullet)
        elif bullet['type'] == 'rain':
            bullet['y'] -= bullet['speed']  # Changed to move upward (from bottom)
        elif bullet['type'] == 'laser':
            bullet['y'] += bullet['speed']
        elif bullet['type'] == 'zigzag':
            bullet['y'] += bullet['speed_y']
            bullet['x'] = bullet['base_x'] + math.sin(bullet['phase']) * bullet['amplitude']
            bullet['phase'] += bullet['frequency']
        elif bullet['type'] == 'zigzag_horizontal':
            bullet['x'] += bullet['speed_x']
            bullet['y'] = bullet['base_y'] + math.sin(bullet['phase']) * bullet['amplitude']
            bullet['phase'] += bullet['frequency']
        elif bullet['type'] == 'giant_explosive':
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
            bullet['life_time'] -= 1
            
            # Explode when life_time runs out
            if bullet['life_time'] <= 0 and not bullet.get('exploded', False):
                bullet['exploded'] = True
                # Create radial burst at explosion location
                explosion_x, explosion_y = bullet['x'], bullet['y']
                bullet_count = 24
                speed = 5
                for i in range(bullet_count):
                    angle = (2 * math.pi / bullet_count) * i
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    new_bullet = {
                        'x': explosion_x,
                        'y': explosion_y,
                        'vx': vx,
                        'vy': vy,
                        'type': 'radial',
                        'rotation': 0,
                        'rotation_speed': 5
                    }
                    bullets.append(new_bullet)
                
                # Remove the giant bullet after explosion
                bullets.remove(bullet)
                continue
        elif bullet['type'] == 'slash_attack':
            # Handle slash attack timing
            if bullet['state'] == 'delayed':
                # Count down delay before starting warning
                bullet['delay'] -= 1
                if bullet['delay'] <= 0:
                    bullet['state'] = 'warning'
            elif bullet['state'] == 'warning':
                bullet['warning_time'] -= 1
                if bullet['warning_time'] <= 0:
                    bullet['state'] = 'active'
            elif bullet['state'] == 'active':
                bullet['active_time'] -= 1
                if bullet['active_time'] <= 0:
                    bullets.remove(bullet)
                    continue
        
        # Remove bullets that have moved off screen (except for targeted bullets, bouncing bullets, and slash attacks which have their own life_time)
        if bullet['type'] not in ['targeted', 'giant_explosive', 'slash_attack', 'bouncing']:
            if (bullet['x'] < -50 or bullet['x'] > WIDTH + 50 or 
                bullet['y'] < -50 or bullet['y'] > HEIGHT + 50):
                if bullet in bullets:  # Safety check
                    bullets.remove(bullet)

def spawn_spiral():
    global spiral_angle
    center_x, center_y = WIDTH // 2, 150
    speed = 4 * apply_difficulty_scaling()
    vx = math.cos(spiral_angle) * speed
    vy = math.sin(spiral_angle) * speed
    bullet = {
        'x': center_x, 'y': center_y, 'vx': vx, 'vy': vy, 'type': 'spiral',
        'rotation': 0, 'rotation_speed': 5
    }
    bullets.append(bullet)
    spiral_angle += 0.15 * apply_difficulty_scaling()  # Spiral tighter at higher difficulty

def spawn_grid_slashes():
    """Spawn grid of slashes that rotate from squares to diamonds to squares"""
    # Grid parameters
    grid_cols = 3
    grid_rows = 3
    cell_width = box_size // grid_cols
    cell_height = box_size // grid_rows
    
    # Calculate positions for grid intersections
    for row in range(grid_rows + 1):
        for col in range(grid_cols + 1):
            x = box_x + col * cell_width
            y = box_y + row * cell_height
            
            # First wave: horizontal and vertical slashes (square pattern)
            # Horizontal slashes
            bullets.append({
                'x': x,
                'y': y,
                'type': 'slash_attack',
                'warning_time': 40,  # Longer warning for complex pattern
                'active_time': 8,    # Shorter active time
                'width': max(WIDTH, HEIGHT) * 2,
                'height': 8,
                'angle': 0,  # Horizontal
                'state': 'warning',
                'phase': 0,  # Track which phase this is
                'delay': 0   # No delay for first wave
            })
            # Vertical slashes
            bullets.append({
                'x': x,
                'y': y,
                'type': 'slash_attack',
                'warning_time': 40,
                'active_time': 8,
                'width': max(WIDTH, HEIGHT) * 2,
                'height': 8,
                'angle': 90,  # Vertical
                'state': 'warning',
                'phase': 0,
                'delay': 0
            })
            
            # Second wave: diagonal slashes (diamond pattern) - delayed
            bullets.append({
                'x': x,
                'y': y,
                'type': 'slash_attack',
                'warning_time': 40,
                'active_time': 8,
                'width': max(WIDTH, HEIGHT) * 2,
                'height': 8,
                'angle': 45,  # Diagonal
                'state': 'delayed',  # New state for delayed slashes
                'phase': 1,
                'delay': 60  # Delay before warning starts (1 second)
            })
            bullets.append({
                'x': x,
                'y': y,
                'type': 'slash_attack',
                'warning_time': 40,
                'active_time': 8,
                'width': max(WIDTH, HEIGHT) * 2,
                'height': 8,
                'angle': 135,  # Other diagonal
                'state': 'delayed',
                'phase': 1,
                'delay': 60
            })
            
            # Third wave: back to horizontal/vertical but offset positions
            offset_x = x + cell_width // 2
            offset_y = y + cell_height // 2
            
            # Only spawn if within play area
            if offset_x <= box_x + box_size and offset_y <= box_y + box_size:
                bullets.append({
                    'x': offset_x,
                    'y': offset_y,
                    'type': 'slash_attack',
                    'warning_time': 40,
                    'active_time': 8,
                    'width': max(WIDTH, HEIGHT) * 2,
                    'height': 8,
                    'angle': 0,
                    'state': 'delayed',
                    'phase': 2,
                    'delay': 120  # Delay 2 seconds
                })
                bullets.append({
                    'x': offset_x,
                    'y': offset_y,
                    'type': 'slash_attack',
                    'warning_time': 40,
                    'active_time': 8,
                    'width': max(WIDTH, HEIGHT) * 2,
                    'height': 8,
                    'angle': 90,
                    'state': 'delayed',
                    'phase': 2,
                    'delay': 120
                })

def spawn_bouncing_bullets():
    """Spawn bullets that bounce off the edges of the play area"""
    difficulty = apply_difficulty_scaling()
    num_bullets = min(5, int(3 * difficulty))
    
    for i in range(num_bullets):
        # Random starting position inside play area
        spawn_x = random.randint(box_x + 30, box_x + box_size - 30)
        spawn_y = random.randint(box_y + 30, box_y + box_size - 30)
        
        # Random velocity - faster at higher difficulty
        speed = random.uniform(3, 6) * difficulty
        angle = random.uniform(0, 2 * math.pi)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        
        bullet = {
            'x': spawn_x,
            'y': spawn_y,
            'vx': vx,
            'vy': vy,
            'type': 'bouncing',
            'rotation': 0,
            'rotation_speed': 5,
            'life_time': FPS * 8  # Last 8 seconds
        }
        bullets.append(bullet)

def spawn_targeted():
    spawn_x = random.randint(50, WIDTH - 50)
    spawn_y = 0
    speed = 3.5 * apply_difficulty_scaling()
    life_time = FPS * 5
    bullet = {
        'x': spawn_x, 'y': spawn_y, 'speed': speed, 'type': 'targeted', 
        'life_time': life_time, 'rotation': 0, 'rotation_speed': 5
    }
    bullets.append(bullet)

def spawn_radial_burst():
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    difficulty = apply_difficulty_scaling()
    bullet_count = min(36, int(24 * difficulty))  # More bullets at higher difficulty
    speed = 5 * difficulty
    for i in range(bullet_count):
        angle = (2 * math.pi / bullet_count) * i
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        bullet = {
            'x': center_x, 'y': center_y, 'vx': vx, 'vy': vy, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet)

def spawn_expanding_spiral():
    global expanding_spiral_angle
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    expanding_spiral_angle += 0.1 * apply_difficulty_scaling()
    bullet = {
        'center_x': center_x,
        'center_y': center_y,
        'angle': expanding_spiral_angle,
        'radius': 0,
        'type': 'expanding_spiral',
        'rotation': 0,
        'rotation_speed': 5
    }
    bullets.append(bullet)

def spawn_double_spiral():
    global double_spiral_angle
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    double_spiral_angle += 0.3 * apply_difficulty_scaling()

    for direction in (1, -1):
        bullet = {
            'center_x': center_x,
            'center_y': center_y,
            'angle': direction * double_spiral_angle,
            'radius': 0,
            'direction': direction,
            'type': 'double_spiral',
            'rotation': 0,
            'rotation_speed': 5 * direction
        }
        bullets.append(bullet)

def spawn_random_rain():
    # Can spawn from walls too now
    wall_choice = random.choice(['top', 'bottom', 'left', 'right'])
    speed = random.uniform(5, 8) * apply_difficulty_scaling()
    
    if wall_choice == 'top':
        spawn_x = random.randint(0, WIDTH)
        spawn_y = 0
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'speed': speed, 'type': 'rain',
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet)
    elif wall_choice == 'bottom':
        spawn_x = random.randint(0, WIDTH)
        spawn_y = HEIGHT
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'speed': -speed, 'type': 'rain',  # Negative speed to go upward
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet)
    elif wall_choice == 'left':
        spawn_x = 0
        spawn_y = random.randint(0, HEIGHT)
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'vx': speed, 'vy': 0, 'type': 'radial',  # Horizontal movement
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet)
    elif wall_choice == 'right':
        spawn_x = WIDTH
        spawn_y = random.randint(0, HEIGHT)
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'vx': -speed, 'vy': 0, 'type': 'radial',  # Horizontal movement
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet)

def spawn_homing_burst():
    # Spawn giant bullets that fall from above and explode into radial bursts
    difficulty = apply_difficulty_scaling()
    giant_bullet_count = min(8, int(5 * difficulty))
    
    for i in range(giant_bullet_count):
        # Random x position across the top of the screen
        spawn_x = random.randint(80, WIDTH - 80)
        spawn_y = -50  # Start above screen
        
        # Shorter detonation time at higher difficulty
        detonate_time = random.randint(int(FPS * 2.0 / difficulty), int(FPS * 3.0 / difficulty))
        
        bullet = {
            'x': spawn_x,
            'y': spawn_y,
            'vx': 0,  # No horizontal movement
            'vy': 3 * difficulty,  # Faster fall at higher difficulty
            'speed': 3 * difficulty,
            'type': 'giant_explosive',
            'life_time': detonate_time,
            'size': 5,  # 5x normal size
            'rotation': 0,
            'rotation_speed': random.uniform(2, 5),
            'exploded': False
        }
        bullets.append(bullet)

def spawn_laser_beams():
    beam_width = WIDTH
    beam_height = 10
    speed = 8 * apply_difficulty_scaling()
    y_start = 0
    color = random.choice(['blue', 'orange'])
    bullets.append({
        'x': 0,
        'y': y_start,
        'width': beam_width,
        'height': beam_height,
        'speed': speed,
        'type': 'laser',
        'color': color
    })

def spawn_cross_pattern():
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    speed = 6 * apply_difficulty_scaling()
    for offset in range(-112, 113, 56):  # Scaled by 0.75 from -150 to 150, step 75
        bullet1 = {
            'x': center_x + offset, 'y': 0, 'vx': 0, 'vy': speed, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet1)
        bullet2 = {
            'x': center_x + offset, 'y': HEIGHT, 'vx': 0, 'vy': -speed, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet2)
        bullet3 = {
            'x': 0, 'y': center_y + offset, 'vx': speed, 'vy': 0, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet3)
        bullet4 = {
            'x': WIDTH, 'y': center_y + offset, 'vx': -speed, 'vy': 0, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5
        }
        bullets.append(bullet4)

def spawn_zigzag_bullets():
    # Can spawn from walls too now
    wall_choice = random.choice(['top', 'bottom', 'left', 'right'])
    
    if wall_choice in ['top', 'bottom']:
        count = 6
        spacing = WIDTH // count
        start_y = 0 if wall_choice == 'top' else HEIGHT
        speed_y = 4 if wall_choice == 'top' else -4
        
        for i in range(count):
            base_x = i * spacing + spacing // 2
            bullet = {
                'base_x': base_x,
                'y': start_y,
                'speed_y': speed_y,
                'phase': 0,
                'amplitude': 45,  # Scaled by 0.75 from 60
                'frequency': 0.15,
                'type': 'zigzag',
                'rotation': 0,
                'rotation_speed': 5
            }
            bullets.append(bullet)
    else:  # left or right walls
        count = 6
        spacing = HEIGHT // count
        start_x = 0 if wall_choice == 'left' else WIDTH
        speed_x = 4 if wall_choice == 'left' else -4
        
        for i in range(count):
            base_y = i * spacing + spacing // 2
            bullet = {
                'base_y': base_y,
                'x': start_x,
                'speed_x': speed_x,
                'phase': 0,
                'amplitude': 45,  # Scaled by 0.75 from 60
                'frequency': 0.15,
                'type': 'zigzag_horizontal',
                'rotation': 0,
                'rotation_speed': 5
            }
            bullets.append(bullet)

def spawn_grid_rain():
    # Can spawn from walls too now
    wall_choice = random.choice(['top', 'bottom', 'left', 'right'])
    
    if wall_choice == 'top':
        rows = 7
        cols = 15
        spacing_x = WIDTH // cols
        spacing_y = 38  # Scaled by 0.75 from 50
        for row in range(rows):
            for col in range(cols):
                x = col * spacing_x + spacing_x // 2
                y = -row * spacing_y
                bullet = {
                    'x': x, 'y': y, 'speed': 5, 'type': 'rain',
                    'rotation': 0, 'rotation_speed': 5
                }
                bullets.append(bullet)
    elif wall_choice == 'bottom':
        rows = 7
        cols = 15
        spacing_x = WIDTH // cols
        spacing_y = 38  # Scaled by 0.75 from 50
        for row in range(rows):
            for col in range(cols):
                x = col * spacing_x + spacing_x // 2
                y = HEIGHT + row * spacing_y
                bullet = {
                    'x': x, 'y': y, 'speed': -5, 'type': 'rain',  # Negative speed to go upward
                    'rotation': 0, 'rotation_speed': 5
                }
                bullets.append(bullet)
    elif wall_choice == 'left':
        rows = 15
        cols = 7
        spacing_x = 38  # Scaled by 0.75 from 50
        spacing_y = HEIGHT // rows
        for row in range(rows):
            for col in range(cols):
                x = -col * spacing_x
                y = row * spacing_y + spacing_y // 2
                bullet = {
                    'x': x, 'y': y, 'vx': 5, 'vy': 0, 'type': 'radial',
                    'rotation': 0, 'rotation_speed': 5
                }
                bullets.append(bullet)
    elif wall_choice == 'right':
        rows = 15
        cols = 7
        spacing_x = 38  # Scaled by 0.75 from 50
        spacing_y = HEIGHT // rows
        for row in range(rows):
            for col in range(cols):
                x = WIDTH + col * spacing_x
                y = row * spacing_y + spacing_y // 2
                bullet = {
                    'x': x, 'y': y, 'vx': -5, 'vy': 0, 'type': 'radial',
                    'rotation': 0, 'rotation_speed': 5
                }
                bullets.append(bullet)

def spawn_slash_attacks():
    """Spawn slash attacks that target the player's current position"""
    # Create 3 slash attacks at random angles
    for i in range(3):
        target_x, target_y = player_pos[0], player_pos[1]
        
        bullets.append({
            'x': target_x,
            'y': target_y,
            'type': 'slash_attack',
            'warning_time': 30,  # Half second warning at 60 FPS
            'active_time': 10,   # How long the slash stays active
            'width': max(WIDTH, HEIGHT) * 2,  # Much longer - double the screen size
            'height': 12,        # Slightly taller as well
            'angle': random.uniform(0, 360),  # Random angle for variety
            'state': 'warning'   # 'warning' then 'active'
        })

def get_pattern_config(pattern_id):
    """Returns (total_bullets, spawn_interval) for each pattern"""
    configs = {
        0: (330, 1),      # spiral: ~330 bullets over 5 seconds
        1: (10, 30),      # bouncing: 10 volleys (30 bullets total)
        2: (16, 30),      # targeted: 16 bullets
        3: (5, 100),      # radial_burst: 5 bursts (120 bullets total)
        4: (100, 5),      # expanding_spiral: 100 bullets
        5: (100, 5),      # double_spiral: 100 spawns (200 bullets total)
        6: (166, 3),      # random_rain: 166 bullets
        7: (5, 100),      # giant_explosive: 5 giant bullets (120 explosion bullets total)
        8: (8, 60),       # laser_beams: 8 beams
        9: (5, 100),      # cross_pattern: 5 crosses (80 bullets total)
        10: (10, 50),     # zigzag: 10 volleys (60 bullets total)
        11: (2, 200),     # grid_rain: 2 grids (210 bullets total)
        12: (8, 50),      # slash_attacks: 8 volleys (24 slashes total)
        13: (1, 500),     # grid_slashes: 1 spawn (complex pattern, long duration)
    }
    return configs.get(pattern_id, (100, 10))

def randomize_cycle_patterns():
    """Create a randomized selection of 8 patterns for the current cycle"""
    global current_cycle_patterns, current_pattern_index
    
    # Get enemy data for difficulty-based pattern selection
    enemy_data = ENEMIES[current_enemy_id]
    available_patterns = enemy_data["attacks"]
    
    # Shuffle available patterns
    shuffled = list(available_patterns)
    random.shuffle(shuffled)
    
    # Select patterns based on difficulty
    difficulty = enemy_data["difficulty"]
    
    if difficulty <= 0.5:  # Easier enemies (1-2)
        pattern_count = 5
    elif difficulty <= 0.9:  # Medium enemies (3)
        pattern_count = 6
    elif difficulty <= 1.1:  # Current difficulty (4)
        pattern_count = 8
    elif difficulty <= 1.5:  # Harder (5)
        pattern_count = 9
    elif difficulty <= 1.8:  # Very hard (6)
        pattern_count = 10
    else:  # Hardest (7-8)
        pattern_count = min(12, len(shuffled))
    
    current_cycle_patterns = shuffled[:pattern_count]
    current_pattern_index = 0

def apply_difficulty_scaling():
    """Apply difficulty scaling to bullet speeds and spawn rates based on enemy"""
    enemy_data = ENEMIES[current_enemy_id]
    difficulty = enemy_data["difficulty"]
    
    # This multiplier affects:
    # - Bullet speeds (applied in spawn functions)
    # - Spawn intervals (patterns spawn faster)
    # - Pattern duration (cycles complete faster at higher difficulty)
    
    return difficulty

def is_cycle_complete():
    """Check if the cycle is complete (all patterns done and no bullets left)"""
    # Check if all patterns have been completed
    patterns_complete = current_pattern_index >= len(current_cycle_patterns)
    
    # Check if there are any active bullets
    active_bullets = len(bullets) > 0
    
    return patterns_complete and not active_bullets

def handle_pattern_spawning():
    global pattern_bullets_spawned, pattern_spawn_timer, current_pattern_index, points
    
    # If all patterns are complete, don't spawn anything new
    if current_pattern_index >= len(current_cycle_patterns):
        return True  # All patterns complete
    
    if not current_cycle_patterns:
        randomize_cycle_patterns()
    
    current_pattern = current_cycle_patterns[current_pattern_index]
    total_bullets, spawn_interval = get_pattern_config(current_pattern)
    
    # Check if current pattern is complete
    if pattern_bullets_spawned >= total_bullets:
        # Move to next pattern
        current_pattern_index += 1
        pattern_bullets_spawned = 0
        pattern_spawn_timer = 0
        
        return current_pattern_index >= len(current_cycle_patterns)  # Return true if all patterns done
    
    # Check if it's time to spawn
    pattern_spawn_timer += 1
    if pattern_spawn_timer >= spawn_interval:
        pattern_spawn_timer = 0
        
        # Spawn bullets based on current pattern
        if current_pattern == 0:
            spawn_spiral()
            pattern_bullets_spawned += 1
        elif current_pattern == 1:
            spawn_bouncing_bullets()
            pattern_bullets_spawned += 1
        elif current_pattern == 2:
            spawn_targeted()
            pattern_bullets_spawned += 1
        elif current_pattern == 3:
            spawn_radial_burst()
            pattern_bullets_spawned += 1
        elif current_pattern == 4:
            spawn_expanding_spiral()
            pattern_bullets_spawned += 1
        elif current_pattern == 5:
            spawn_double_spiral()
            pattern_bullets_spawned += 1
        elif current_pattern == 6:
            spawn_random_rain()
            pattern_bullets_spawned += 1
        elif current_pattern == 7:
            spawn_homing_burst()
            pattern_bullets_spawned += 1
        elif current_pattern == 8:
            spawn_laser_beams()
            pattern_bullets_spawned += 1
        elif current_pattern == 9:
            spawn_cross_pattern()
            pattern_bullets_spawned += 1
        elif current_pattern == 10:
            spawn_zigzag_bullets()
            pattern_bullets_spawned += 1
        elif current_pattern == 11:
            spawn_grid_rain()
            pattern_bullets_spawned += 1
        elif current_pattern == 12:
            spawn_slash_attacks()
            pattern_bullets_spawned += 1
        elif current_pattern == 13:
            spawn_grid_slashes()
            pattern_bullets_spawned += 1
    
    return False  # Pattern not complete

def check_collisions():
    global player_health, invincible_timer, points
    keys = pygame.key.get_pressed()
    moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]
    
    # Check regular bullet collisions
    for bullet in bullets[:]:
        if bullet['type'] == 'laser':
            rect = pygame.Rect(bullet['x'], bullet['y'], bullet['width'], bullet['height'])
            if abs(player_pos[0] - rect.centerx) < rect.width // 2 + player_radius and abs(player_pos[1] - rect.centery) < rect.height // 2 + player_radius:
                if invincible_timer <= 0:
                    if bullet.get('color') == 'blue' and moving:
                        damage = 1
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
                    elif bullet.get('color') == 'orange' and not moving:
                        damage = 1
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
        elif bullet['type'] == 'slash_attack':
            # Only check collision when slash is active
            if bullet['state'] == 'active':
                # Check if player is within the rotated rectangle of the slash
                cos_angle = math.cos(math.radians(bullet['angle']))
                sin_angle = math.sin(math.radians(bullet['angle']))
                
                # Translate player position relative to slash center
                rel_x = player_pos[0] - bullet['x']
                rel_y = player_pos[1] - bullet['y']
                
                # Rotate player position to align with slash rectangle
                rotated_x = rel_x * cos_angle + rel_y * sin_angle
                rotated_y = -rel_x * sin_angle + rel_y * cos_angle
                
                # Check if within rectangle bounds
                if (abs(rotated_x) < bullet['width'] // 2 + player_radius and 
                    abs(rotated_y) < bullet['height'] // 2 + player_radius):
                    if invincible_timer <= 0:
                        damage = bullet.get('damage', 1)  # Allow variable damage
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
        elif bullet['type'] == 'zigzag_horizontal':
            # Handle horizontal zigzag collision - use scaled collision radius
            collision_radius = bullet_img.get_width() // 2  # This is now 6 pixels (12/2)
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                if invincible_timer <= 0:
                    damage = bullet.get('damage', 1)  # Allow variable damage
                    player_health -= damage
                    invincible_timer = INVINCIBLE_DURATION
                    create_hit_particles(player_pos[0], player_pos[1])
                    bullets.remove(bullet)
        else:
            collision_radius = bullet_img.get_width() // 2  # This is now 6 pixels (12/2)
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                if invincible_timer <= 0:
                    damage = bullet.get('damage', 1)  # Allow variable damage
                    player_health -= damage
                    invincible_timer = INVINCIBLE_DURATION
                    create_hit_particles(player_pos[0], player_pos[1])
                    bullets.remove(bullet)

def draw_play_area():
    """Draw the play area box with semi-transparent background and white border"""
    # Create semi-transparent black background
    box_surface = pygame.Surface((box_size, box_size))
    box_surface.set_alpha(128)  # 50% transparency
    box_surface.fill(BLACK)
    screen.blit(box_surface, (box_x, box_y))
    
    # Draw white border (solid)
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_size, box_size), 2)
    
    # Draw enemy health bar below the box
    health_bar_width = box_size
    health_bar_height = 20
    health_bar_x = box_x
    health_bar_y = box_y + box_size + 10  # 10 pixels below the box
    
    # Background
    pygame.draw.rect(screen, (50, 50, 50), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
    
    # Health fill
    health_ratio = enemy_health / max_enemy_health
    health_fill_width = int(health_bar_width * health_ratio)
    pygame.draw.rect(screen, RED, (health_bar_x, health_bar_y, health_fill_width, health_bar_height))
    
    # Border
    pygame.draw.rect(screen, WHITE, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
    
    # Health text
    health_text = render_text(f"ENEMY: {enemy_health}/{max_enemy_health}", WHITE, 0.6)
    health_text_rect = health_text.get_rect(center=(box_x + box_size // 2, health_bar_y + health_bar_height // 2))
    screen.blit(health_text, health_text_rect)

def draw_background():
    """Draw the background with animation support"""
    global background_frame_counter, background_current_frame, background_animation_speed
    
    # Update animation frame
    background_frame_counter += 1
    if background_frame_counter >= background_animation_speed:
        background_frame_counter = 0
        background_current_frame = (background_current_frame + 1) % len(background_frames)
    
    # Draw current frame
    screen.blit(background_frames[background_current_frame], (0, 0))

def draw_enemy():
    """Draw the enemy sprite on the right side of the screen (with animation support)"""
    global enemy_frame_counter, enemy_current_frame, enemy_animation_speed
    
    # Choose which frames to use based on hard mode
    frames_to_use = hard_enemy_frames if hard_mode_active else enemy_frames
    
    # Update animation frame
    enemy_frame_counter += 1
    if enemy_frame_counter >= enemy_animation_speed:
        enemy_frame_counter = 0
        enemy_current_frame = (enemy_current_frame + 1) % len(frames_to_use)
    
    # Draw current frame
    screen.blit(frames_to_use[enemy_current_frame], (enemy_x, enemy_y))

def draw_ally():
    """Draw the ally sprite on the left side of the screen - changes based on selected character (with animation support)"""
    global ally_frame_counter, ally_current_frame, ally_animation_speed
    
    # Get frames for selected character
    ally_frames = ally_frames_list[selected_character]
    
    # Update animation frame
    ally_frame_counter += 1
    if ally_frame_counter >= ally_animation_speed:
        ally_frame_counter = 0
        ally_current_frame = (ally_current_frame + 1) % len(ally_frames)
    
    # Draw current frame
    screen.blit(ally_frames[ally_current_frame], (ally_x, ally_y))

def handle_input():
    keys = pygame.key.get_pressed()
    
    # Handle movement with confinement to play area box
    if keys[pygame.K_w] and player_pos[1] - player_speed - player_radius > box_y:
        player_pos[1] -= player_speed
    if keys[pygame.K_s] and player_pos[1] + player_speed + player_radius < box_y + box_size:
        player_pos[1] += player_speed
    if keys[pygame.K_a] and player_pos[0] - player_speed - player_radius > box_x:
        player_pos[0] -= player_speed
    if keys[pygame.K_d] and player_pos[0] + player_speed + player_radius < box_x + box_size:
        player_pos[0] += player_speed

def draw_health():
    character_name = character_stats[selected_character]["name"]
    
    # Use custom text rendering
    health_text = render_text(f"HEALTH: {player_health}/{max_health}", WHITE, 1.0)
    screen.blit(health_text, (10, 10))
    
    cycle_text = render_text(f"CYCLE: {cycle_count}", WHITE, 1.0)
    screen.blit(cycle_text, (10, 45))
    
    char_text = render_text(f"CHARACTER: {character_name}", WHITE, 0.7)
    screen.blit(char_text, (10, 80))

def trigger_hard_mode():
    """Trigger a really hard attack phase with bullets that deal 2 damage"""
    global bullets, hard_mode_active
    
    # Activate hard mode sprite
    hard_mode_active = True
    
    # Clear existing bullets
    bullets.clear()
    
    # Give the player a brief moment before bullets start
    # Spawn difficult but not instant-death patterns
    
    # Dense spiral from center (slower than before)
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    for angle_offset in range(0, 360, 10):  # Every 10 degrees instead of 5
        angle = math.radians(angle_offset)
        speed = 4  # Slower (was 6)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        bullet = {
            'x': center_x,
            'y': center_y,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'damage': 2  # 2 damage bullets
        }
        bullets.append(bullet)
    
    # Multiple slash attacks at the player position (but with warning time)
    for i in range(4):  # 4 slashes instead of 6
        bullets.append({
            'x': player_pos[0],
            'y': player_pos[1],
            'type': 'slash_attack',
            'warning_time': 30,  # Full warning time
            'active_time': 12,
            'width': max(WIDTH, HEIGHT) * 2,
            'height': 15,
            'angle': i * 90,  # Evenly spaced instead of random
            'state': 'warning',
            'damage': 2  # 2 damage slashes
        })
    
    # Grid of bullets from sides (less dense, slower)
    spacing = 80  # More spacing (was 40)
    speed = 5  # Slower (was 7)
    
    for x in range(0, WIDTH, spacing):
        bullets.append({
            'x': x,
            'y': 0,
            'vx': 0,
            'vy': speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'damage': 2
        })
        bullets.append({
            'x': x,
            'y': HEIGHT,
            'vx': 0,
            'vy': -speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'damage': 2
        })
    
    for y in range(0, HEIGHT, spacing):
        bullets.append({
            'x': 0,
            'y': y,
            'vx': speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'damage': 2
        })
        bullets.append({
            'x': WIDTH,
            'y': y,
            'vx': -speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'damage': 2
        })

def show_attack_phase():
    """Show attack phase with flavor text sprite and QTE"""
    global attack_active, qte_active, qte_position, qte_direction, enemy_health, player_health
    
    attack_active = True
    
    # Choose random flavor text sprite
    flavor_sprite = random.choice(attack_flavor_texts)
    
    # Show flavor text screen
    showing_flavor = True
    space_pressed = False
    
    while showing_flavor:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not space_pressed:
                    space_pressed = True
                    showing_flavor = False
        
        # Draw background
        draw_background()
        
        # Draw ally and enemy
        draw_ally()
        draw_enemy()
        
        # Draw flavor text sprite (centered)
        flavor_rect = flavor_sprite.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(flavor_sprite, flavor_rect)
        
        # Draw instruction
        instruction = render_text("PRESS SPACE TO CONTINUE", WHITE, 0.7)
        instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        screen.blit(instruction, instruction_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Start QTE
    qte_active = True
    qte_position = 0
    qte_direction = 1
    hit_registered = False
    freeze_frames = 30  # Half second at 60 FPS
    fade_frames = 30  # Half second fade
    frozen_frame = None
    damage_dealt = 0
    hit_quality = ""
    hit_color = WHITE
    
    while qte_active:
        space_pressed_in_qte = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not space_pressed_in_qte and not hit_registered:
                    space_pressed_in_qte = True
                    hit_registered = True
                    
                    # Calculate damage based on position
                    distance_from_target = abs(qte_position - qte_target_position)
                    
                    # Get character damage multiplier
                    char_damage_mult = get_character_damage_multiplier()
                    
                    if distance_from_target <= qte_perfect_range:
                        damage_dealt = int(20 * char_damage_mult)  # Perfect hit
                        hit_quality = "PERFECT!"
                        hit_color = YELLOW
                    elif distance_from_target <= qte_good_range:
                        damage_dealt = int(15 * char_damage_mult)  # Good hit
                        hit_quality = "GOOD!"
                        hit_color = GREEN
                    else:
                        # Scale damage from 1-10 based on distance
                        max_distance = qte_bar_length // 2
                        base_damage = max(1, int(10 * (1 - distance_from_target / max_distance)))
                        damage_dealt = int(base_damage * char_damage_mult)
                        hit_quality = "HIT"
                        hit_color = WHITE
                    
                    # Heal 2 HP on attack
                    player_health = min(max_health, player_health + 2)
                    
                    # Check if this would kill the enemy
                    would_kill = enemy_health - damage_dealt <= 0
                    
                    # 1/100 chance for hard mode if attack would kill
                    hard_mode_triggered = False
                    if would_kill and random.randint(1, 100) == 1:
                        hard_mode_triggered = True
                        enemy_health = 1  # Enemy survives at 1 HP
                    else:
                        enemy_health = max(0, enemy_health - damage_dealt)
                    
                    # Check if enemy was killed
                    enemy_killed = enemy_health <= 0
                    
                    # Special mechanic for Sans (Enemy 6) - he "dodges" the first few attacks
                    if current_enemy_id == 6 and enemy_killed:
                        # Sans has dodged! Restore health and count dodges
                        if not hasattr(show_attack_phase, 'sans_dodge_count'):
                            show_attack_phase.sans_dodge_count = 0
                        
                        if show_attack_phase.sans_dodge_count < 3:  # He dodges 3 times
                            enemy_health = 1
                            show_attack_phase.sans_dodge_count += 1
                            enemy_killed = False
                            # Override hit text to show dodge
                            hit_quality = "DODGE!"
                            hit_color = (100, 200, 255)  # Light blue
                    
                    if enemy_killed:
                        # Mark as defeated - player wins this fight
                        defeated_enemies.add(current_enemy_id)
                        save_game()
                        # Full heal for next fight
                        player_health = max_health
                        # Reset enemy health
                        enemy_health = max_enemy_health
                        # Deactivate hard mode sprite
                        hard_mode_active = False
                        # Set flag to exit to menu
                        qte_active = False
                        attack_active = False
                        return  # Exit attack phase immediately
                    
                    # Capture the frozen frame
                    frozen_frame = screen.copy()
        
        if not hit_registered:
            # Update QTE position
            qte_position += qte_speed * qte_direction
            
            # Bounce at edges
            if qte_position <= 0 or qte_position >= 100:
                qte_direction *= -1
        
            # Draw QTE screen
            draw_background()
            draw_ally()
            draw_enemy()
            
            # Draw QTE bar
            bar_x = WIDTH // 2 - qte_bar_length // 2
            bar_y = HEIGHT // 2
            bar_height = 40
            
            # Draw bar background
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, qte_bar_length, bar_height))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, qte_bar_length, bar_height), 3)
            
            # Draw target zone (middle)
            target_x = bar_x + qte_bar_length // 2 - 30
            pygame.draw.rect(screen, GREEN, (target_x, bar_y, 60, bar_height))
            
            # Draw perfect zone
            perfect_x = bar_x + qte_bar_length // 2 - 10
            pygame.draw.rect(screen, YELLOW, (perfect_x, bar_y, 20, bar_height))
            
            # Draw moving indicator
            indicator_x = bar_x + int((qte_position / 100) * qte_bar_length)
            pygame.draw.rect(screen, RED, (indicator_x - 5, bar_y - 10, 10, bar_height + 20))
            
            # Draw instruction
            instruction = render_text("PRESS SPACE TO ATTACK!", WHITE, 1.0)
            instruction_rect = instruction.get_rect(center=(WIDTH // 2, bar_y - 50))
            screen.blit(instruction, instruction_rect)
            
            pygame.display.flip()
            clock.tick(FPS)
        else:
            # Freeze phase
            if freeze_frames > 0:
                screen.blit(frozen_frame, (0, 0))
                
                # Draw hit result text
                result_text = render_text(f"{hit_quality}", hit_color, 2.0)
                result_rect = result_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
                screen.blit(result_text, result_rect)
                
                damage_text = render_text(f"{damage_dealt} DAMAGE!", hit_color, 1.0)
                damage_rect = damage_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
                screen.blit(damage_text, damage_rect)
                
                freeze_frames -= 1
                pygame.display.flip()
                clock.tick(FPS)
            # Fade phase
            elif fade_frames > 0:
                # Calculate fade alpha
                alpha = int(255 * (fade_frames / 30))
                
                # Create faded version of frozen frame
                faded_frame = frozen_frame.copy()
                fade_surface = pygame.Surface((WIDTH, HEIGHT))
                fade_surface.fill(BLACK)
                fade_surface.set_alpha(255 - alpha)
                faded_frame.blit(fade_surface, (0, 0))
                
                screen.blit(faded_frame, (0, 0))
                
                # Draw fading text
                result_text = render_text(f"{hit_quality}", hit_color, 2.0)
                result_text.set_alpha(alpha)
                result_rect = result_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
                screen.blit(result_text, result_rect)
                
                damage_text = render_text(f"{damage_dealt} DAMAGE!", hit_color, 1.0)
                damage_text.set_alpha(alpha)
                damage_rect = damage_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
                screen.blit(damage_text, damage_rect)
                
                fade_frames -= 1
                pygame.display.flip()
                clock.tick(FPS)
            else:
                # Done - check if we need to trigger hard mode
                if hard_mode_triggered:
                    trigger_hard_mode()
                
                qte_active = False
                attack_active = False

def enemy_selection_screen():
    """Show enemy selection screen with defeated status"""
    global current_enemy_id, defeated_enemies
    
    selected_enemy = 1
    
    # Check if secret enemy is unlocked
    secret_unlocked = len(defeated_enemies) >= 7
    
    while True:
        screen.fill(BLACK)
        
        # Title
        title_text = render_text("SELECT ENEMY", WHITE, 2.0)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Enemy list
        y_pos = 250
        for enemy_id in range(1, 9):
            # Skip secret enemy if not unlocked
            if enemy_id == 8 and not secret_unlocked:
                continue
            
            enemy_data = ENEMIES[enemy_id]
            enemy_name = enemy_data["name"]
            
            # Check if defeated
            is_defeated = enemy_id in defeated_enemies
            is_selected = enemy_id == selected_enemy
            
            # Color coding
            if is_selected:
                color = YELLOW
            elif is_defeated:
                color = GREEN
            else:
                color = WHITE
            
            # Draw enemy name
            text = render_text(f"{enemy_id}. {enemy_name}", color, 1.2)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_pos))
            
            # Show defeated status
            if is_defeated:
                defeated_text = render_text("[DEFEATED]", GREEN, 0.6)
                screen.blit(defeated_text, (WIDTH // 2 + text.get_width() // 2 + 20, y_pos + 10))
            
            y_pos += 60
        
        # Instructions
        instructions = render_text("W/S: SELECT - SPACE: FIGHT/REMATCH", WHITE, 0.6)
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 150))
        
        if secret_unlocked:
            secret_text = render_text("SECRET ENEMY UNLOCKED!", YELLOW, 0.7)
            screen.blit(secret_text, (WIDTH // 2 - secret_text.get_width() // 2, HEIGHT - 100))
        else:
            secret_text = render_text("DEFEAT ALL 7 ENEMIES TO UNLOCK SECRET BOSS", (128, 128, 128), 0.5)
            screen.blit(secret_text, (WIDTH // 2 - secret_text.get_width() // 2, HEIGHT - 100))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    selected_enemy -= 1
                    if selected_enemy < 1:
                        selected_enemy = 8 if secret_unlocked else 7
                    if selected_enemy == 8 and not secret_unlocked:
                        selected_enemy = 7
                elif event.key == pygame.K_s:
                    selected_enemy += 1
                    max_enemy = 8 if secret_unlocked else 7
                    if selected_enemy > max_enemy:
                        selected_enemy = 1
                    if selected_enemy == 8 and not secret_unlocked:
                        selected_enemy = 1
                elif event.key == pygame.K_SPACE:
                    current_enemy_id = selected_enemy
                    return
                elif event.key == pygame.K_u:
                    # Debug: Unlock all bosses
                    defeated_enemies = {1, 2, 3, 4, 5, 6, 7}
                    save_game()
                    secret_unlocked = True  # Update immediately
        
        clock.tick(FPS)

def start_screen():
    """Main menu with New Game and Continue options"""
    
    # Check if save file exists
    has_save = os.path.exists(save_file)
    selected_option = 0 if not has_save else 1  # Default to New Game if no save
    
    options = ["NEW GAME"]
    if has_save:
        options.append("CONTINUE")
    options.append("QUIT")

    while True:
        screen.fill(BLACK)
        
        title_text = render_text("BUR", WHITE, 3.0)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3))
        
        # Draw options
        y_pos = HEIGHT // 2
        for i, option in enumerate(options):
            color = YELLOW if i == selected_option else WHITE
            option_text = render_text(option, color, 1.2)
            screen.blit(option_text, (WIDTH // 2 - option_text.get_width() // 2, y_pos))
            y_pos += 60

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_s:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_SPACE:
                    if options[selected_option] == "NEW GAME":
                        # Reset save data
                        global defeated_enemies, current_enemy_id
                        defeated_enemies = set()
                        current_enemy_id = 4
                        save_game()
                        return
                    elif options[selected_option] == "CONTINUE":
                        load_game()
                        return
                    elif options[selected_option] == "QUIT":
                        pygame.quit()
                        exit()
        
        clock.tick(FPS)

def main():
    global last_pattern_switch, current_pattern, invincible_timer, pattern_duration, cycle_count
    global pattern_bullets_spawned, pattern_spawn_timer, current_pattern_index
    global enemy_health, max_enemy_health, defeated_enemies, hard_mode_active
    
    start_screen()
    enemy_selection_screen()
    
    # Load assets for selected enemy
    load_enemy_assets(current_enemy_id)
    
    # Set enemy health based on selected enemy
    enemy_data = ENEMIES[current_enemy_id]
    max_enemy_health = enemy_data["max_health"]
    enemy_health = max_enemy_health
    hard_mode_active = False  # Reset hard mode for new fight
    
    initialize_character_stats()
    
    running = True
    last_pattern_switch = pygame.time.get_ticks()
    
    # Initialize pattern tracking
    pattern_bullets_spawned = 0
    pattern_spawn_timer = 0
    randomize_cycle_patterns()  # Initialize randomized pattern order
    
    # Set player to center of play area box
    player_pos[0] = WIDTH // 2
    player_pos[1] = HEIGHT // 2
    
    while running:
        dt = clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Regular game logic
        handle_input()

        # Handle pattern spawning
        all_patterns_spawned = handle_pattern_spawning()
        
        # Check if cycle is complete (all patterns done AND no bullets left)
        if is_cycle_complete():
            cycle_count += 1
            
            # End i-frames and reset player position
            invincible_timer = 0
            player_pos[0] = WIDTH // 2
            player_pos[1] = HEIGHT // 2
            
            # Show attack phase instead of shop
            show_attack_phase()
            
            # Reset for new cycle
            pattern_duration = max(1000, int(base_pattern_duration * (0.9 ** cycle_count)))
            last_pattern_switch = pygame.time.get_ticks()
            # Reset pattern tracking for new cycle
            pattern_bullets_spawned = 0
            pattern_spawn_timer = 0
            randomize_cycle_patterns()  # Randomize patterns for new cycle

        move_bullets()
        update_particles()
        check_collisions()

        if invincible_timer > 0:
            invincible_timer -= 1

        # Draw background sprite
        draw_background()
        
        # Draw ally
        draw_ally()
        
        # Draw enemy
        draw_enemy()
        
        # Draw play area box
        draw_play_area()
        
        draw_player()
        for bullet in bullets:
            draw_bullet(bullet)
        draw_particles()
        draw_health()

        if player_health <= 0:
            game_over_text = render_text("GAME OVER", RED, 2.5)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
            retry_text = render_text("PRESS SPACE TO RETURN TO MENU", WHITE, 0.8)
            screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 80))
            pygame.display.flip()
            
            # Wait for space to return to menu
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            waiting = False
                            running = False
                clock.tick(FPS)
        
        # Check if enemy was defeated (handled in attack phase, will exit to menu)
        if current_enemy_id in defeated_enemies and enemy_health >= max_enemy_health:
            # Enemy was just defeated, show victory and return to menu
            victory_text = render_text("VICTORY!", GREEN, 2.5)
            screen.blit(victory_text, (WIDTH // 2 - victory_text.get_width() // 2, HEIGHT // 2))
            continue_text = render_text("PRESS SPACE TO CONTINUE", WHITE, 0.8)
            screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT // 2 + 80))
            pygame.display.flip()
            
            # Wait for space
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            waiting = False
                            running = False
                clock.tick(FPS)

        pygame.display.flip()

    pygame.mixer.music.stop()
    
    # Return to menu
    main()

if __name__ == "__main__":
    main()
