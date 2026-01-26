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

# Enemy definitions - Each enemy has completely unique attacks
ENEMIES = {
    1: {
        "name": "Comedy and Tragedy",
        "background": "stage",
        "music": "tv_world",
        "difficulty": 0.4,
        "max_health": 80,
        "attacks": [14, 15, 16, 17, 18]  # Theater Curtain, Spotlight Dance, Mask Spiral, Drama Waves, Comedy Rain
    },
    2: {
        "name": "Diego",
        "background": "desert",
        "music": "friend_inside_me",
        "difficulty": 0.6,
        "max_health": 85,
        "attacks": [19, 20, 21, 22, 23]  # Tumbleweed Roll, Cactus Burst, Dust Devil, High Noon, Lasso Spin
    },
    3: {
        "name": "Shred Master",
        "background": "cyber_city",
        "music": "fandago",
        "difficulty": 0.8,
        "max_health": 90,
        "attacks": [24, 25, 26, 27, 28]  # Dance Routine, Bass Drop, Neon Pulse, CD Throw, Synth Wave
    },
    4: {
        "name": "Spamton NEO",
        "background": "queens_basement",
        "music": "big_shot",
        "difficulty": 1.0,
        "max_health": 100,
        "attacks": [29, 30, 31, 32, 33]  # Pipis Spread, Phone Attack, Deal Maker, Big Shot, Hyperlink Blocked
    },
    5: {
        "name": "The Roaring Knight",
        "background": "fountain",
        "music": "the_roaring_knight",
        "difficulty": 1.3,
        "max_health": 120,
        "attacks": [13, 34, 35, 36, 37]  # Grid Slashes, Shadow Crystal, Dark Fountain, Knight's Lance, Roaring Blast
    },
    6: {
        "name": "Sans",
        "background": "hall_of_judgment",
        "music": "musclememory",
        "difficulty": 1.6,
        "max_health": 1,
        "attacks": [38, 39, 40, 41, 42]  # Bone Zone, Gaster Blaster, Blue Attack, Karma, Dunked On
    },
    7: {
        "name": "Susie",
        "background": "forest_light",
        "music": "megalovania_susie",
        "difficulty": 2.0,
        "max_health": 150,
        "attacks": [43, 44, 45, 46, 47]  # Rude Buster, Axe Throw, Ultimate Heal, Red Buster, Tail Whip
    },
    8: {
        "name": "???",
        "background": "forest_dark",
        "music": "fun_value",
        "difficulty": 2.5,
        "max_health": 200,
        "attacks": [48, 49, 50, 51, 52]  # Void Convergence, Reality Break, Glitch Storm, Delete, Corruption
    }
}

# Game state
current_enemy_id = 4  # Start with Spamton NEO
defeated_enemies = set()  # Track which enemies have been beaten
save_file = "bur_save.json"
hard_mode_active = False  # Track if we're in hard mode

def find_file(filename):
    """Recursively search for a file starting from current directory"""
    import os
    for root, dirs, files in os.walk('.'):
        if filename in files:
            return os.path.join(root, filename)
    return None

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
    filepath = find_file(f"attack_text_{flavor_text_num}.png")
    if filepath:
        try:
            flavor_sprite = pygame.image.load(filepath).convert_alpha()
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
    else:
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
    letters_found = False
    for root, dirs, files in os.walk('.'):
        if 'letters' in dirs or any('letters' in d for d in dirs):
            letters_found = True
            break
    
    if not letters_found:
        print("WARNING: 'letters' folder not found!")
        print(f"Current directory: {os.getcwd()}")
        print("Please create a 'letters' folder with letter sprite images.")
    else:
        print(f"Letters folder found")
    
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?.-:,'/() "
    
    # First try to load at least one letter to get dimensions
    first_loaded = False
    loaded_sprites = 0
    
    for char in characters:
        # Try loading individual letter files
        if char == ' ':
            filename = 'space.png'
        elif char == '!':
            filename = 'exclamation.png'
        elif char == '?':
            filename = 'question.png'
        elif char == '.':
            filename = 'period.png'
        elif char == '-':
            filename = 'dash.png'
        elif char == ':':
            filename = 'colon.png'
        elif char == ',':
            filename = 'comma.png'
        elif char == "'":
            filename = 'apostrophe.png'
        elif char == '/':
            filename = 'slash.png'
        elif char == '(':
            filename = 'lparen.png'
        elif char == ')':
            filename = 'rparen.png'
        else:
            filename = f'{char}.png'
        
        # Search for file in any subfolder
        filepath = None
        for root, dirs, files in os.walk('.'):
            if filename in files:
                filepath = os.path.join(root, filename)
                break
        
        if filepath:
            try:
                sprite = pygame.image.load(filepath).convert_alpha()
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
        else:
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
        print("⚠ WARNING: No letter sprites found!")
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
bullet_filepath = find_file("bullet.png")
if bullet_filepath:
    try:
        bullet_img = pygame.image.load(bullet_filepath).convert_alpha()
        bullet_img = pygame.transform.scale(bullet_img, (12, 12))
    except:
        # Create fallback bullet
        bullet_img = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(bullet_img, RED, (6, 6), 5)
