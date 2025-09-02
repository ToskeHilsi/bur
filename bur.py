import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1920, 1080 #normally 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("bur")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (100, 100, 255)
GREEN = (50, 255, 50)
PURPLE = (150, 50, 200)
LIGHT_PURPLE = (50, 20, 70)

player_pos = [WIDTH // 2, HEIGHT - 50]
base_player_speed = 5
player_speed = base_player_speed
player_radius = 15

# Phase mechanic variables
phased = False
phase_background_alpha = 30
p_key_pressed = False  # Track P key state to prevent toggle spam

# Character selection
selected_character = 0  # 0, 1, or 2

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
bullet_img = pygame.transform.scale(bullet_img, (16, 16))

# Character sprites - you'll need to provide these
try:
    player_imgs = [
        pygame.image.load("player1.png").convert_alpha(),
        pygame.image.load("player2.png").convert_alpha(), 
        pygame.image.load("player3.png").convert_alpha()
    ]
    # Scale all character sprites
    for i in range(len(player_imgs)):
        player_imgs[i] = pygame.transform.scale(player_imgs[i], (40, 40))
except:
    # Fallback if custom sprites aren't available
    player_imgs = [
        pygame.image.load("player.png").convert_alpha(),
        pygame.image.load("player.png").convert_alpha(),
        pygame.image.load("player.png").convert_alpha()
    ]
    for i in range(len(player_imgs)):
        player_imgs[i] = pygame.transform.scale(player_imgs[i], (40, 40))

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
    
    # Apply purple tint if phased
    if phased:
        tinted_img = player_img.copy()
        purple_overlay = pygame.Surface(tinted_img.get_size())
        purple_overlay.fill(PURPLE)
        tinted_img.blit(purple_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
        player_img = tinted_img
    
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
        elif bullet.get('color') == 'purple':
            # Purple laser only visible when not phased
            if not phased:
                color = PURPLE
            else:
                return  # Don't draw purple laser when phased
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
    elif bullet['type'] == 'screen_attack':
        if bullet['state'] == 'warning':
            # Draw purple warning overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(50 + int(20 * math.sin(pygame.time.get_ticks() * 0.01)))  # Pulsing effect
            overlay.fill(PURPLE)
            screen.blit(overlay, (0, 0))
            
            # Draw warning text
            warning_text = font.render("SCREEN ATTACK INCOMING!", True, PURPLE)
            screen.blit(warning_text, (WIDTH // 2 - warning_text.get_width() // 2, HEIGHT // 2 - 50))
            
            phase_text = small_font.render("Press P to phase!", True, WHITE)
            screen.blit(phase_text, (WIDTH // 2 - phase_text.get_width() // 2, HEIGHT // 2 + 20))
        elif bullet['state'] == 'active':
            # Draw solid purple overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill(PURPLE)
            screen.blit(overlay, (0, 0))
    elif bullet['type'] == 'bullet_stream':
        # Don't draw bullet stream spawners - they're invisible
        pass
    else:
        # Scale bullet sprite based on size
        size_multiplier = bullet.get('size', 1)
        scaled_size = (int(bullet_img.get_width() * size_multiplier), 
                      int(bullet_img.get_height() * size_multiplier))
        scaled_img = pygame.transform.scale(bullet_img, scaled_size)
        
        # Color healing bullets green or phase bullets purple
        if bullet.get('healing', False):
            # Create a green-tinted version
            green_img = scaled_img.copy()
            green_img.fill(GREEN, special_flags=pygame.BLEND_MULT)
            scaled_img = green_img
        elif phased:
            # Make bullets purple when phased
            purple_img = scaled_img.copy()
            purple_img.fill(PURPLE, special_flags=pygame.BLEND_MULT)
            scaled_img = purple_img
        
        # Rotate the bullet sprite
        rotated_img = pygame.transform.rotate(scaled_img, bullet['rotation'])
        rotated_rect = rotated_img.get_rect()
        rotated_rect.center = (int(bullet['x']), int(bullet['y']))
        screen.blit(rotated_img, rotated_rect)

def move_bullets():
    for bullet in bullets[:]:
        # Update rotation for all non-laser bullets that have rotation (except giant explosive bullets)
        if bullet['type'] not in ['laser', 'slash_attack', 'screen_attack'] and 'rotation_speed' in bullet:
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
                # Create 10 bullet streams at random angles (increased from 6)
                explosion_x, explosion_y = bullet['x'], bullet['y']
                bullets_per_line = 25  # Increased from 15
                bullet_speed = 5  # Faster bullets
                line_count = 10  # Increased from 6
                
                # Generate random angles with some spread to avoid clustering
                for line_idx in range(line_count):
                    angle = random.uniform(0, 2 * math.pi)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    
                    # Create a bullet stream spawner
                    bullets.append({
                        'x': explosion_x,
                        'y': explosion_y,
                        'type': 'bullet_stream',
                        'direction_x': dx,
                        'direction_y': dy,
                        'bullet_speed': bullet_speed,
                        'bullets_remaining': bullets_per_line,
                        'spawn_timer': 0,
                        'spawn_interval': 2,  # Even faster spawning (every 2 frames instead of 3)
                        'bullets_spawned': 0,
                        'rotation': 0,
                        'rotation_speed': 0
                    })
                
                # Remove the giant bullet after explosion
                bullets.remove(bullet)
                continue
        elif bullet['type'] == 'bullet_stream':
            # Handle bullet stream spawning
            bullet['spawn_timer'] += 1
            
            if bullet['spawn_timer'] >= bullet['spawn_interval'] and bullet['bullets_remaining'] > 0:
                bullet['spawn_timer'] = 0
                bullet['bullets_remaining'] -= 1
                bullet['bullets_spawned'] += 1
                
                # Spawn a bullet at increasing distance from origin
                spawn_distance = bullet['bullets_spawned'] * 15  # Even tighter spacing (15 instead of 20)
                spawn_x = bullet['x'] + bullet['direction_x'] * spawn_distance
                spawn_y = bullet['y'] + bullet['direction_y'] * spawn_distance
                
                new_bullet = {
                    'x': spawn_x,
                    'y': spawn_y,
                    'vx': bullet['direction_x'] * bullet['bullet_speed'],
                    'vy': bullet['direction_y'] * bullet['bullet_speed'],
                    'type': 'radial',
                    'rotation': 0,
                    'rotation_speed': 5,  # Will be overridden to uniform speed
                    'healing': False
                }
                
                bullets.append(new_bullet)
            
            # Remove stream spawner when done
            if bullet['bullets_remaining'] <= 0:
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
        elif bullet['type'] == 'screen_attack':
            # Handle screen attack timing
            if bullet['state'] == 'warning':
                bullet['warning_time'] -= 1
                if bullet['warning_time'] <= 0:
                    bullet['state'] = 'active'
            elif bullet['state'] == 'active':
                bullet['active_time'] -= 1
                if bullet['active_time'] <= 0:
                    bullets.remove(bullet)
                    continue
        
        # Remove bullets that have moved off screen (except for targeted bullets, bullet streams, slash attacks, and screen attacks which have their own life_time)
        if bullet['type'] not in ['targeted', 'giant_explosive', 'bullet_stream', 'slash_attack', 'screen_attack']:
            if (bullet['x'] < -50 or bullet['x'] > WIDTH + 50 or 
                bullet['y'] < -50 or bullet['y'] > HEIGHT + 50):
                if bullet in bullets:  # Safety check
                    bullets.remove(bullet)

def add_healing_chance_to_bullet(bullet_dict):
    """Add a small chance for any bullet to be a healing bullet - DISABLED"""
    # Healing bullets removed entirely
    return bullet_dict

def spawn_spiral():
    global spiral_angle
    center_x, center_y = WIDTH // 2, 150
    speed = 4
    vx = math.cos(spiral_angle) * speed
    vy = math.sin(spiral_angle) * speed
    bullet = {
        'x': center_x, 'y': center_y, 'vx': vx, 'vy': vy, 'type': 'spiral',
        'rotation': 0, 'rotation_speed': 5, 'healing': False
    }
    bullets.append(add_healing_chance_to_bullet(bullet))
    spiral_angle += 0.15

def spawn_wave():
    speed = 4
    amplitude = 60
    wave_speed = 0.1
    bullets_per_wave = 7
    spacing = 40

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
            'rotation_speed': 5,
            'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))

def spawn_targeted():
    spawn_x = random.randint(50, WIDTH - 50)
    spawn_y = 0
    speed = 3.5
    life_time = FPS * 5
    bullet = {
        'x': spawn_x, 'y': spawn_y, 'speed': speed, 'type': 'targeted', 
        'life_time': life_time, 'rotation': 0, 'rotation_speed': 5, 'healing': False
    }
    bullets.append(add_healing_chance_to_bullet(bullet))

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
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))

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
        'rotation_speed': 5,
        'healing': False
    }
    bullets.append(add_healing_chance_to_bullet(bullet))

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
            'rotation_speed': 5 * direction,
            'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))

def spawn_random_rain():
    # Can spawn from walls too now
    wall_choice = random.choice(['top', 'bottom', 'left', 'right'])
    speed = random.uniform(5, 8)
    
    if wall_choice == 'top':
        spawn_x = random.randint(0, WIDTH)
        spawn_y = 0
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'speed': speed, 'type': 'rain',
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))
    elif wall_choice == 'bottom':
        spawn_x = random.randint(0, WIDTH)
        spawn_y = HEIGHT
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'speed': -speed, 'type': 'rain',  # Negative speed to go upward
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))
    elif wall_choice == 'left':
        spawn_x = 0
        spawn_y = random.randint(0, HEIGHT)
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'vx': speed, 'vy': 0, 'type': 'radial',  # Horizontal movement
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))
    elif wall_choice == 'right':
        spawn_x = WIDTH
        spawn_y = random.randint(0, HEIGHT)
        bullet = {
            'x': spawn_x, 'y': spawn_y, 'vx': -speed, 'vy': 0, 'type': 'radial',  # Horizontal movement
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet))

