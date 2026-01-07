import pygame
import random
import math

pygame.init()

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

# Character selection and stats
selected_character = 0  # 0, 1, or 2
character_stats = {
    0: {"name": "bur", "max_health": 8, "money_multiplier": 1.0},
    1: {"name": "also bur", "max_health": 6, "money_multiplier": 1.5},
    2: {"name": "definitely not bur", "max_health": 10, "money_multiplier": 0.7}
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
points = 0
shop_active = False
max_health_upgrades = 0  # Track number of max health upgrades purchased
speed_upgrades = 0  # Track number of speed upgrades purchased

font = pygame.font.SysFont(None, 36)
shop_font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 24)

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

# Load sprites
bullet_img = pygame.image.load("bullet.png").convert_alpha()
bullet_img = pygame.transform.scale(bullet_img, (12, 12))  # Multiplied by 1.5 from 8x8

# Load background sprite
try:
    background_img = pygame.image.load("background.png").convert()
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
except:
    # Fallback to black background if no sprite available
    background_img = pygame.Surface((WIDTH, HEIGHT))
    background_img.fill(BLACK)

# Character sprites - you'll need to provide these
try:
    player_imgs = [
        pygame.image.load("player1.png").convert_alpha(),
        pygame.image.load("player2.png").convert_alpha(), 
        pygame.image.load("player3.png").convert_alpha()
    ]
    # Scale all character sprites
    for i in range(len(player_imgs)):
        player_imgs[i] = pygame.transform.scale(player_imgs[i], (30, 30))  # Multiplied by 1.5 from 20x20
except:
    # Fallback if custom sprites aren't available
    player_imgs = [
        pygame.image.load("player.png").convert_alpha(),
        pygame.image.load("player.png").convert_alpha(),
        pygame.image.load("player.png").convert_alpha()
    ]
    for i in range(len(player_imgs)):
        player_imgs[i] = pygame.transform.scale(player_imgs[i], (30, 30))  # Multiplied by 1.5 from 20x20

# Enemy sprite
try:
    enemy_img = pygame.image.load("enemy.png").convert_alpha()
    # Enemy is bigger than the box (450px), let's make it 600px
    enemy_img = pygame.transform.scale(enemy_img, (600, 600))
except:
    # Fallback if custom sprite isn't available - create a simple red circle
    enemy_img = pygame.Surface((600, 600), pygame.SRCALPHA)
    pygame.draw.circle(enemy_img, RED, (300, 300), 250)

# Enemy position (right side of screen)
enemy_x = WIDTH - 650  # Positioned on the right side
enemy_y = HEIGHT // 2 - 250  # Centered vertically

# Ally player sprites (3 different ones based on character selection)
try:
    ally_imgs = [
        pygame.image.load("ally1.png").convert_alpha(),
        pygame.image.load("ally2.png").convert_alpha(),
        pygame.image.load("ally3.png").convert_alpha()
    ]
    # Scale all ally sprites to match enemy size
    for i in range(len(ally_imgs)):
        ally_imgs[i] = pygame.transform.scale(ally_imgs[i], (600, 600))
except:
    # Fallback if custom sprites aren't available - create simple colored circles
    ally_imgs = []
    colors = [BLUE, GREEN, YELLOW]  # Different colors for each character
    for color in colors:
        ally_img = pygame.Surface((600, 600), pygame.SRCALPHA)
        pygame.draw.circle(ally_img, color, (300, 300), 250)
        ally_imgs.append(ally_img)

# Ally position (left side of screen, mirrored from enemy)
ally_x = 50  # Positioned on the left side (same distance as enemy: 650 from right = 50 from left)
ally_y = HEIGHT // 2 - 250  # Centered vertically (same as enemy)

def initialize_character_stats():
    """Initialize player stats based on selected character"""
    global max_health, player_health
    stats = character_stats[selected_character]
    max_health = stats["max_health"]
    player_health = max_health

def get_money_multiplier():
    """Get the money multiplier for the selected character"""
    return character_stats[selected_character]["money_multiplier"]