else:
    # Create fallback bullet
    bullet_img = pygame.Surface((12, 12), pygame.SRCALPHA)
    pygame.draw.circle(bullet_img, RED, (6, 6), 5)

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
        filepath = find_file(f"{bg_name}_{frame_num}.png")
        if filepath:
            try:
                frame = pygame.image.load(filepath).convert()
                frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))
                background_frames.append(frame)
                frame_num += 1
            except:
                break
        else:
            break
    
    if not background_frames:
        filepath = find_file(f"{bg_name}.png")
        if filepath:
            try:
                bg = pygame.image.load(filepath).convert()
                bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
                background_frames = [bg]
            except:
                bg = pygame.Surface((WIDTH, HEIGHT))
                bg.fill(BLACK)
                background_frames = [bg]
        else:
            bg = pygame.Surface((WIDTH, HEIGHT))
            bg.fill(BLACK)
            background_frames = [bg]
    
    # Load enemy sprite for this enemy
    enemy_frames = []
    frame_num = 0
    while True:
        filepath = find_file(f"enemy{enemy_id}_{frame_num}.png")
        if filepath:
            try:
                frame = pygame.image.load(filepath).convert_alpha()
                original_width, original_height = frame.get_size()
                scale_factor = min(600 / original_width, 600 / original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                frame = pygame.transform.scale(frame, (new_width, new_height))
                enemy_frames.append(frame)
                frame_num += 1
            except:
                break
        else:
            break
    
    if not enemy_frames:
        filepath = find_file(f"enemy{enemy_id}.png")
        if filepath:
            try:
                enemy_img = pygame.image.load(filepath).convert_alpha()
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
        else:
            enemy_img = pygame.Surface((600, 600), pygame.SRCALPHA)
            pygame.draw.circle(enemy_img, RED, (300, 300), 250)
            enemy_frames = [enemy_img]
    
    # Load hard mode enemy sprite
    hard_enemy_frames = []
    frame_num = 0
    while True:
        filepath = find_file(f"hard_enemy{enemy_id}_{frame_num}.png")
        if filepath:
            try:
                frame = pygame.image.load(filepath).convert_alpha()
                original_width, original_height = frame.get_size()
                scale_factor = min(600 / original_width, 600 / original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                frame = pygame.transform.scale(frame, (new_width, new_height))
                hard_enemy_frames.append(frame)
                frame_num += 1
            except:
                break
        else:
            break
    
    if not hard_enemy_frames:
        filepath = find_file(f"hard_enemy{enemy_id}.png")
        if filepath:
            try:
                hard_enemy_img = pygame.image.load(filepath).convert_alpha()
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
        else:
            # Fallback - purple tint
            hard_enemy_frames = []
            for frame in enemy_frames:
                hard_frame = frame.copy()
                purple_overlay = pygame.Surface(hard_frame.get_size())
                purple_overlay.fill((128, 0, 128))
                hard_frame.blit(purple_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
                hard_enemy_frames.append(hard_frame)
    
    # Load bullet sprite for this enemy
    filepath = find_file(f"bullet{enemy_id}.png")
    if filepath:
        try:
            bullet_img = pygame.image.load(filepath).convert_alpha()
            bullet_img = pygame.transform.scale(bullet_img, (12, 12))
        except:
            # Use default bullet
            filepath = find_file("bullet.png")
            if filepath:
                bullet_img = pygame.image.load(filepath).convert_alpha()
                bullet_img = pygame.transform.scale(bullet_img, (12, 12))
    else:
        # Use default bullet
        filepath = find_file("bullet.png")
        if filepath:
            try:
                bullet_img = pygame.image.load(filepath).convert_alpha()
                bullet_img = pygame.transform.scale(bullet_img, (12, 12))
            except:
                pass
    
    # Load and play music for this enemy
    music_name = enemy_data["music"]
    music_loaded = False
    
    # Try multiple formats in order of preference: .ogg (best quality/performance), .mp3, .wav
    for ext in ['.ogg', '.mp3', '.wav']:
        filepath = find_file(music_name + ext)
        if filepath:
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                music_loaded = True
                break
            except:
                continue
    
    if not music_loaded:
        # Try without extension (in case it's already included)
        filepath = find_file(music_name)
        if filepath:
            try:
                pygame.mixer.music.load(filepath)
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
player_filepath = find_file("player.png")
if player_filepath:
    try:
        player_img = pygame.image.load(player_filepath).convert_alpha()
        player_img = pygame.transform.scale(player_img, (30, 30))
        player_imgs = [player_img]  # Keep as list for compatibility
    except:
        player_img = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(player_img, BLUE, (15, 15), 12)
        player_imgs = [player_img]
else:
    player_img = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(player_img, BLUE, (15, 15), 12)
    player_imgs = [player_img]

# Ally player sprites (single character)
ally_filepath = find_file("ally.png")
if ally_filepath:
    try:
        ally_img = pygame.image.load(ally_filepath).convert_alpha()
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
else:
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
            # Move in straight line - no homing
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
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
        
        # Remove bullets that go off-screen (except slashes and bouncing which handle their own lifetime)
        if bullet['type'] not in ['slash_attack', 'bouncing'] and bullet in bullets:
            margin = 100  # Allow bullets to go a bit off-screen before despawning
            if (bullet['x'] < -margin or bullet['x'] > WIDTH + margin or 
                bullet['y'] < -margin or bullet['y'] > HEIGHT + margin):
                bullets.remove(bullet)
        
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
        # Roaring Knight
        13: (1, 500),     # grid_slashes
        
        # Enemy 1 - Comedy and Tragedy
        14: (1, 350),     # theater_curtain
        15: (10, 45),     # spotlight_dance
        16: (70, 7),      # mask_spiral
        17: (1, 300),     # drama_waves (single burst)
        18: (100, 4),     # comedy_rain
        
        # Enemy 2 - Diego
        19: (5, 90),      # tumbleweed_roll
        20: (1, 350),     # cactus_burst (single burst)
        21: (1, 450),     # dust_devil
        22: (1, 400),     # high_noon
        23: (60, 10),     # lasso_spin
        
        # Enemy 3-8: Keep existing configs for now
        24: (1, 450),     # dance_routine
        25: (5, 100),     # bass_drop
        26: (80, 6),      # neon_pulse
        27: (8, 60),      # cd_throw
        28: (70, 8),      # synth_wave
        29: (1, 350),     # pipis_spread
        30: (12, 40),     # phone_attack
        31: (1, 450),     # deal_maker
        32: (10, 55),     # big_shot
        33: (60, 9),      # hyperlink_blocked
        34: (1, 400),     # shadow_crystal
        35: (1, 500),     # dark_fountain
        36: (8, 70),      # knights_lance
        37: (1, 350),     # roaring_blast
        38: (1, 500),     # bone_zone
        39: (5, 100),     # gaster_blaster
        40: (60, 10),     # blue_attack
        41: (70, 8),      # karma
        42: (1, 450),     # dunked_on
        43: (1, 350),     # rude_buster
        44: (7, 75),      # axe_throw
        45: (1, 400),     # ultimate_heal
        46: (8, 65),      # red_buster
        47: (50, 12),     # tail_whip
        48: (1, 550),     # void_convergence
        49: (1, 500),     # reality_break
        50: (90, 6),      # glitch_storm
        51: (1, 450),     # delete
        52: (75, 7),      # corruption
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
        # Only Grid Slashes from old patterns (used by Roaring Knight)
        if current_pattern == 13:
            spawn_grid_slashes()
            pattern_bullets_spawned += 1
        # Enemy 1 - Comedy and Tragedy
        elif current_pattern == 14:
            spawn_theater_curtain()
            pattern_bullets_spawned += 1
        elif current_pattern == 15:
            spawn_spotlight_dance()
            pattern_bullets_spawned += 1
        elif current_pattern == 16:
            spawn_mask_spiral()
            pattern_bullets_spawned += 1
        elif current_pattern == 17:
            spawn_drama_waves()
            pattern_bullets_spawned += 1
        elif current_pattern == 18:
            spawn_comedy_rain()
            pattern_bullets_spawned += 1
        # Enemy 2 - Diego
        elif current_pattern == 19:
            spawn_tumbleweed_roll()
            pattern_bullets_spawned += 1
        elif current_pattern == 20:
            spawn_cactus_burst()
            pattern_bullets_spawned += 1
        elif current_pattern == 21:
            spawn_dust_devil()
            pattern_bullets_spawned += 1
        elif current_pattern == 22:
            spawn_high_noon()
            pattern_bullets_spawned += 1
        elif current_pattern == 23:
            spawn_lasso_spin()
            pattern_bullets_spawned += 1
        # Enemy 3 - Cap'n Cakes
        elif current_pattern == 24:
            spawn_dance_routine()
            pattern_bullets_spawned += 1
        elif current_pattern == 25:
            spawn_bass_drop()
            pattern_bullets_spawned += 1
        elif current_pattern == 26:
            spawn_neon_pulse()
            pattern_bullets_spawned += 1
        elif current_pattern == 27:
            spawn_cd_throw()
            pattern_bullets_spawned += 1
        elif current_pattern == 28:
            spawn_synth_wave()
            pattern_bullets_spawned += 1
        # Enemy 4 - Spamton NEO
        elif current_pattern == 29:
            spawn_pipis_spread()
            pattern_bullets_spawned += 1
        elif current_pattern == 30:
            spawn_phone_attack()
            pattern_bullets_spawned += 1
        elif current_pattern == 31:
            spawn_deal_maker()
            pattern_bullets_spawned += 1
        elif current_pattern == 32:
            spawn_big_shot()
            pattern_bullets_spawned += 1
        elif current_pattern == 33:
            spawn_hyperlink_blocked()
            pattern_bullets_spawned += 1
        # Enemy 5 - Roaring Knight
        elif current_pattern == 34:
            spawn_shadow_crystal()
            pattern_bullets_spawned += 1
        elif current_pattern == 35:
            spawn_dark_fountain()
            pattern_bullets_spawned += 1
        elif current_pattern == 36:
            spawn_knights_lance()
            pattern_bullets_spawned += 1
        elif current_pattern == 37:
            spawn_roaring_blast()
            pattern_bullets_spawned += 1
        # Enemy 6 - Sans
        elif current_pattern == 38:
            spawn_bone_zone()
            pattern_bullets_spawned += 1
        elif current_pattern == 39:
            spawn_gaster_blaster()
            pattern_bullets_spawned += 1
        elif current_pattern == 40:
            spawn_blue_attack()
            pattern_bullets_spawned += 1
        elif current_pattern == 41:
            spawn_karma()
            pattern_bullets_spawned += 1
        elif current_pattern == 42:
            spawn_dunked_on()
            pattern_bullets_spawned += 1
        # Enemy 7 - Susie
        elif current_pattern == 43:
            spawn_rude_buster()
            pattern_bullets_spawned += 1
        elif current_pattern == 44:
            spawn_axe_throw()
            pattern_bullets_spawned += 1
        elif current_pattern == 45:
            spawn_ultimate_heal()
            pattern_bullets_spawned += 1
        elif current_pattern == 46:
            spawn_red_buster()
            pattern_bullets_spawned += 1
        elif current_pattern == 47:
            spawn_tail_whip()
            pattern_bullets_spawned += 1
        # Enemy 8 - ???
        elif current_pattern == 48:
            spawn_void_convergence()
            pattern_bullets_spawned += 1
        elif current_pattern == 49:
            spawn_reality_break()
            pattern_bullets_spawned += 1
        elif current_pattern == 50:
            spawn_glitch_storm()
            pattern_bullets_spawned += 1
        elif current_pattern == 51:
            spawn_delete()
            pattern_bullets_spawned += 1
        elif current_pattern == 52:
            spawn_corruption()
            pattern_bullets_spawned += 1
    
    return False  # Pattern not complete

def check_collisions():
    global player_health, invincible_timer, points
    keys = pygame.key.get_pressed()
    moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]
    
    # Check regular bullet collisions
    for bullet in bullets[:]:
        hit_detected = False
        
        if bullet['type'] == 'laser':
            rect = pygame.Rect(bullet['x'], bullet['y'], bullet['width'], bullet['height'])
            if abs(player_pos[0] - rect.centerx) < rect.width // 2 + player_radius and abs(player_pos[1] - rect.centery) < rect.height // 2 + player_radius:
                hit_detected = True
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
                    hit_detected = True
                    if invincible_timer <= 0:
                        damage = bullet.get('damage', 1)
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
        else:
            # Circle collision for all other bullet types
            collision_radius = bullet_img.get_width() // 2
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                hit_detected = True
                if invincible_timer <= 0:
                    damage = bullet.get('damage', 1)
                    player_health -= damage
                    invincible_timer = INVINCIBLE_DURATION
                    create_hit_particles(player_pos[0], player_pos[1])
        
        # Delete bullet on ANY hit, even during i-frames (except slashes and lasers)
        if hit_detected and bullet['type'] not in ['slash_attack', 'laser']:
            if bullet in bullets:
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
    global enemy_frame_counter, enemy_current_frame, enemy_animation_speed, enemy_x
    
    # Handle Sans dodge animation
    sans_offset = 0
    if current_enemy_id == 6 and hasattr(show_attack_phase, 'sans_dodge_triggered') and show_attack_phase.sans_dodge_triggered:
        # Dodge animation: slide right then back with easing
        show_attack_phase.sans_dodge_timer = getattr(show_attack_phase, 'sans_dodge_timer', 0) + 1
        
        dodge_duration = 40  # Total frames for dodge animation (increased for smoother motion)
        if show_attack_phase.sans_dodge_timer < dodge_duration:
            # Calculate progress (0.0 to 1.0)
            progress = show_attack_phase.sans_dodge_timer / dodge_duration
            
            # Apply easeInOutCubic easing
            # Slower at start/end (apex), faster in middle
            if progress < 0.5:
                # Ease out cubic for first half (moving right)
                t = progress * 2
                eased = 1 - pow(1 - t, 3)
                sans_offset = int(200 * eased)
            else:
                # Ease in cubic for second half (moving back)
                t = (progress - 0.5) * 2
                eased = pow(t, 3)
                sans_offset = int(200 * (1 - eased))
        else:
            # Animation complete
            show_attack_phase.sans_dodge_triggered = False
            show_attack_phase.sans_dodge_timer = 0
            sans_offset = 0
    
    # Choose which frames to use based on hard mode
    frames_to_use = hard_enemy_frames if hard_mode_active else enemy_frames
    
    # Update animation frame
    enemy_frame_counter += 1
    if enemy_frame_counter >= enemy_animation_speed:
        enemy_frame_counter = 0
        enemy_current_frame = (enemy_current_frame + 1) % len(frames_to_use)
    
    # Draw current frame (with Sans offset if dodging)
    screen.blit(frames_to_use[enemy_current_frame], (enemy_x + sans_offset, enemy_y))

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

### ENEMY 1 - COMEDY AND TRAGEDY ###
def spawn_theater_curtain():
    """Closing curtains from sides"""
    difficulty = apply_difficulty_scaling()
    speed = 3 * difficulty
    
    # Horizontal beams from left and right
    for i in range(5):
        y = box_y + i * (box_size // 5)
        bullets.append({
            'x': box_x,
            'y': y,
            'vx': speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 0
        })
        bullets.append({
            'x': box_x + box_size,
            'y': y,
            'vx': -speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 0
        })

def spawn_spotlight_dance():
    """Spotlights that sweep across"""
    difficulty = apply_difficulty_scaling()
    speed = 3.5 * difficulty
    
    # Vertical sweep
    for x in range(box_x, box_x + box_size, 55):
        bullets.append({
            'x': x,
            'y': box_y,
            'vx': 0,
            'vy': speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_mask_spiral():
    """Comedy/tragedy mask spiral"""
    difficulty = apply_difficulty_scaling()
    global spiral_angle
    speed = 3 * difficulty
    
    vx = math.cos(spiral_angle) * speed
    vy = math.sin(spiral_angle) * speed
    bullets.append({
        'x': WIDTH // 2,
        'y': 150,
        'vx': vx,
        'vy': vy,
        'type': 'spiral',
        'rotation': 0,
        'rotation_speed': 5
    })
    spiral_angle += 0.22

def spawn_drama_waves():
    """Wave pattern"""
    difficulty = apply_difficulty_scaling()
    speed = 3.5 * difficulty
    
    for i in range(8):
        angle = (360 / 8) * i
        vx = math.cos(math.radians(angle)) * speed
        vy = math.sin(math.radians(angle)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_comedy_rain():
    """Rain from top"""
    difficulty = apply_difficulty_scaling()
    x = random.randint(box_x, box_x + box_size)
    speed = random.uniform(3, 5) * difficulty
    
    bullets.append({
        'x': x,
        'y': box_y,
        'vx': 0,
        'vy': speed,
        'type': 'radial',
        'rotation': 0,
        'rotation_speed': 5
    })

### ENEMY 2 - DIEGO ###
def spawn_tumbleweed_roll():
    """Rolling tumbleweeds"""
    difficulty = apply_difficulty_scaling()
    
    edge = random.choice(['left', 'right'])
    spawn_y = random.randint(box_y + 30, box_y + box_size - 30)
    
    if edge == 'left':
        spawn_x = box_x
        vx = random.uniform(3, 5) * difficulty
    else:
        spawn_x = box_x + box_size
        vx = -random.uniform(3, 5) * difficulty
    
    vy = random.uniform(-1.5, 1.5) * difficulty
    
    bullets.append({
        'x': spawn_x,
        'y': spawn_y,
        'vx': vx,
        'vy': vy,
        'type': 'bouncing',
        'rotation': 0,
        'rotation_speed': 10,
        'life_time': FPS * 6
    })

def spawn_cactus_burst():
    """Bursts from corners"""
    difficulty = apply_difficulty_scaling()
    speed = 3.5 * difficulty
    
    corners = [(box_x, box_y), (box_x + box_size, box_y)]
    corner = random.choice(corners)
    
    for i in range(8):
        angle = random.uniform(0, 2 * math.pi)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        bullets.append({
            'x': corner[0],
            'y': corner[1],
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_dust_devil():
    """Swirling dust"""
    difficulty = apply_difficulty_scaling()
    
    center_x = random.randint(box_x + 50, box_x + box_size - 50)
    center_y = random.randint(box_y + 50, box_y + box_size - 50)
    
    for i in range(18):
        angle = (360 / 18) * i
        radius = 30 + i * 5
        x = center_x + math.cos(math.radians(angle)) * radius
        y = center_y + math.sin(math.radians(angle)) * radius
        
        vx = math.cos(math.radians(angle + 90)) * 2.5 * difficulty
        vy = math.sin(math.radians(angle + 90)) * 2.5 * difficulty
        
        bullets.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_high_noon():
    """Sun rays from top"""
    difficulty = apply_difficulty_scaling()
    speed = 4 * difficulty
    
    for angle in range(0, 180, 18):
        vx = math.cos(math.radians(angle + 90)) * speed
        vy = math.sin(math.radians(angle + 90)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': box_y,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_lasso_spin():
    """Spinning lasso"""
    difficulty = apply_difficulty_scaling()
    global spiral_angle
    
    radius = 100
    x = WIDTH // 2 + math.cos(spiral_angle) * radius
    y = HEIGHT // 2 + math.sin(spiral_angle) * radius
    
    bullets.append({
        'x': x,
        'y': y,
        'vx': 0,
        'vy': 0,
        'type': 'radial',
        'rotation': 0,
        'rotation_speed': 10
    })
    spiral_angle += 0.32 * difficulty

### ENEMY 3 - SHRED MASTER ###
def spawn_dance_routine():
    """Corner bursts"""
    difficulty = apply_difficulty_scaling()
    speed = 5 * difficulty
    
    corners = [
        (box_x, box_y),
        (box_x + box_size, box_y),
        (box_x, box_y + box_size),
        (box_x + box_size, box_y + box_size)
    ]
    
    for corner_x, corner_y in corners:
        for i in range(6):
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            bullets.append({
                'x': corner_x,
                'y': corner_y,
                'vx': vx,
                'vy': vy,
                'type': 'radial',
                'rotation': 0,
                'rotation_speed': 5
            })

def spawn_bass_drop():
    """Heavy beat waves"""
    difficulty = apply_difficulty_scaling()
    speed = 6 * difficulty
    
    for i in range(12):
        angle = (360 / 12) * i
        vx = math.cos(math.radians(angle)) * speed
        vy = math.sin(math.radians(angle)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_neon_pulse():
    """Pulsing rings"""
    difficulty = apply_difficulty_scaling()
    global expanding_spiral_angle
    
    expanding_spiral_angle += 0.1 * difficulty
    bullets.append({
        'center_x': WIDTH // 2,
        'center_y': HEIGHT // 2,
        'angle': expanding_spiral_angle,
        'radius': 0,
        'type': 'expanding_spiral',
        'rotation': 0,
        'rotation_speed': 5
    })

def spawn_cd_throw():
    """Spinning discs"""
    difficulty = apply_difficulty_scaling()
    speed = 5 * difficulty
    
    side = random.choice(['left', 'right'])
    y = random.randint(box_y + 30, box_y + box_size - 30)
    
    if side == 'left':
        x = box_x
        vx = speed
    else:
        x = box_x + box_size
        vx = -speed
    
    bullets.append({
        'x': x,
        'y': y,
        'vx': vx,
        'vy': 0,
        'type': 'radial',
        'rotation': 0,
        'rotation_speed': 15
    })

def spawn_synth_wave():
    """Wavy pattern"""
    difficulty = apply_difficulty_scaling()
    global double_spiral_angle
    
    double_spiral_angle += 0.3 * difficulty
    for direction in (1, -1):
        bullets.append({
            'center_x': WIDTH // 2,
            'center_y': HEIGHT // 2,
            'angle': direction * double_spiral_angle,
            'radius': 0,
            'direction': direction,
            'type': 'double_spiral',
            'rotation': 0,
            'rotation_speed': 5 * direction
        })

### ENEMY 4 - SPAMTON NEO ###
def spawn_pipis_spread():
    """Egg bullets that explode"""
    difficulty = apply_difficulty_scaling()
    
    num_pipis = 8
    radius = 100
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    for i in range(num_pipis):
        angle = (2 * math.pi / num_pipis) * i
        spawn_x = center_x + math.cos(angle) * radius
        spawn_y = center_y + math.sin(angle) * radius
        
        bullets.append({
            'x': spawn_x,
            'y': spawn_y,
            'vx': 0,
            'vy': 0,
            'type': 'giant_explosive',
            'life_time': int(FPS * (2 / difficulty)),
            'size': 3,
            'speed': 4 * difficulty,
            'rotation': 0,
            'rotation_speed': 3,
            'exploded': False
        })

def spawn_phone_attack():
    """Phone-shaped bullets"""
    difficulty = apply_difficulty_scaling()
    speed = 5 * difficulty
    
    for i in range(6):
        angle = (360 / 6) * i
        vx = math.cos(math.radians(angle)) * speed
        vy = math.sin(math.radians(angle)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_deal_maker():
    """Deal patterns"""
    difficulty = apply_difficulty_scaling()
    speed = 4 * difficulty
    
    # Four corners deal
    for corner in [(box_x, box_y), (box_x + box_size, box_y), 
                   (box_x, box_y + box_size), (box_x + box_size, box_y + box_size)]:
        angle = math.atan2(HEIGHT // 2 - corner[1], WIDTH // 2 - corner[0])
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        bullets.append({
            'x': corner[0],
            'y': corner[1],
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_big_shot():
    """BIG SHOT!"""
    difficulty = apply_difficulty_scaling()
    speed = 6 * difficulty
    
    angle = math.atan2(player_pos[1] - HEIGHT // 2, player_pos[0] - WIDTH // 2)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    
    bullets.append({
        'x': WIDTH // 2,
        'y': HEIGHT // 2,
        'vx': vx,
        'vy': vy,
        'speed': speed,  # Add speed for targeted type
        'type': 'targeted',
        'rotation': 0,
        'rotation_speed': 5,
        'life_time': FPS * 5
    })

def spawn_hyperlink_blocked():
    """Blocked patterns"""
    difficulty = apply_difficulty_scaling()
    x = random.randint(box_x, box_x + box_size)
    speed = random.uniform(4, 7) * difficulty
    
    bullets.append({
        'x': x,
        'y': 0,
        'speed': speed,
        'type': 'rain',
        'rotation': 0,
        'rotation_speed': 5
    })

### ENEMY 5 - THE ROARING KNIGHT ###
def spawn_shadow_crystal():
    """Rotating crystal formation"""
    difficulty = apply_difficulty_scaling()
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    num_crystals = 12
    radius = 150
    
    for i in range(num_crystals):
        angle = (2 * math.pi / num_crystals) * i
        x = center_x + math.cos(angle) * radius
        y = center_y + math.sin(angle) * radius
        
        vx = math.cos(angle + math.pi/2) * 3 * difficulty
        vy = math.sin(angle + math.pi/2) * 3 * difficulty
        
        bullets.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_dark_fountain():
    """Dark fountain surge"""
    difficulty = apply_difficulty_scaling()
    
    for i in range(24):
        angle = (360 / 24) * i
        speed = random.uniform(3, 6) * difficulty
        vx = math.cos(math.radians(angle)) * speed
        vy = math.sin(math.radians(angle)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_knights_lance():
    """Lance thrusts"""
    difficulty = apply_difficulty_scaling()
    speed = 7 * difficulty
    
    side = random.choice(['left', 'right', 'top', 'bottom'])
    
    if side == 'left':
        bullets.append({
            'x': box_x,
            'y': random.randint(box_y, box_y + box_size),
            'vx': speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 0
        })
    elif side == 'right':
        bullets.append({
            'x': box_x + box_size,
            'y': random.randint(box_y, box_y + box_size),
            'vx': -speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 0
        })
    elif side == 'top':
        bullets.append({
            'x': random.randint(box_x, box_x + box_size),
            'y': box_y,
            'vx': 0,
            'vy': speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 0
        })
    else:
        bullets.append({
            'x': random.randint(box_x, box_x + box_size),
            'y': box_y + box_size,
            'vx': 0,
            'vy': -speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 0
        })

def spawn_roaring_blast():
    """Massive blast"""
    difficulty = apply_difficulty_scaling()
    speed = 5 * difficulty
    
    for i in range(16):
        angle = (360 / 16) * i
        vx = math.cos(math.radians(angle)) * speed
        vy = math.sin(math.radians(angle)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

### ENEMY 6 - SANS ###
def spawn_bone_zone():
    """Bone walls"""
    difficulty = apply_difficulty_scaling()
    
    gap_size = 80
    gap_position = random.randint(box_x + gap_size, box_x + box_size - gap_size)
    
    # Top bones
    for x in range(box_x, box_x + box_size, 20):
        if abs(x - gap_position) > gap_size // 2:
            bullets.append({
                'x': x,
                'y': box_y,
                'vx': 0,
                'vy': 6 * difficulty,
                'type': 'radial',
                'rotation': 0,
                'rotation_speed': 0,
                'life_time': FPS * 3
            })
    
    # Bottom bones
    for x in range(box_x, box_x + box_size, 20):
        if abs(x - gap_position) > gap_size // 2:
            bullets.append({
                'x': x,
                'y': box_y + box_size,
                'vx': 0,
                'vy': -6 * difficulty,
                'type': 'radial',
                'rotation': 0,
                'rotation_speed': 0,
                'life_time': FPS * 3
            })

def spawn_gaster_blaster():
    """Blaster beams"""
    difficulty = apply_difficulty_scaling()
    speed = 6 * difficulty
    
    angle = random.uniform(0, 2 * math.pi)
    for i in range(8):
        offset_angle = angle + (2 * math.pi / 8) * i
        vx = math.cos(offset_angle) * speed
        vy = math.sin(offset_angle) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_blue_attack():
    """Blue (stationary warning)"""
    difficulty = apply_difficulty_scaling()
    
    for i in range(10):
        x = random.randint(box_x + 20, box_x + box_size - 20)
        y = random.randint(box_y + 20, box_y + box_size - 20)
        bullets.append({
            'x': x,
            'y': y,
            'vx': 0,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'life_time': FPS * 4
        })

def spawn_karma():
    """Karma damage over time"""
    difficulty = apply_difficulty_scaling()
    global spiral_angle
    
    speed = 4 * difficulty
    vx = math.cos(spiral_angle) * speed
    vy = math.sin(spiral_angle) * speed
    bullets.append({
        'x': WIDTH // 2,
        'y': 150,
        'vx': vx,
        'vy': vy,
        'type': 'spiral',
        'rotation': 0,
        'rotation_speed': 5
    })
    spiral_angle += 0.15 * difficulty

def spawn_dunked_on():
    """Get dunked on"""
    difficulty = apply_difficulty_scaling()
    
    # Rain from above
    for i in range(20):
        x = box_x + (box_size / 20) * i
        bullets.append({
            'x': x,
            'y': box_y,
            'vx': 0,
            'vy': 7 * difficulty,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

### ENEMY 7 - SUSIE ###
def spawn_rude_buster():
    """Massive beams"""
    difficulty = apply_difficulty_scaling()
    speed = 7 * difficulty
    
    side = random.choice(['left', 'right'])
    y = random.randint(box_y + 50, box_y + box_size - 50)
    
    if side == 'left':
        for offset in range(-20, 21, 10):
            bullets.append({
                'x': box_x,
                'y': y + offset,
                'vx': speed,
                'vy': 0,
                'type': 'radial',
                'rotation': 0,
                'rotation_speed': 0,
                'size': 2
            })
    else:
        for offset in range(-20, 21, 10):
            bullets.append({
                'x': box_x + box_size,
                'y': y + offset,
                'vx': -speed,
                'vy': 0,
                'type': 'radial',
                'rotation': 0,
                'rotation_speed': 0,
                'size': 2
            })

def spawn_axe_throw():
    """Spinning axes"""
    difficulty = apply_difficulty_scaling()
    speed = 6 * difficulty
    
    angle = random.uniform(0, 2 * math.pi)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    
    bullets.append({
        'x': WIDTH // 2,
        'y': HEIGHT // 2,
        'vx': vx,
        'vy': vy,
        'type': 'radial',
        'rotation': 0,
        'rotation_speed': 20
    })

def spawn_ultimate_heal():
    """AOE burst"""
    difficulty = apply_difficulty_scaling()
    speed = 5 * difficulty
    
    for i in range(20):
        angle = (360 / 20) * i
        vx = math.cos(math.radians(angle)) * speed
        vy = math.sin(math.radians(angle)) * speed
        bullets.append({
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_red_buster():
    """Red beam"""
    difficulty = apply_difficulty_scaling()
    speed = 6 * difficulty
    
    angle = math.atan2(player_pos[1] - HEIGHT // 2, player_pos[0] - WIDTH // 2)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    
    bullets.append({
        'x': WIDTH // 2,
        'y': HEIGHT // 2,
        'vx': vx,
        'vy': vy,
        'speed': speed,  # Add speed for targeted type
        'type': 'targeted',
        'rotation': 0,
        'rotation_speed': 5,
        'life_time': FPS * 5
    })

def spawn_tail_whip():
    """Sweeping tail"""
    difficulty = apply_difficulty_scaling()
    
    for i in range(10):
        bullets.append({
            'x': box_x + i * (box_size // 10),
            'y': box_y if i % 2 == 0 else box_y + box_size,
            'vx': 0,
            'vy': (5 if i % 2 == 0 else -5) * difficulty,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

### ENEMY 8 - ??? ###
def spawn_void_convergence():
    """All edges converge"""
    difficulty = apply_difficulty_scaling()
    speed = 4 * difficulty
    spacing = 20
    
    # All edges toward center
    for x in range(box_x, box_x + box_size, spacing):
        bullets.append({
            'x': x,
            'y': box_y,
            'vx': 0,
            'vy': speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })
        bullets.append({
            'x': x,
            'y': box_y + box_size,
            'vx': 0,
            'vy': -speed,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })
    
    for y in range(box_y, box_y + box_size, spacing):
        bullets.append({
            'x': box_x,
            'y': y,
            'vx': speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })
        bullets.append({
            'x': box_x + box_size,
            'y': y,
            'vx': -speed,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5
        })

def spawn_reality_break():
    """Reality tears"""
    difficulty = apply_difficulty_scaling()
    
    for i in range(16):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 7) * difficulty
        x = random.randint(box_x, box_x + box_size)
        y = random.randint(box_y, box_y + box_size)
        
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        
        bullets.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 10
        })

def spawn_glitch_storm():
    """Chaotic glitch"""
    difficulty = apply_difficulty_scaling()
    
    x = random.randint(box_x, box_x + box_size)
    y = random.randint(box_y, box_y + box_size)
    speed = random.uniform(3, 8) * difficulty
    angle = random.uniform(0, 2 * math.pi)
    
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    
    bullets.append({
        'x': x,
        'y': y,
        'vx': vx,
        'vy': vy,
        'type': 'radial',
        'rotation': 0,
        'rotation_speed': random.randint(-15, 15)
    })

def spawn_delete():
    """Delete sequence"""
    difficulty = apply_difficulty_scaling()
    
    # X pattern
    for i in range(10):
        progress = i / 10
        
        # Top-left to bottom-right
        x1 = box_x + progress * box_size
        y1 = box_y + progress * box_size
        bullets.append({
            'x': x1,
            'y': y1,
            'vx': 0,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'life_time': FPS * 2
        })
        
        # Top-right to bottom-left
        x2 = box_x + box_size - progress * box_size
        y2 = box_y + progress * box_size
        bullets.append({
            'x': x2,
            'y': y2,
            'vx': 0,
            'vy': 0,
            'type': 'radial',
            'rotation': 0,
            'rotation_speed': 5,
            'life_time': FPS * 2
        })

def spawn_corruption():
    """Corrupted patterns"""
    difficulty = apply_difficulty_scaling()
    global spiral_angle
    
    speed = random.uniform(3, 6) * difficulty
    vx = math.cos(spiral_angle) * speed
    vy = math.sin(spiral_angle) * speed
    
    bullets.append({
        'x': WIDTH // 2,
        'y': 150,
        'vx': vx,
        'vy': vy,
        'type': 'spiral',
        'rotation': 0,
        'rotation_speed': random.randint(-10, 10)
    })
    spiral_angle += random.uniform(0.1, 0.3) * difficulty

def show_attack_phase():
    """Enemy 1 - Comedy and Tragedy: Curtains close from both sides"""
    difficulty = apply_difficulty_scaling()
    
    # Curtains from left and right
    curtain_speed = 3 * difficulty
    curtain_height = box_size // 10
    
    for i in range(10):
        y_pos = box_y + i * (box_size // 10)
        
        # Left curtain
        bullets.append({
            'x': box_x,
            'y': y_pos,
            'type': 'laser',
            'width': 0,  # Will grow
            'height': curtain_height,
            'speed': curtain_speed,
            'color': 'blue',
            'growing': True,
            'max_width': box_size // 2 - 50
        })
        
        # Right curtain
        bullets.append({
            'x': box_x + box_size,
            'y': y_pos,
            'type': 'laser',
            'width': 0,  # Will grow
            'height': curtain_height,
            'speed': -curtain_speed,
            'color': 'blue',
            'growing': True,
            'max_width': box_size // 2 - 50
        })

def spawn_tumbleweed_roll():
    """Enemy 2 - Diego: Rolling tumbleweeds that bounce"""
    difficulty = apply_difficulty_scaling()
    
    for i in range(3):
        # Spawn from random edge
        edge = random.choice(['left', 'right'])
        spawn_y = random.randint(box_y + 30, box_y + box_size - 30)
        
        if edge == 'left':
            spawn_x = box_x
            vx = random.uniform(4, 7) * difficulty
        else:
            spawn_x = box_x + box_size
            vx = -random.uniform(4, 7) * difficulty
        
        vy = random.uniform(-2, 2) * difficulty
        
        bullets.append({
            'x': spawn_x,
            'y': spawn_y,
            'vx': vx,
            'vy': vy,
            'type': 'bouncing',
            'rotation': 0,
            'rotation_speed': 10,
            'life_time': FPS * 6,
            'size': 2  # Bigger bullets
        })

def spawn_dance_routine():
    """Enemy 3 - Cap'n Cakes: Alternating corner bursts in rhythm"""
    difficulty = apply_difficulty_scaling()
    speed = 5 * difficulty
    
    corners = [
        (box_x, box_y),
        (box_x + box_size, box_y),
        (box_x, box_y + box_size),
        (box_x + box_size, box_y + box_size)
    ]
    
    # Burst from each corner
    for corner_x, corner_y in corners:
        for angle_offset in range(0, 90, 15):
            # Calculate angle toward center from corner
            if corner_x == box_x and corner_y == box_y:
                base_angle = 45
            elif corner_x == box_x + box_size and corner_y == box_y:
                base_angle = 135
            elif corner_x == box_x and corner_y == box_y + box_size:
                base_angle = 315
            else:
                base_angle = 225
            
            angle = math.radians(base_angle + angle_offset - 45)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            bullets.append({
                'x': corner_x,
                'y': corner_y,
                'vx': vx,
                'vy': vy,
                'type': 'radial',
                'rotation': 0,
                'rotation_speed': 5
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
                    
                    # Check if Sans should dodge BEFORE calculating damage
                    sans_will_dodge = False
                    if current_enemy_id == 6:
                        # Calculate damage to check if it would kill
                        distance_from_target = abs(qte_position - qte_target_position)
                        char_damage_mult = get_character_damage_multiplier()
                        
                        if distance_from_target <= qte_perfect_range:
                            temp_damage = int(20 * char_damage_mult)
                        elif distance_from_target <= qte_good_range:
                            temp_damage = int(15 * char_damage_mult)
                        else:
                            max_distance = qte_bar_length // 2
                            temp_damage = max(1, int(10 * (1 - distance_from_target / max_distance) * char_damage_mult))
                        
                        # Check if this would kill Sans
                        if enemy_health - temp_damage <= 0:
                            # Check dodge count
                            if not hasattr(show_attack_phase, 'sans_dodge_count'):
                                show_attack_phase.sans_dodge_count = 0
                            
                            if show_attack_phase.sans_dodge_count < 10:
                                sans_will_dodge = True
                                show_attack_phase.sans_dodge_count += 1
                                # Start dodge animation immediately
                                show_attack_phase.sans_dodge_triggered = True
                                show_attack_phase.sans_dodge_timer = 0
                    
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
                    
                    # Override display if Sans dodged
                    if sans_will_dodge:
                        hit_quality = "DODGE!"
                        hit_color = (100, 200, 255)
                        damage_dealt = 0  # No damage dealt when dodging
                    
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

def hub_room():
    """Hub room where player walks around and interacts with enemy statues"""
    global current_enemy_id, defeated_enemies
    
    # Hub room settings
    hub_player_x = WIDTH // 2
    hub_player_y = HEIGHT // 2
    hub_player_speed = 4
    
    # Statue positions - arranged in a circle with more spread
    statue_radius = 400  # Increased from 250
    statues = []
    num_enemies = 8
    
    for i in range(num_enemies):
        angle = (2 * math.pi / num_enemies) * i - math.pi / 2  # Start from top
        x = WIDTH // 2 + math.cos(angle) * statue_radius
        y = HEIGHT // 2 + math.sin(angle) * statue_radius
        
        enemy_id = i + 1
        
        # Add all statues except secret if not unlocked
        if enemy_id == 8 and len(defeated_enemies) < 7:
            continue
        
        statues.append({
            'id': enemy_id,
            'x': x,
            'y': y,
            'name': ENEMIES[enemy_id]["name"],
            'defeated': enemy_id in defeated_enemies
        })
    
    # Load or create hub room background
    hub_bg_path = find_file("hub_room.png")
    if hub_bg_path:
        try:
            hub_bg = pygame.image.load(hub_bg_path).convert()
            hub_bg = pygame.transform.scale(hub_bg, (WIDTH, HEIGHT))
        except:
            hub_bg = pygame.Surface((WIDTH, HEIGHT))
            hub_bg.fill((20, 20, 30))  # Dark background placeholder
    else:
        hub_bg = pygame.Surface((WIDTH, HEIGHT))
        hub_bg.fill((20, 20, 30))  # Dark background placeholder
    
    # Load or create player sprite for hub
    hub_player_path = find_file("hub_player.png")
    if hub_player_path:
        try:
            hub_player_img = pygame.image.load(hub_player_path).convert_alpha()
            hub_player_img = pygame.transform.scale(hub_player_img, (30, 30))
        except:
            hub_player_img = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(hub_player_img, BLUE, (15, 15), 12)  # Placeholder
    else:
        hub_player_img = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(hub_player_img, BLUE, (15, 15), 12)  # Placeholder
    
    # Load or create statue sprites
    statue_path = find_file("statue.png")
    if statue_path:
        try:
            statue_img = pygame.image.load(statue_path).convert_alpha()
            statue_img = pygame.transform.scale(statue_img, (60, 80))
        except:
            statue_img = pygame.Surface((60, 80), pygame.SRCALPHA)
            pygame.draw.rect(statue_img, (100, 100, 100), (10, 20, 40, 60))  # Placeholder
            pygame.draw.circle(statue_img, (80, 80, 80), (30, 15), 15)
    else:
        statue_img = pygame.Surface((60, 80), pygame.SRCALPHA)
        pygame.draw.rect(statue_img, (100, 100, 100), (10, 20, 40, 60))  # Placeholder
        pygame.draw.circle(statue_img, (80, 80, 80), (30, 15), 15)
    
    defeated_statue_path = find_file("statue_defeated.png")
    if defeated_statue_path:
        try:
            defeated_statue_img = pygame.image.load(defeated_statue_path).convert_alpha()
            defeated_statue_img = pygame.transform.scale(defeated_statue_img, (60, 80))
        except:
            defeated_statue_img = pygame.Surface((60, 80), pygame.SRCALPHA)
            pygame.draw.rect(defeated_statue_img, (50, 150, 50), (10, 20, 40, 60))  # Green tint
            pygame.draw.circle(defeated_statue_img, (40, 120, 40), (30, 15), 15)
    else:
        defeated_statue_img = pygame.Surface((60, 80), pygame.SRCALPHA)
        pygame.draw.rect(defeated_statue_img, (50, 150, 50), (10, 20, 40, 60))  # Green tint
        pygame.draw.circle(defeated_statue_img, (40, 120, 40), (30, 15), 15)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    # Check if near any statue
                    for statue in statues:
                        dist = math.hypot(hub_player_x - statue['x'], hub_player_y - statue['y'])
                        if dist < 80:  # Interaction range increased from 60
                            current_enemy_id = statue['id']
                            return  # Exit hub room and start fight immediately
                elif event.key == pygame.K_u:
                    # Debug unlock
                    defeated_enemies = {1, 2, 3, 4, 5, 6, 7}
                    save_game()
                    # Refresh by recursing (will rebuild statue list)
                    return hub_room()
                elif event.key == pygame.K_p:
                    # Reset save data
                    defeated_enemies = set()
                    save_game()
                    # Refresh by recursing (will rebuild statue list)
                    return hub_room()
        
        # Handle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            hub_player_y = max(60, hub_player_y - hub_player_speed)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            hub_player_y = min(HEIGHT - 60, hub_player_y + hub_player_speed)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            hub_player_x = max(60, hub_player_x - hub_player_speed)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            hub_player_x = min(WIDTH - 60, hub_player_x + hub_player_speed)
        
        # Draw everything
        screen.blit(hub_bg, (0, 0))
        
        # Draw statues
        for statue in statues:
            # Choose sprite based on defeated status
            current_statue_img = defeated_statue_img if statue['defeated'] else statue_img
            statue_rect = current_statue_img.get_rect(center=(int(statue['x']), int(statue['y'])))
            screen.blit(current_statue_img, statue_rect)
            
            # Draw statue name
            name_text = render_text(statue['name'], WHITE if not statue['defeated'] else GREEN, 0.5)
            name_rect = name_text.get_rect(center=(int(statue['x']), int(statue['y']) + 50))
            screen.blit(name_text, name_rect)
            
            # Show [DEFEATED] tag
            if statue['defeated']:
                defeated_text = render_text("[DEFEATED]", GREEN, 0.4)
                defeated_rect = defeated_text.get_rect(center=(int(statue['x']), int(statue['y']) + 65))
                screen.blit(defeated_text, defeated_rect)
        
        # Draw player
        player_rect = hub_player_img.get_rect(center=(int(hub_player_x), int(hub_player_y)))
        screen.blit(hub_player_img, player_rect)
        
        # Check if near any statue and show prompt
        near_statue = None
        for statue in statues:
            dist = math.hypot(hub_player_x - statue['x'], hub_player_y - statue['y'])
            if dist < 80:
                near_statue = statue
                break
        
        if near_statue:
            action_text = "REMATCH" if near_statue['defeated'] else "FIGHT"
            prompt = render_text(f"PRESS E TO {action_text}", YELLOW, 0.7)
            prompt_rect = prompt.get_rect(center=(WIDTH // 2, HEIGHT - 80))
            screen.blit(prompt, prompt_rect)
        
        # Draw title
        title = render_text("SELECT YOUR OPPONENT", WHITE, 1.2)
        title_rect = title.get_rect(center=(WIDTH // 2, 40))
        screen.blit(title, title_rect)
        
        # Draw controls
        controls = render_text("WASD/ARROWS: MOVE - E: INTERACT - U: UNLOCK ALL - P: RESET SAVE", WHITE, 0.5)
        controls_rect = controls.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        screen.blit(controls, controls_rect)
        
        pygame.display.flip()
        clock.tick(FPS)

def enemy_selection_screen():
    """Redirect to hub room - statue interaction sets current_enemy_id and returns"""
    hub_room()

def start_screen():
    """Simple title screen - press any key to start"""
    global defeated_enemies
    
    # Try to load save file
    load_game()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                waiting = False
        
        screen.fill(BLACK)
        
        # Title
        title = render_text("BUR", WHITE, 3.0)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(title, title_rect)
        
        # Prompt
        prompt = render_text("PRESS ANY KEY TO START", WHITE, 0.8)
        prompt_rect = prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(prompt, prompt_rect)
        
        pygame.display.flip()
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
    
    # Clear all bullets from previous fight
    bullets.clear()
    
    # Reset Sans dodge mechanics
    if hasattr(show_attack_phase, 'sans_dodge_count'):
        show_attack_phase.sans_dodge_count = 0
    if hasattr(show_attack_phase, 'sans_dodge_triggered'):
        show_attack_phase.sans_dodge_triggered = False
    if hasattr(show_attack_phase, 'sans_dodge_timer'):
        show_attack_phase.sans_dodge_timer = 0
    
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
            # Fade out music
            pygame.mixer.music.fadeout(1000)  # 1 second fadeout
            
            # Clear all bullets
            bullets.clear()
            
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
            # Fade out music
            pygame.mixer.music.fadeout(1500)  # 1.5 second fadeout
            
            # Clear all bullets
            bullets.clear()
            
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