def spawn_homing_burst():
    # Spawn 5 giant bullets that fall from above and randomly explode
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
            'exploded': False,
            'healing': False  # Giant bullets can't be healing
        }
        bullets.append(bullet)

def spawn_laser_beams():
    beam_width = WIDTH
    beam_height = 10
    speed = 8
    y_start = 0
    color = random.choice(['blue', 'orange', 'purple'])  # Added purple laser
    bullets.append({
        'x': 0,
        'y': y_start,
        'width': beam_width,
        'height': beam_height,
        'speed': speed,
        'type': 'laser',
        'color': color,
        'healing': False  # Lasers can't be healing
    })

def spawn_cross_pattern():
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    speed = 6
    for offset in range(-150, 151, 75):
        bullet1 = {
            'x': center_x + offset, 'y': 0, 'vx': 0, 'vy': speed, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet1))
        bullet2 = {
            'x': center_x + offset, 'y': HEIGHT, 'vx': 0, 'vy': -speed, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet2))
        bullet3 = {
            'x': 0, 'y': center_y + offset, 'vx': speed, 'vy': 0, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet3))
        bullet4 = {
            'x': WIDTH, 'y': center_y + offset, 'vx': -speed, 'vy': 0, 'type': 'radial',
            'rotation': 0, 'rotation_speed': 5, 'healing': False
        }
        bullets.append(add_healing_chance_to_bullet(bullet4))

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
                'amplitude': 60,
                'frequency': 0.15,
                'type': 'zigzag',
                'rotation': 0,
                'rotation_speed': 5,
                'healing': False
            }
            bullets.append(add_healing_chance_to_bullet(bullet))
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
                'amplitude': 60,
                'frequency': 0.15,
                'type': 'zigzag_horizontal',
                'rotation': 0,
                'rotation_speed': 5,
                'healing': False
            }
            bullets.append(add_healing_chance_to_bullet(bullet))