def get_damage_multiplier():
    """Calculate damage multiplier based on current cycle count"""
    # Every 5 cycles, damage doubles: 1-5=1x, 6-10=2x, 11-15=4x, etc.
    tier = (cycle_count - 1) // 5  # 0-indexed tier (0, 1, 2, 3, ...)
    return 2 ** tier

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
        elif bullet['type'] == 'wave':
            bullet['x'] += bullet['vx']
            bullet['y'] = bullet['base_y'] + math.sin(bullet['wave_phase']) * bullet['wave_amplitude']
            bullet['wave_phase'] += bullet['wave_speed']
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
            if bullet['state'] == 'warning':
                bullet['warning_time'] -= 1
                if bullet['warning_time'] <= 0:
                    bullet['state'] = 'active'
            elif bullet['state'] == 'active':
                bullet['active_time'] -= 1
                if bullet['active_time'] <= 0:
                    bullets.remove(bullet)
                    continue
        
        # Remove bullets that have moved off screen (except for targeted bullets and slash attacks which have their own life_time)
        if bullet['type'] not in ['targeted', 'giant_explosive', 'slash_attack']:
            if (bullet['x'] < -50 or bullet['x'] > WIDTH + 50 or 
                bullet['y'] < -50 or bullet['y'] > HEIGHT + 50):
                if bullet in bullets:  # Safety check
                    bullets.remove(bullet)

def spawn_spiral():
    global spiral_angle
    center_x, center_y = WIDTH // 2, 150
    speed = 4
    vx = math.cos(spiral_angle) * speed
    vy = math.sin(spiral_angle) * speed
    bullet = {
        'x': center_x, 'y': center_y, 'vx': vx, 'vy': vy, 'type': 'spiral',
        'rotation': 0, 'rotation_speed': 5
    }
    bullets.append(bullet)
    spiral_angle += 0.15

def spawn_wave():
    speed = 4
    amplitude = 45  # Scaled by 0.75 from 60
    wave_speed = 0.1
    bullets_per_wave = 7
    spacing = 30  # Scaled by 0.75 from 40

    start_y = random.randint(200, HEIGHT - 200 - spacing * (bullets_per_wave - 1))
    for i in range(bullets_per_wave):
        base_y = start_y + i * spacing
        bullet = {
            'x': 0,
            'base_y': base_y,
            'wave_phase': i * 0.5,
            'wave_amplitude': amplitude,
            'wave_speed': wave_speed,
            'vx': speed,
            'type': 'wave',
            'y': base_y,
            'rotation': 0,
            'rotation_speed': 5
        }
        bullets.append(bullet)

def spawn_targeted():
    spawn_x = random.randint(50, WIDTH - 50)
    spawn_y = 0
    speed = 3.5
    life_time = FPS * 5
    bullet = {
        'x': spawn_x, 'y': spawn_y, 'speed': speed, 'type': 'targeted', 
        'life_time': life_time, 'rotation': 0, 'rotation_speed': 5
    }
    bullets.append(bullet)

def spawn_radial_burst():
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    bullet_count = 24
    speed = 5
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
    expanding_spiral_angle += 0.1
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
    double_spiral_angle += 0.3

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
    speed = random.uniform(5, 8)
    
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
    # Spawn 5 giant bullets that fall from above and explode into radial bursts
    giant_bullet_count = 5  # Increased from 4
    
    for i in range(giant_bullet_count):
        # Random x position across the top of the screen
        spawn_x = random.randint(80, WIDTH - 80)  # Closer to edges
        spawn_y = -50  # Start above screen
        
        # Shorter, more urgent detonation time
        detonate_time = random.randint(int(FPS * 1.0), int(FPS * 2.5))
        
        bullet = {
            'x': spawn_x,
            'y': spawn_y,
            'vx': 0,  # No horizontal movement
            'vy': 3,  # Faster fall speed
            'speed': 3,
            'type': 'giant_explosive',
            'life_time': detonate_time,
            'size': 5,  # 5x normal size
            'rotation': 0,
            'rotation_speed': random.uniform(2, 5),  # Keep slow rotation
            'exploded': False
        }
        bullets.append(bullet)

def spawn_laser_beams():
    beam_width = WIDTH
    beam_height = 10
    speed = 8
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
    speed = 6
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
        1: (50, 10),      # wave: 50 waves (350 bullets total)
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
    }
    return configs.get(pattern_id, (100, 10))

