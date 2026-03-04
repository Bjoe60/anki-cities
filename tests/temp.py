import math
import json

# --------------------------------------------------
# Projection formulas (example from your message)
# --------------------------------------------------

def project(lat, lon):
    r = math.pi / 180

    x = (35.0444) * (
        math.cos(lat*r) * math.sin((lon + (lon < 0)*360 - (-165.0)) * r)
    ) * (
        ((1
          + math.sin(lat*r)*math.sin(-10.0*r)
          + math.cos(lat*r)*math.cos(-10.0*r)
          * math.cos((lon + (lon < 0)*360 - (-165.0))*r)
        ) * 0.5) ** -0.5
    ) - (-50.0)

    y = (100 + (-49.0056)) - (38.3135) * (
        math.cos(-10.0*r)*math.sin(lat*r)
        - math.sin(-10.0*r)*math.cos(lat*r)
        * math.cos((lon + (lon < 0)*360 - (-165.0))*r)
    ) * (
        ((1
          + math.sin(lat*r)*math.sin(-10.0*r)
          + math.cos(lat*r)*math.cos(-10.0*r)
          * math.cos((lon + (lon < 0)*360 - (-165.0))*r)
        ) * 0.5) ** -0.5
    )

    return x, y


# --------------------------------------------------
# Build lookup grid
# --------------------------------------------------

GRID_SIZE = 100

grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# sample the globe
for lat in range(-90, 91):
    for lon in range(-180, 181):

        x, y = project(lat, lon)

        ix = int(x)
        iy = int(y)

        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            grid[iy][ix] = (lat, lon)


# --------------------------------------------------
# Fill missing cells (nearest neighbour)
# --------------------------------------------------

for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):

        if grid[y][x] is None:

            best = None
            best_d = 9999

            for yy in range(GRID_SIZE):
                for xx in range(GRID_SIZE):

                    if grid[yy][xx] is None:
                        continue

                    d = (xx-x)**2 + (yy-y)**2

                    if d < best_d:
                        best_d = d
                        best = grid[yy][xx]

            grid[y][x] = best


# --------------------------------------------------
# Save grid
# --------------------------------------------------

with open("projection_lookup.json", "w") as f:
    json.dump(grid, f)

print("Lookup grid saved.")


# --------------------------------------------------
# Example inverse lookup
# --------------------------------------------------

def lookup_latlon(x, y):

    x0 = int(x)
    y0 = int(y)

    x1 = min(x0+1, GRID_SIZE-1)
    y1 = min(y0+1, GRID_SIZE-1)

    q11 = grid[y0][x0]
    q21 = grid[y0][x1]
    q12 = grid[y1][x0]
    q22 = grid[y1][x1]

    fx = x - x0
    fy = y - y0

    lat = (
        q11[0]*(1-fx)*(1-fy) +
        q21[0]*fx*(1-fy) +
        q12[0]*(1-fx)*fy +
        q22[0]*fx*fy
    )

    lon = (
        q11[1]*(1-fx)*(1-fy) +
        q21[1]*fx*(1-fy) +
        q12[1]*(1-fx)*fy +
        q22[1]*fx*fy
    )

    return lat, lon


# --------------------------------------------------
# Test
# --------------------------------------------------

test_lat = 40
test_lon = -120

x, y = project(test_lat, test_lon)

lat2, lon2 = lookup_latlon(x, y)

print("Original:", test_lat, test_lon)
print("Projected:", x, y)
print("Recovered:", lat2, lon2)