def spawn_grid_rain():
    # Can spawn from walls too now
    wall_choice = random.choice(['top', 'bottom', 'left', 'right'])
    
    if wall_choice == 'top':
        rows = 7
        cols = 15
        spacing_x = WIDTH // cols
        spacing_y = 50
        for row in range(rows):
            for col in range(cols):
                x = col * spacing_x + spacing_x // 2
                y = -row * spacing_y
                bullet = {
                    'x': x, 'y': y, 'speed': 5, 'type': 'rain',
                    'rotation': 0, 'rotation_speed': 5, 'healing': False
                }
                bullets.append(add_healing_chance_to_bullet(bullet))
    elif wall_choice == 'bottom':
        rows = 7
        cols = 15
        spacing_x = WIDTH // cols
        spacing_y = 50
        for row in range(rows):
            for col in range(cols):
                x = col * spacing_x + spacing_x // 2
                y = HEIGHT + row * spacing_y
                bullet = {
                    'x': x, 'y': y, 'speed': -5, 'type': 'rain',  # Negative speed to go upward
                    'rotation': 0, 'rotation_speed': 5, 'healing': False
                }
                bullets.append(add_healing_chance_to_bullet(bullet))
    elif wall_choice == 'left':
        rows = 15
        cols = 7
        spacing_x = 50
        spacing_y = HEIGHT // rows
        for row in range(rows):
            for col in range(cols):
                x = -col * spacing_x
                y = row * spacing_y + spacing_y // 2
                bullet = {
                    'x': x, 'y': y, 'vx': 5, 'vy': 0, 'type': 'radial',
                    'rotation': 0, 'rotation_speed': 5, 'healing': False
                }
                bullets.append(add_healing_chance_to_bullet(bullet))
    elif wall_choice == 'right':
        rows = 15
        cols = 7
        spacing_x = 50
        spacing_y = HEIGHT // rows
        for row in range(rows):
            for col in range(cols):
                x = WIDTH + col * spacing_x
                y = row * spacing_y + spacing_y // 2
                bullet = {
                    'x': x, 'y': y, 'vx': -5, 'vy': 0, 'type': 'radial',
                    'rotation': 0, 'rotation_speed': 5, 'healing': False
                }
                bullets.append(add_healing_chance_to_bullet(bullet))

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
            'state': 'warning',   # 'warning' then 'active'
            'healing': False  # Slash attacks can't be healing
        })

