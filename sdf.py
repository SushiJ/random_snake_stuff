import time
import math

def donut(x: float, y: float, z: float) -> float:
   radius = 0.4 
   thickness = 0.3

   xy_d = math.sqrt(x**2 + y**2) - radius

   d = math.sqrt(xy_d**2 + z**2)

   return d - thickness / 2

def sample(x: float, y: float) -> str:
    z = -10 
    for _ in range(30):
        delta = time.time() * 2
        # rotating input cords
        t_x = x * math.cos(delta) - z * math.sin(delta)
        t_z = x * math.sin(delta) + z * math.cos(delta)

        # t_y = x * math.cos(delta) - z * math.sin(delta)
        # t_z = x * math.cos(delta) + z * math.sin(delta)

        d = donut(t_x, y, t_z)
        if d <= 0.01:
            return '#'
        else:
            z += d
    return ' '


while True:
    frame_chars = []
    for y in range(20):
        for x in range(80):
            # Normalizing x and making sure to preserve the aspect ratio in y
            remapped_x = x / 80 * 2 - 1
            remapped_y = (y / 20 * 2 - 1) * (2 * 20/80)

            frame_chars.append(sample(remapped_x, remapped_y))
        frame_chars.append('\n')

    # Clear screen and then print chars
    print('\033[2J' + ''.join(frame_chars))
    # 30FPS
    time.sleep(1/30)