def randomize_cycle_patterns():
    """Create a randomized selection of 8 patterns for the current cycle"""
    global current_cycle_patterns, current_pattern_index
    all_patterns = list(range(13))  # All pattern IDs 0-12
    random.shuffle(all_patterns)
    current_cycle_patterns = all_patterns[:8]  # Select 8 random patterns
    current_pattern_index = 0

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
        
        # Award points for completing a pattern (with character multiplier)
        points += int(10 * get_money_multiplier())
        
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
            spawn_wave()
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
    
    return False  # Pattern not complete

def check_collisions():
    global player_health, invincible_timer, points
    keys = pygame.key.get_pressed()
    moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]
    
    # Get current damage multiplier
    damage_multiplier = get_damage_multiplier()
    
    # Check regular bullet collisions
    for bullet in bullets[:]:
        if bullet['type'] == 'laser':
            rect = pygame.Rect(bullet['x'], bullet['y'], bullet['width'], bullet['height'])
            if abs(player_pos[0] - rect.centerx) < rect.width // 2 + player_radius and abs(player_pos[1] - rect.centery) < rect.height // 2 + player_radius:
                if invincible_timer <= 0:
                    if bullet.get('color') == 'blue' and moving:
                        damage = damage_multiplier
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
                    elif bullet.get('color') == 'orange' and not moving:
                        damage = damage_multiplier
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
                        damage = damage_multiplier
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
        elif bullet['type'] == 'zigzag_horizontal':
            # Handle horizontal zigzag collision - use scaled collision radius
            collision_radius = bullet_img.get_width() // 2  # This is now 6 pixels (12/2)
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                if invincible_timer <= 0:
                    damage = damage_multiplier
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
                    damage = damage_multiplier
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

def draw_enemy():
    """Draw the enemy sprite on the right side of the screen"""
    screen.blit(enemy_img, (enemy_x, enemy_y))

def draw_ally():
    """Draw the ally sprite on the left side of the screen - changes based on selected character"""
    ally_img = ally_imgs[selected_character]
    screen.blit(ally_img, (ally_x, ally_y))

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
    damage_multiplier = get_damage_multiplier()
    character_name = character_stats[selected_character]["name"]
    
    screen.blit(font.render(f"Health: {player_health}/{max_health}", True, WHITE), (10, 10))
    screen.blit(font.render(f"Points: {points}", True, WHITE), (10, 50))
    screen.blit(font.render(f"Speed: {player_speed:.1f}", True, WHITE), (10, 90))
    screen.blit(font.render(f"Cycle: {cycle_count}", True, WHITE), (10, 130))
    screen.blit(font.render(f"Damage: {damage_multiplier}x", True, (255, 100, 100)), (10, 170))
    screen.blit(small_font.render(f"Character: {character_name} ({get_money_multiplier():.1f}x money)", True, WHITE), (10, 210))