def spawn_screen_attack():
    """Spawn the special screen attack that hits everywhere"""
    bullets.append({
        'type': 'screen_attack',
        'warning_time': 120,  # 2 seconds warning at 60 FPS
        'active_time': 30,    # Half second active
        'state': 'warning',   # 'warning' then 'active'
        'healing': False
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
        7: (5, 100),      # giant_explosive: 5 giant bullets (1250 explosion bullets total)
        8: (8, 60),       # laser_beams: 8 beams
        9: (5, 100),      # cross_pattern: 5 crosses (80 bullets total)
        10: (10, 50),     # zigzag: 10 volleys (60 bullets total)
        11: (2, 200),     # grid_rain: 2 grids (210 bullets total)
        12: (8, 50),      # slash_attacks: 8 volleys (24 slashes total)
        13: (3, 180),     # screen_attack: 3 screen attacks
    }
    return configs.get(pattern_id, (100, 10))

def randomize_cycle_patterns():
    """Create a randomized order of all patterns for the current cycle"""
    global current_cycle_patterns, current_pattern_index
    current_cycle_patterns = list(range(14))  # All pattern IDs 0-13 (now includes screen_attack)
    random.shuffle(current_cycle_patterns)
    current_pattern_index = 0

def is_cycle_complete():
    """Check if the cycle is complete (all patterns done and no bullets/spawners left)"""
    # Check if all patterns have been completed
    patterns_complete = current_pattern_index >= len(current_cycle_patterns)
    
    # Check if there are any active bullets or bullet spawners
    active_bullets_or_spawners = len(bullets) > 0
    
    return patterns_complete and not active_bullets_or_spawners

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
        
        # Award points for completing a pattern
        points += 10
        
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
        elif current_pattern == 13:
            spawn_screen_attack()
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
                        damage = 5 * damage_multiplier if phased else damage_multiplier
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
                        # No particles for laser attacks
                    elif bullet.get('color') == 'orange' and not moving:
                        damage = 5 * damage_multiplier if phased else damage_multiplier
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
                        # No particles for laser attacks
                    elif bullet.get('color') == 'purple':
                        # Purple laser only damages when not phased
                        if not phased:
                            player_health -= 5
                            invincible_timer = INVINCIBLE_DURATION
                            # No particles for laser attacks
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
                        damage = 5 * damage_multiplier if phased else damage_multiplier
                        player_health -= damage
                        invincible_timer = INVINCIBLE_DURATION
                        # No particles for slash attacks
        elif bullet['type'] == 'screen_attack':
            # Only check collision when attack is active and player is not phased
            if bullet['state'] == 'active':
                if phased:
                    # Remove the screen attack if player is phased - no damage taken
                    bullets.remove(bullet)
                    continue
                else:
                    # Player takes 5 damage from screen attack
                    if invincible_timer <= 0:
                        player_health -= 5
                        invincible_timer = INVINCIBLE_DURATION
                        create_hit_particles(player_pos[0], player_pos[1])
                        bullets.remove(bullet)
                        continue
        elif bullet['type'] == 'zigzag_horizontal':
            # Handle horizontal zigzag collision
            collision_radius = bullet_img.get_width() // 2
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                if invincible_timer <= 0:
                    # Phased players take 5x damage multiplier damage from all bullets
                    damage = 5 * damage_multiplier if phased else damage_multiplier
                    player_health -= damage
                    invincible_timer = INVINCIBLE_DURATION
                    create_hit_particles(player_pos[0], player_pos[1])
                    bullets.remove(bullet)
        else:
            collision_radius = bullet_img.get_width() // 2
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                if invincible_timer <= 0:
                    # Phased players take 5x damage multiplier damage from all bullets
                    damage = 5 * damage_multiplier if phased else damage_multiplier
                    player_health -= damage
                    invincible_timer = INVINCIBLE_DURATION
                    create_hit_particles(player_pos[0], player_pos[1])
                    bullets.remove(bullet)

def handle_input():
    global phased, p_key_pressed
    
    keys = pygame.key.get_pressed()
    
    # Handle phase toggle - only toggle when P is pressed (not held)
    if keys[pygame.K_p] and not p_key_pressed:
        phased = not phased  # Toggle phase state
        p_key_pressed = True
    elif not keys[pygame.K_p]:
        p_key_pressed = False
    
    # Handle movement
    if keys[pygame.K_w] and player_pos[1] - player_speed - player_radius > 0:
        player_pos[1] -= player_speed
    if keys[pygame.K_s] and player_pos[1] + player_speed + player_radius < HEIGHT:
        player_pos[1] += player_speed
    if keys[pygame.K_a] and player_pos[0] - player_speed - player_radius > 0:
        player_pos[0] -= player_speed
    if keys[pygame.K_d] and player_pos[0] + player_speed + player_radius < WIDTH:
        player_pos[0] += player_speed

def draw_health():
    damage_multiplier = get_damage_multiplier()
    screen.blit(font.render(f"Health: {player_health}/{max_health}", True, WHITE), (10, 10))
    screen.blit(font.render(f"Points: {points}", True, WHITE), (10, 50))
    screen.blit(font.render(f"Speed: {player_speed:.1f}", True, WHITE), (10, 90))
    screen.blit(font.render(f"Cycle: {cycle_count}", True, WHITE), (10, 130))
    screen.blit(font.render(f"Damage: {damage_multiplier}x", True, (255, 100, 100)), (10, 170))
    
    # Show phase status
    if phased:
        phase_text = font.render("PHASED", True, PURPLE)
        screen.blit(phase_text, (10, 210))
        phase_info = small_font.render(f"All bullets deal {5 * damage_multiplier} damage", True, PURPLE)
        screen.blit(phase_info, (10, 240))
    else:
        controls_text = small_font.render("Press P to phase", True, WHITE)
        screen.blit(controls_text, (10, 210))

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
        
        # Points earned message
        points_msg = font.render(f"Points Earned This Cycle: +{cycle_count * 50}", True, (0, 255, 0))
        screen.blit(points_msg, (WIDTH // 2 - points_msg.get_width() // 2, 150))
        
        # Current stats
        stats_y = 200
        health_text = font.render(f"Current Health: {player_health}/{max_health}", True, WHITE)
        points_text = font.render(f"Available Points: {points}", True, WHITE)
        speed_text = font.render(f"Current Speed: {player_speed:.1f}", True, WHITE)
        damage_multiplier = get_damage_multiplier()
        damage_text = font.render(f"Current Damage: {damage_multiplier}x", True, (255, 100, 100))
        upgrades_text = small_font.render(f"Upgrades: Health +{max_health_upgrades}, Speed +{speed_upgrades}", True, (150, 150, 150))
        screen.blit(health_text, (WIDTH // 2 - health_text.get_width() // 2, stats_y))
        screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, stats_y + 30))
        screen.blit(speed_text, (WIDTH // 2 - speed_text.get_width() // 2, stats_y + 60))
        screen.blit(damage_text, (WIDTH // 2 - damage_text.get_width() // 2, stats_y + 90))
        screen.blit(upgrades_text, (WIDTH // 2 - upgrades_text.get_width() // 2, stats_y + 115))
        
        # Shop options
        option_y = 350
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
            
            # Highlight selected character
            if i == selected_character:
                pygame.draw.rect(screen, WHITE, 
                               (char_x - 50, char_y - 50, 100, 120), 3)
                select_text = small_font.render("SELECTED", True, WHITE)
                select_rect = select_text.get_rect()
                select_rect.center = (char_x, char_y + 80)
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
    
    running = True
    last_pattern_switch = pygame.time.get_ticks()
    
    # Initialize pattern tracking
    pattern_bullets_spawned = 0
    pattern_spawn_timer = 0
    randomize_cycle_patterns()  # Initialize randomized pattern order
    
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
            # Award bonus points for completing a cycle
            points += cycle_count * 50
            
            # End i-frames and reset player position
            invincible_timer = 0
            player_pos[0] = WIDTH // 2
            player_pos[1] = HEIGHT - 50
            
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

        screen.fill(BLACK)
        
        # Add purple background tint if phased
        if phased:
            phase_overlay = pygame.Surface((WIDTH, HEIGHT))
            phase_overlay.set_alpha(phase_background_alpha)
            phase_overlay.fill(LIGHT_PURPLE)
            screen.blit(phase_overlay, (0, 0))
        
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
