import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("bur")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)

player_pos = [WIDTH // 2, HEIGHT - 50]
base_player_speed = 5
player_speed = base_player_speed
player_radius = 15

clock = pygame.time.Clock()
FPS = 60

bullets = []

player_health = 8
max_health = 8
invincible_timer = 0
INVINCIBLE_DURATION = FPS * 2
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

# Load sprites
bullet_img = pygame.image.load("bullet.png").convert_alpha()
bullet_img = pygame.transform.scale(bullet_img, (16, 16))

player_img = pygame.image.load("player.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (40, 40))  # Adjust size if needed

def draw_player():
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
        color = (173, 216, 230) if bullet.get('color') == 'blue' else (255, 165, 0)
        pygame.draw.rect(screen, color, rect)
    elif bullet['type'] == 'bullet_stream':
        # Don't draw bullet stream spawners - they're invisible
        pass
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
        # Update rotation for all non-laser bullets
        if bullet['type'] != 'laser':
            bullet['rotation'] += bullet['rotation_speed']
            
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
            bullet['angle'] += bullet['direction'] * 0.15
            max_radius = min(WIDTH, HEIGHT) // 3
            bullet['radius'] = min(bullet['radius'] + 0.5, max_radius)
            bullet['x'] = bullet['center_x'] + math.cos(bullet['angle']) * bullet['radius']
            bullet['y'] = bullet['center_y'] + math.sin(bullet['angle']) * bullet['radius']
            # Remove double spiral bullets when they reach max radius
            if bullet['radius'] >= max_radius:
                bullets.remove(bullet)
        elif bullet['type'] == 'rain':
            bullet['y'] += bullet['speed']
        elif bullet['type'] == 'laser':
            bullet['y'] += bullet['speed']
        elif bullet['type'] == 'zigzag':
            bullet['y'] += bullet['speed_y']
            bullet['x'] = bullet['base_x'] + math.sin(bullet['phase']) * bullet['amplitude']
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
                
                bullets.append({
                    'x': spawn_x,
                    'y': spawn_y,
                    'vx': bullet['direction_x'] * bullet['bullet_speed'],
                    'vy': bullet['direction_y'] * bullet['bullet_speed'],
                    'type': 'radial',
                    'rotation': 0,
                    'rotation_speed': random.uniform(3, 8)
                })
            
            # Remove stream spawner when done
            if bullet['bullets_remaining'] <= 0:
                bullets.remove(bullet)
                continue
        elif bullet['type'] == 'special_bomb':
            # Move towards target position
            dx = bullet['target_x'] - bullet['x']
            dy = bullet['target_y'] - bullet['y']
            dist = math.hypot(dx, dy)
            
            if dist > 5:  # Still moving towards target
                bullet['x'] += (dx / dist) * bullet['speed']
                bullet['y'] += (dy / dist) * bullet['speed']
            else:
                # Reached target, explode into 16 bullets
                if not bullet.get('exploded', False):
                    bullet['exploded'] = True
                    explosion_x, explosion_y = bullet['x'], bullet['y']
                    
                    # Create 16 bullets in a radial pattern
                    for i in range(16):
                        angle = (2 * math.pi / 16) * i
                        speed = 3
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed
                        
                        bullets.append({
                            'x': explosion_x,
                            'y': explosion_y,
                            'vx': vx,
                            'vy': vy,
                            'type': 'radial',
                            'rotation': 0,
                            'rotation_speed': random.uniform(3, 8)
                        })
                    
                    # Remove the special bomb after explosion
                    bullets.remove(bullet)
                    continue
        
        # Remove bullets that have moved off screen (except for targeted bullets, bullet streams, and special bombs which have their own life_time)
        if bullet['type'] not in ['targeted', 'giant_explosive', 'bullet_stream', 'special_bomb']:
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
    bullets.append({
        'x': center_x, 'y': center_y, 'vx': vx, 'vy': vy, 'type': 'spiral',
        'rotation': 0, 'rotation_speed': random.uniform(2, 8)
    })
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
        bullets.append({
            'x': 0,
            'base_y': base_y,
            'wave_phase': i * 0.5,
            'wave_amplitude': amplitude,
            'wave_speed': wave_speed,
            'vx': speed,
            'type': 'wave',
            'y': base_y,
            'rotation': 0,
            'rotation_speed': random.uniform(3, 6)
        })

def spawn_targeted():
    spawn_x = random.randint(50, WIDTH - 50)
    spawn_y = 0
    speed = 3.5
    life_time = FPS * 5
    bullets.append({
        'x': spawn_x, 'y': spawn_y, 'speed': speed, 'type': 'targeted', 
        'life_time': life_time, 'rotation': 0, 'rotation_speed': random.uniform(4, 10)
    })

def spawn_radial_burst():
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    bullet_count = 24
    speed = 5
    for i in range(bullet_count):
        angle = (2 * math.pi / bullet_count) * i
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        bullets.append({
            'x': center_x, 'y': center_y, 'vx': vx, 'vy': vy, 'type': 'radial',
            'rotation': 0, 'rotation_speed': random.uniform(5, 12)
        })

def spawn_expanding_spiral():
    global expanding_spiral_angle
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    expanding_spiral_angle += 0.1
    bullets.append({
        'center_x': center_x,
        'center_y': center_y,
        'angle': expanding_spiral_angle,
        'radius': 0,
        'type': 'expanding_spiral',
        'rotation': 0,
        'rotation_speed': random.uniform(6, 15)
    })

def spawn_double_spiral():
    global double_spiral_angle
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    double_spiral_angle += 0.3

    for direction in (1, -1):
        bullets.append({
            'center_x': center_x,
            'center_y': center_y,
            'angle': direction * double_spiral_angle,
            'radius': 0,
            'direction': direction,
            'type': 'double_spiral',
            'rotation': 0,
            'rotation_speed': random.uniform(8, 18) * direction
        })

def spawn_random_rain():
    spawn_x = random.randint(0, WIDTH)
    speed = random.uniform(5, 8)
    bullets.append({
        'x': spawn_x, 'y': 0, 'speed': speed, 'type': 'rain',
        'rotation': 0, 'rotation_speed': random.uniform(1, 4)
    })

def spawn_homing_burst():
    # Spawn 5 giant bullets that fall from above and randomly explode
    giant_bullet_count = 5  # Increased from 4
    
    for i in range(giant_bullet_count):
        # Random x position across the top of the screen
        spawn_x = random.randint(80, WIDTH - 80)  # Closer to edges
        spawn_y = -50  # Start above screen
        
        # Shorter, more urgent detonation time
        detonate_time = random.randint(int(FPS * 1.0), int(FPS * 2.5))
        
        bullets.append({
            'x': spawn_x,
            'y': spawn_y,
            'vx': 0,  # No horizontal movement
            'vy': 3,  # Faster fall speed
            'speed': 3,
            'type': 'giant_explosive',
            'life_time': detonate_time,
            'size': 5,  # 5x normal size
            'rotation': 0,
            'rotation_speed': random.uniform(2, 5),
            'exploded': False
        })

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
    for offset in range(-150, 151, 75):
        bullets.append({
            'x': center_x + offset, 'y': 0, 'vx': 0, 'vy': speed, 'type': 'radial',
            'rotation': 0, 'rotation_speed': random.uniform(3, 7)
        })
        bullets.append({
            'x': center_x + offset, 'y': HEIGHT, 'vx': 0, 'vy': -speed, 'type': 'radial',
            'rotation': 0, 'rotation_speed': random.uniform(3, 7)
        })
        bullets.append({
            'x': 0, 'y': center_y + offset, 'vx': speed, 'vy': 0, 'type': 'radial',
            'rotation': 0, 'rotation_speed': random.uniform(3, 7)
        })
        bullets.append({
            'x': WIDTH, 'y': center_y + offset, 'vx': -speed, 'vy': 0, 'type': 'radial',
            'rotation': 0, 'rotation_speed': random.uniform(3, 7)
        })

def spawn_zigzag_bullets():
    count = 6  # Reduced from 15 to 6 for 200% more spacing
    spacing = WIDTH // count
    for i in range(count):
        base_x = i * spacing + spacing // 2
        bullets.append({
            'base_x': base_x,
            'y': 0,
            'speed_y': 4,
            'phase': 0,
            'amplitude': 60,
            'frequency': 0.15,
            'type': 'zigzag',
            'rotation': 0,
            'rotation_speed': random.uniform(4, 9)
        })

def spawn_grid_rain():
    rows = 7
    cols = 15
    spacing_x = WIDTH // cols
    spacing_y = 50
    for row in range(rows):
        for col in range(cols):
            x = col * spacing_x + spacing_x // 2
            y = -row * spacing_y
            bullets.append({
                'x': x, 'y': y, 'speed': 5, 'type': 'rain',
                'rotation': 0, 'rotation_speed': random.uniform(2, 5)
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
    }
    return configs.get(pattern_id, (100, 10))

def handle_pattern_spawning():
    global pattern_bullets_spawned, pattern_spawn_timer
    
    total_bullets, spawn_interval = get_pattern_config(current_pattern)
    
    # Check if pattern is complete
    if pattern_bullets_spawned >= total_bullets:
        return True  # Pattern complete
    
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
    
    return False  # Pattern not complete

def check_collisions():
    global player_health, invincible_timer
    keys = pygame.key.get_pressed()
    moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]
    for bullet in bullets[:]:
        if bullet['type'] == 'laser':
            rect = pygame.Rect(bullet['x'], bullet['y'], bullet['width'], bullet['height'])
            if abs(player_pos[0] - rect.centerx) < rect.width // 2 + player_radius and abs(player_pos[1] - rect.centery) < rect.height // 2 + player_radius:
                if invincible_timer <= 0:
                    if bullet.get('color') == 'blue' and moving:
                        player_health -= 1
                        invincible_timer = INVINCIBLE_DURATION
                    elif bullet.get('color') == 'orange' and not moving:
                        player_health -= 1
                        invincible_timer = INVINCIBLE_DURATION
        else:
            collision_radius = bullet_img.get_width() // 2
            if bullet.get('size'):
                collision_radius *= bullet['size']
            
            if math.hypot(bullet['x'] - player_pos[0], bullet['y'] - player_pos[1]) < player_radius + collision_radius:
                if invincible_timer <= 0:
                    player_health -= 1
                    invincible_timer = INVINCIBLE_DURATION
                    bullets.remove(bullet)

def handle_input():
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and player_pos[1] - player_speed - player_radius > 0:
        player_pos[1] -= player_speed
    if keys[pygame.K_s] and player_pos[1] + player_speed + player_radius < HEIGHT:
        player_pos[1] += player_speed
    if keys[pygame.K_a] and player_pos[0] - player_speed - player_radius > 0:
        player_pos[0] -= player_speed
    if keys[pygame.K_d] and player_pos[0] + player_speed + player_radius < WIDTH:
        player_pos[0] += player_speed

def draw_health():
    screen.blit(font.render(f"Health: {player_health}/{max_health}", True, WHITE), (10, 10))
    screen.blit(font.render(f"Points: {points}", True, WHITE), (10, 50))
    screen.blit(font.render(f"Speed: {player_speed:.1f}", True, WHITE), (10, 90))
    screen.blit(font.render(f"Cycle: {cycle_count}", True, WHITE), (10, 130))

def show_shop():
    global player_health, max_health, points, shop_active, cycle_count, max_health_upgrades, speed_upgrades, player_speed
    shop_active = True
    selected_option = 0
    
    # Calculate escalating costs
    max_health_cost = 200 + (max_health_upgrades * 150)  # 200, 350, 500, 650, etc.
    speed_cost = 150 + (speed_upgrades * 100)  # 150, 250, 350, 450, etc.
    
    # Calculate full heal cost based on missing health
    missing_health = max_health - player_health
    full_heal_cost = missing_health * 35  # 35 points per health point to be restored
    
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
                        full_heal_cost = missing_health * 35
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
        upgrades_text = small_font.render(f"Upgrades: Health +{max_health_upgrades}, Speed +{speed_upgrades}", True, (150, 150, 150))
        screen.blit(health_text, (WIDTH // 2 - health_text.get_width() // 2, stats_y))
        screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, stats_y + 30))
        screen.blit(speed_text, (WIDTH // 2 - speed_text.get_width() // 2, stats_y + 60))
        screen.blit(upgrades_text, (WIDTH // 2 - upgrades_text.get_width() // 2, stats_y + 85))
        
        # Shop options
        option_y = 320
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

def handle_special_input(box_bounds):
    keys = pygame.key.get_pressed()
    new_x, new_y = player_pos[0], player_pos[1]
    
    if keys[pygame.K_w]:
        new_y -= player_speed
    if keys[pygame.K_s]:
        new_y += player_speed
    if keys[pygame.K_a]:
        new_x -= player_speed
    if keys[pygame.K_d]:
        new_x += player_speed
    
    # Constrain to box bounds
    new_x = max(box_bounds['left'] + player_radius, min(new_x, box_bounds['right'] - player_radius))
    new_y = max(box_bounds['top'] + player_radius, min(new_y, box_bounds['bottom'] - player_radius))
    
    player_pos[0] = new_x
    player_pos[1] = new_y

def check_box_collision(box_bounds):
    global player_health, invincible_timer
    
    # If player is outside the box, take damage
    if (player_pos[0] - player_radius < box_bounds['left'] or 
        player_pos[0] + player_radius > box_bounds['right'] or
        player_pos[1] - player_radius < box_bounds['top'] or
        player_pos[1] + player_radius > box_bounds['bottom']):
        
        if invincible_timer <= 0:
            player_health -= 1
            invincible_timer = INVINCIBLE_DURATION

def draw_special_box(box_bounds):
    # Draw box outline
    pygame.draw.rect(screen, (255, 100, 100), 
                    (box_bounds['left'], box_bounds['top'], 
                     box_bounds['width'], box_bounds['height']), 3)

def main():
    global last_pattern_switch, current_pattern, invincible_timer, pattern_duration, cycle_count, points
    global pattern_bullets_spawned, pattern_spawn_timer
    
    start_screen()
    running = True
    last_pattern_switch = pygame.time.get_ticks()
    waiting_for_shop = False
    shop_wait_start = 0
    
    # Initialize pattern tracking
    pattern_bullets_spawned = 0
    pattern_spawn_timer = 0
    
    # Special attack phase variables
    special_phase = False
    special_phase_start_time = 0
    special_box_bounds = None
    special_bomb_spawn_timer = 0
    special_bomb_spawn_rate = 60  # Start spawning every 60 frames (1 second)
    special_box_center_x = WIDTH // 2
    special_box_center_y = HEIGHT // 2
    special_box_move_timer = 0
    special_box_direction = [1, 1]  # Movement direction for the box
    
    while running:
        dt = clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Debug cheat code
                    points += 1000

        # Check if we should start special attack phase (every 3 cycles: 3, 6, 9, 12, etc.)
        if not special_phase and cycle_count > 0 and cycle_count % 3 == 0 and current_pattern == 0 and not waiting_for_shop:
            special_phase = True
            special_phase_start_time = current_time
            # Create containment box (300x200 pixels, enough room to move)
            box_width, box_height = 300, 200
            special_box_bounds = {
                'left': special_box_center_x - box_width // 2,
                'right': special_box_center_x + box_width // 2,
                'top': special_box_center_y - box_height // 2,
                'bottom': special_box_center_y + box_height // 2,
                'width': box_width,
                'height': box_height
            }
            special_bomb_spawn_timer = 0
            special_bomb_spawn_rate = 60
            bullets.clear()  # Clear existing bullets for special phase

        # Handle special attack phase
        if special_phase:
            special_phase_elapsed = current_time - special_phase_start_time
            
            # Move the box around (slower than player speed)
            special_box_move_timer += 1
            if special_box_move_timer >= 2:  # Move every 2 frames
                special_box_move_timer = 0
                move_speed = 2  # Slower than minimum player speed
                
                # Calculate new box center position
                new_center_x = special_box_center_x + special_box_direction[0] * move_speed
                new_center_y = special_box_center_y + special_box_direction[1] * move_speed
                
                # Check boundaries and bounce - ensure box stays fully on screen
                half_width = special_box_bounds['width'] // 2
                half_height = special_box_bounds['height'] // 2
                
                if new_center_x - half_width <= 0 or new_center_x + half_width >= WIDTH:
                    special_box_direction[0] *= -1
                    new_center_x = special_box_center_x  # Don't move this frame to avoid getting stuck
                else:
                    special_box_center_x = new_center_x
                
                if new_center_y - half_height <= 0 or new_center_y + half_height >= HEIGHT:
                    special_box_direction[1] *= -1
                    new_center_y = special_box_center_y  # Don't move this frame to avoid getting stuck
                else:
                    special_box_center_y = new_center_y
                
                # Update box bounds
                special_box_bounds['left'] = special_box_center_x - half_width
                special_box_bounds['right'] = special_box_center_x + half_width
                special_box_bounds['top'] = special_box_center_y - half_height
                special_box_bounds['bottom'] = special_box_center_y + half_height
            
            # Increase bomb spawn rate over time
            time_factor = min(special_phase_elapsed / 1000.0, 5.0)  # Max at 5 seconds
            special_bomb_spawn_rate = max(15, int(60 - (time_factor * 9)))  # From 60 to 15 frames
            
            # Spawn targeted bombs
            special_bomb_spawn_timer += 1
            if special_bomb_spawn_timer >= special_bomb_spawn_rate:
                special_bomb_spawn_timer = 0
                # Spawn bomb targeting current player position
                spawn_x = random.randint(0, WIDTH)
                target_x, target_y = player_pos[0], player_pos[1]
                
                bullets.append({
                    'x': spawn_x,
                    'y': -30,
                    'target_x': target_x,
                    'target_y': target_y,
                    'speed': 4,
                    'type': 'special_bomb',
                    'rotation': 0,
                    'rotation_speed': random.uniform(5, 12)
                })
            
            # End special phase after 30 seconds
            if special_phase_elapsed >= 30000:
                special_phase = False
                special_box_bounds = None
                cycle_count += 1
                points += cycle_count * 50
                waiting_for_shop = True
                shop_wait_start = current_time
                continue

        # Handle shop waiting state
        if waiting_for_shop:
            # Wait for all bullets to disappear before opening shop
            if len(bullets) == 0:
                # All bullets gone, open shop
                show_shop()
                waiting_for_shop = False
                pattern_duration = max(1000, int(base_pattern_duration * (0.9 ** cycle_count)))
                last_pattern_switch = pygame.time.get_ticks()
                # Reset pattern tracking for new cycle
                pattern_bullets_spawned = 0
                pattern_spawn_timer = 0
            else:
                # Show waiting message
                screen.fill(BLACK)
                wait_text = font.render("Cycle Complete! Clearing bullets...", True, WHITE)
                screen.blit(wait_text, (WIDTH // 2 - wait_text.get_width() // 2, HEIGHT // 2))
                
                # Continue moving and drawing bullets
                move_bullets()
                for bullet in bullets:
                    draw_bullet(bullet)
                    
                pygame.display.flip()
                continue

        # Regular game logic (only if not in special phase)
        if not special_phase:
            handle_input()

            # Handle pattern spawning based on bullet count instead of time
            pattern_complete = handle_pattern_spawning()
            
            if pattern_complete:
                # Award points for completing a pattern
                points += 10
                
                current_pattern = (current_pattern + 1) % 12
                last_pattern_switch = current_time
                
                # Reset pattern tracking
                pattern_bullets_spawned = 0
                pattern_spawn_timer = 0
                
                # Check if we completed a full cycle (but not special cycle)
                if current_pattern == 0:
                    cycle_count += 1
                    # Award bonus points for completing a cycle
                    points += cycle_count * 50
                    # Start waiting for bullets to clear
                    waiting_for_shop = True
                    shop_wait_start = current_time
                    continue  # Skip the rest of the loop
        else:
            # Special phase input handling with box constraints
            handle_special_input(special_box_bounds)

        move_bullets()
        check_collisions()
        
        # Check box collision in special phase
        if special_phase and special_box_bounds:
            check_box_collision(special_box_bounds)

        if invincible_timer > 0:
            invincible_timer -= 1

        screen.fill(BLACK)
        
        # Draw special box if in special phase
        if special_phase and special_box_bounds:
            draw_special_box(special_box_bounds)
        
        draw_player()
        for bullet in bullets:
            draw_bullet(bullet)
        draw_health()
        
        # Special phase indicator
        if special_phase:
            special_text = font.render("SPECIAL ATTACK PHASE", True, (255, 100, 100))
            screen.blit(special_text, (WIDTH // 2 - special_text.get_width() // 2, 10))

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