def show_shop():
    global player_health, max_health, points, shop_active, cycle_count, max_health_upgrades, speed_upgrades, player_speed
    shop_active = True
    selected_option = 0
    
    # Calculate escalating costs
    max_health_cost = 200 + (max_health_upgrades * 150)  # 200, 350, 500, 650, etc.
    speed_cost = 150 + (speed_upgrades * 100)  # 150, 250, 350, 450, etc.
    
    # Calculate full heal cost based on missing health (better rate than single heals for 3+ HP, worse for 1-2 HP)
    missing_health = max_health - player_health
    if missing_health <= 2:
        full_heal_cost = missing_health * 60  # More expensive per HP for small amounts (60 vs 50)
    else:
        full_heal_cost = missing_health * 40  # Better rate for bulk healing (40 vs 50)
    
    shop_options = [
        {"name": "Heal 1 HP", "cost": 50, "description": "Restore 1 health point"},
        {"name": "Max Health +1", "cost": max_health_cost, "description": f"Increase maximum health by 1 (#{max_health_upgrades + 1})"},
        {"name": "Speed +0.5", "cost": speed_cost, "description": f"Increase movement speed by 0.5 (#{speed_upgrades + 1})"},
        {"name": "Full Heal", "cost": full_heal_cost, "description": f"Restore {missing_health} health ({player_health}/{max_health} → {max_health}/{max_health})"},
        {"name": "Continue", "cost": 0, "description": "Continue to next cycle"}
    ]
    
    while shop_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w and selected_option > 0:
                    selected_option -= 1
                elif event.key == pygame.K_s and selected_option < len(shop_options) - 1:
                    selected_option += 1
                elif event.key == pygame.K_SPACE:
                    option = shop_options[selected_option]
                    if option["name"] == "Continue":
                        shop_active = False
                    elif points >= option["cost"]:
                        points -= option["cost"]
                        if option["name"] == "Heal 1 HP" and player_health < max_health:
                            player_health += 1
                        elif option["name"] == "Max Health +1":
                            max_health += 1
                            # Only heal if already at full health
                            if player_health == max_health - 1:  # Was at full health before the upgrade
                                player_health = max_health  # Stay at full health after upgrade
                            max_health_upgrades += 1  # Track the upgrade
                            # Recalculate cost for next upgrade and update the option
                            new_cost = 200 + (max_health_upgrades * 150)
                            shop_options[1]["cost"] = new_cost
                            shop_options[1]["description"] = f"Increase maximum health by 1 (#{max_health_upgrades + 1})"
                        elif option["name"] == "Speed +0.5":
                            speed_upgrades += 1
                            player_speed = base_player_speed + (speed_upgrades * 0.5)
                            # Recalculate cost for next upgrade and update the option
                            new_cost = 150 + (speed_upgrades * 100)
                            shop_options[2]["cost"] = new_cost
                            shop_options[2]["description"] = f"Increase movement speed by 0.5 (#{speed_upgrades + 1})"
                        elif option["name"] == "Full Heal":
                            player_health = max_health
                        
                        # Recalculate full heal cost after any purchase that might change health
                        missing_health = max_health - player_health
                        if missing_health <= 2:
                            full_heal_cost = missing_health * 60  # More expensive per HP for small amounts
                        else:
                            full_heal_cost = missing_health * 40  # Better rate for bulk healing
                        shop_options[3]["cost"] = full_heal_cost
                        shop_options[3]["description"] = f"Restore {missing_health} health ({player_health}/{max_health} → {max_health}/{max_health})"
        
        # Draw shop
        screen.fill(BLACK)
        
        # Shop title
        title = shop_font.render("SHOP - Cycle Complete!", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        
        # Points earned message (with character multiplier)
        cycle_bonus = int(cycle_count * 50 * get_money_multiplier())
        points_msg = font.render(f"Points Earned This Cycle: +{cycle_bonus}", True, (0, 255, 0))
        screen.blit(points_msg, (WIDTH // 2 - points_msg.get_width() // 2, 150))
        
        # Current stats
        stats_y = 200
        character_name = character_stats[selected_character]["name"]
        char_text = font.render(f"Character: {character_name} ({get_money_multiplier():.1f}x money)", True, WHITE)
        health_text = font.render(f"Current Health: {player_health}/{max_health}", True, WHITE)
        points_text = font.render(f"Available Points: {points}", True, WHITE)
        speed_text = font.render(f"Current Speed: {player_speed:.1f}", True, WHITE)
        damage_multiplier = get_damage_multiplier()
        damage_text = font.render(f"Current Damage: {damage_multiplier}x", True, (255, 100, 100))
        upgrades_text = small_font.render(f"Upgrades: Health +{max_health_upgrades}, Speed +{speed_upgrades}", True, (150, 150, 150))
        screen.blit(char_text, (WIDTH // 2 - char_text.get_width() // 2, stats_y))
        screen.blit(health_text, (WIDTH // 2 - health_text.get_width() // 2, stats_y + 30))
        screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, stats_y + 60))
        screen.blit(speed_text, (WIDTH // 2 - speed_text.get_width() // 2, stats_y + 90))
        screen.blit(damage_text, (WIDTH // 2 - damage_text.get_width() // 2, stats_y + 120))
        screen.blit(upgrades_text, (WIDTH // 2 - upgrades_text.get_width() // 2, stats_y + 145))
        
        # Shop options
        option_y = 380
        for i, option in enumerate(shop_options):
            color = WHITE
            if i == selected_option:
                color = (255, 255, 0)  # Yellow for selected
                # Draw selection indicator
                pygame.draw.rect(screen, (50, 50, 50), 
                               (WIDTH // 2 - 300, option_y + i * 60 - 5, 600, 50))
            elif option["cost"] > 0 and points < option["cost"]:
                color = (100, 100, 100)  # Gray for unaffordable
            elif option["name"] == "Heal 1 HP" and player_health >= max_health:
                color = (100, 100, 100)  # Gray if already at full health
            elif option["name"] == "Full Heal" and player_health >= max_health:
                color = (100, 100, 100)  # Gray if already at full health
            
            # Option name and cost
            if option["cost"] > 0:
                option_text = f"{option['name']} - {option['cost']} points"
            else:
                option_text = option["name"]
            
            text = font.render(option_text, True, color)
            screen.blit(text, (WIDTH // 2 - 280, option_y + i * 60))
            
            # Description
            desc_text = small_font.render(option["description"], True, color)
            screen.blit(desc_text, (WIDTH // 2 - 280, option_y + i * 60 + 25))
        
        # Instructions
        instructions = small_font.render("Use W/S to navigate, SPACE to select", True, WHITE)
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 100))
        
        pygame.display.flip()
        clock.tick(FPS)

def character_selection():
    global selected_character
    title_font = pygame.font.SysFont(None, 72)
    instruction_font = pygame.font.SysFont(None, 36)
    
    character_names = ["bur", "also bur", "definitely not bur"]
    character_descriptions = [
        "normal",
        "less hp more money",
        "more hp less money"
    ]
    
    while True:
        screen.fill(BLACK)
        
        # Title
        title_text = title_font.render("Select Your bur", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
        
        # Character selection
        char_y = HEIGHT // 2 - 100
        for i, name in enumerate(character_names):
            char_x = WIDTH // 2 - 200 + i * 200
            
            # Draw character sprite
            char_img = player_imgs[i]
            char_rect = char_img.get_rect()
            char_rect.center = (char_x, char_y)
            screen.blit(char_img, char_rect)
            
            # Draw character name
            name_text = small_font.render(name, True, WHITE)
            name_rect = name_text.get_rect()
            name_rect.center = (char_x, char_y + 60)
            screen.blit(name_text, name_rect)
            
            # Draw character description
            desc_text = small_font.render(character_descriptions[i], True, WHITE)
            desc_rect = desc_text.get_rect()
            desc_rect.center = (char_x, char_y + 80)
            screen.blit(desc_text, desc_rect)
            
            # Highlight selected character
            if i == selected_character:
                pygame.draw.rect(screen, WHITE, 
                               (char_x - 60, char_y - 60, 120, 150), 3)
                select_text = small_font.render("SELECTED", True, WHITE)
                select_rect = select_text.get_rect()
                select_rect.center = (char_x, char_y + 100)
                screen.blit(select_text, select_rect)
        
        # Instructions
        instruction_text = instruction_font.render("Use A/D to select, SPACE to confirm", True, WHITE)
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT - 100))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a and selected_character > 0:
                    selected_character -= 1
                elif event.key == pygame.K_d and selected_character < 2:
                    selected_character += 1
                elif event.key == pygame.K_SPACE:
                    return

def start_screen():
    title_font = pygame.font.SysFont(None, 72)
    instruction_font = pygame.font.SysFont(None, 36)

    while True:
        screen.fill(BLACK)
        title_text = title_font.render("bur", True, WHITE)
        instruction_text = instruction_font.render("Press SPACE to start", True, WHITE)

        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3))
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return

def main():
    global last_pattern_switch, current_pattern, invincible_timer, pattern_duration, cycle_count, points
    global pattern_bullets_spawned, pattern_spawn_timer, current_pattern_index
    
    start_screen()
    character_selection()
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
            # Award bonus points for completing a cycle (with character multiplier)
            points += int(cycle_count * 50 * get_money_multiplier())
            
            # End i-frames and reset player position
            invincible_timer = 0
            player_pos[0] = WIDTH // 2
            player_pos[1] = HEIGHT // 2
            
            show_shop()
            
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
        screen.blit(background_img, (0, 0))
        
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
            game_over_text = font.render("Game Over", True, RED)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
