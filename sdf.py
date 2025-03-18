import time
import math
import typing

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
            _, nt_y, nt_z = normal(donut, t_x, y, t_z)
            
            is_lit = nt_y < -0.15
            is_frosted = nt_z < - 0.15
            if is_frosted:
                return '@' if is_lit else '#'
            else:
                return '=' if is_lit else '.'
        else:
            z += d
    return ' '

Sdf = typing.Callable[[float, float, float], float]
def normal(sdf: Sdf, x: float, y: float, z: float) -> tuple[float, float, float]:
    dt = 0.001

    n_x = sdf(x + dt, y, z) - sdf(x - dt, y, z)
    n_y = sdf(x, y + dt, z) - sdf(x , y - dt, z)
    n_z = sdf(x, y, z + dt) - sdf(x, y, z - dt)

    norm = math.sqrt(n_x**2 + n_y**2 + n_z**2)
    return (n_x / norm, n_y / norm, n_z / norm)


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
