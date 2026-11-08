from build123d import *
import math

# --- parameters (mm) ---
pitch = 2.54
grid_n = 9                 # 9x9 holes, columns A-I, rows 1-9
board_size = 25.0
board_t = 1.6
hole_d = 1.0
pad_d = 1.8
pad_t = 0.05
mount_hole_d = 3.0
mount_hole_cell = ("E", 1)  # ASSUMPTION: mounting hole centred on row 1

def xy(col, row):
    c = "ABCDEFGHI".index(col)
    return ((c - (grid_n - 1) / 2) * pitch, -((row - 1) - (grid_n - 1) / 2) * pitch)

top = board_t / 2
bot = -board_t / 2

# board with holes
mx, my = xy(*mount_hole_cell)
board = Box(board_size, board_size, board_t)
keep = []
for ci, col in enumerate("ABCDEFGHI"):
    for row in range(1, grid_n + 1):
        x, y = xy(col, row)
        if math.hypot(x - mx, y - my) < mount_hole_d / 2 + pad_d / 2 + 0.2:
            continue
        keep.append((x, y))
holes = Compound([Cylinder(hole_d / 2, board_t * 2).move(Location((x, y, 0))) for x, y in keep])
board = board - holes - Cylinder(mount_hole_d / 2, board_t * 2).move(Location((mx, my, 0)))
show(board, "board")
print(len(keep))

pad_ring = Cylinder(pad_d / 2, pad_t) - Cylinder(hole_d / 2, pad_t * 2)
pads = Compound([pad_ring.moved(Location((x, y, bot - pad_t / 2))) for x, y in keep])
show(pads, "pads")

# --- DIP-8 open-frame socket: pins 1-4 at C3-C6, pins 8-5 at F3-F6, notch toward row 1 ---
sock_len = 10.2        # along rows (Y)
sock_w = 10.1          # across columns (X)
sock_h = 4.3
sock_standoff = 0.6
rail_w = 2.4
win_y = 5.6            # open window length
c3 = xy("C", 3); f6 = xy("F", 6)
scx = (c3[0] + f6[0]) / 2; scy = (c3[1] + f6[1]) / 2
frame_h = sock_h - sock_standoff
socket = Box(sock_w, sock_len, frame_h)
socket -= Box(sock_w - 2 * rail_w, win_y, frame_h * 2)
socket -= Cylinder(0.8, frame_h * 2).move(Location((0, sock_len / 2, 0)))   # notch
socket = socket.move(Location((scx, scy, top + sock_standoff + frame_h / 2)))
sock_pins = []
for r in range(3, 7):
    for col in "CF":
        x, y = xy(col, r)
        sock_pins.append(Box(0.5, 0.3, sock_standoff + board_t + 3.0).move(
            Location((x, y, top + sock_standoff - (sock_standoff + board_t + 3.0) / 2 + sock_standoff))))
socket = socket + Compound(sock_pins)
show(socket, "socket")

# --- ATtiny85 DIP-8 ---
chip_l = 9.27; chip_w = 6.35; chip_h = 3.3
chip_z0 = top + sock_h + 0.4
chip = Box(chip_w, chip_l, chip_h).move(Location((scx, scy, chip_z0 + chip_h / 2)))
chip -= Cylinder(1.0, chip_h).move(Location((scx, scy + chip_l / 2, chip_z0 + chip_h)))  # notch
chip -= Cylinder(0.5, 0.4).move(Location((c3[0] + 1.6, c3[1] - 1.0, chip_z0 + chip_h)))  # pin-1 dot
legs = []
for r in range(3, 7):
    for col, sgn in (("C", -1), ("F", 1)):
        x, y = xy(col, r)
        legs.append(Box(0.5, 1.5, 0.25).move(Location((x - sgn * 0.6, y, chip_z0 + 1.0))))
        legs.append(Box(0.3, 0.45, 3.5).move(Location((x, y, chip_z0 + 1.0 - 1.75))))
chip = chip + Compound(legs)
show(chip, "attiny85")

def seg(p1, p2, r):
    p1 = Vector(*p1); p2 = Vector(*p2)
    d = p2 - p1
    return Solid.make_cylinder(r, d.length, Plane(origin=p1, z_dir=d))

def pt(cell, z):
    x, y = xy(*cell); return (x, y, z)

# --- 0.1uF ceramic cap lying flat inside the socket window, legs E3 -> D6 ---
lead_r = 0.25
cap_z = top + 0.25
e3 = xy("E", 3); d6 = xy("D", 6)
ang = math.degrees(math.atan2(d6[1] - e3[1], d6[0] - e3[0]))
cap_body = Box(3.6, 2.4, 1.4).move(Location(((e3[0] + d6[0]) / 2, (e3[1] + d6[1]) / 2, cap_z + 0.7), (0, 0, ang)))
dirv = Vector(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)
mid = Vector((e3[0] + d6[0]) / 2, (e3[1] + d6[1]) / 2, cap_z + 0.3)
endA = mid - dirv * 1.8; endB = mid + dirv * 1.8
cap = cap_body + seg((e3[0], e3[1], cap_z + 0.3), endA, lead_r) + seg(endB, (d6[0], d6[1], cap_z + 0.3), lead_r)
for c in (e3, d6):
    cap += seg((c[0], c[1], bot - 1.0), (c[0], c[1], cap_z + 0.3 + lead_r), lead_r)
show(cap, "cap_100nF")

# --- series resistor standing vertically: body over A5, lead loops to B5 ---
res_l = 6.3; res_d = 2.4
a5 = xy("A", 5); b5 = xy("B", 5)
res_z0 = top + 0.8
loop_z = res_z0 + res_l + 1.2
resistor = Cylinder(res_d / 2, res_l).move(Location((a5[0], a5[1], res_z0 + res_l / 2)))
resistor += seg((a5[0], a5[1], bot - 1.0), (a5[0], a5[1], loop_z), lead_r)
resistor += seg((a5[0], a5[1], loop_z), (b5[0], b5[1], loop_z), lead_r)
resistor += seg((b5[0], b5[1], loop_z), (b5[0], b5[1], bot - 1.0), lead_r)
show(resistor, "resistor")

# --- solder-side bridges (bare wire) ---
bz = bot - pad_t - 0.3
bridge_r = 0.3
bridge_pairs = [(("D", 2), ("H", 2)), (("F", 2), ("F", 3)),          # 5V rail
                (("C", 8), ("H", 8)), (("C", 6), ("C", 8)),          # GND rail
                (("E", 3), ("F", 3)), (("D", 6), ("C", 6)),          # decoupling
                (("C", 5), ("B", 5)), (("A", 5), ("A", 4))]          # data
bridges = Compound([seg(pt(a, bz), pt(b, bz), bridge_r) for a, b in bridge_pairs])
show(bridges, "bridges")

# --- off-board wires (stubs) ---
stub_len = 10.0
def wire(cell, od):
    x, y = xy(*cell)
    w = Cylinder(od / 2, stub_len).move(Location((x, y, top + stub_len / 2)))
    return w + seg((x, y, bot - 1.0), (x, y, top), 0.32)
wire_5v_ring = wire(("D", 2), 1.6); wire_5v_usb = wire(("H", 2), 1.6)
wire_gnd_ring = wire(("D", 8), 1.6); wire_gnd_usb = wire(("H", 8), 1.6)
wire_din = wire(("A", 4), 1.0)
for n, w in [("wire_ring_5v", wire_5v_ring), ("wire_usb_5v", wire_5v_usb), ("wire_ring_gnd", wire_gnd_ring),
             ("wire_usb_gnd", wire_gnd_usb), ("wire_ring_din", wire_din)]:
    show(w, n)

for a, b in [("cap", cap), ("res", resistor), ("din", wire_din), ("chip", chip)]:
    print(a, clearance(socket, b).get("status"), round(clearance(socket, b).get("clearance", 0), 2))
print("cap-chip", clearance(cap, chip).get("status"))
print("res-din", clearance(resistor, wire_din).get("status"), round(clearance(resistor, wire_din)["clearance"], 2))

cap_z = top
cap_body = Box(3.6, 2.4, 1.4).move(Location(((e3[0] + d6[0]) / 2, (e3[1] + d6[1]) / 2, cap_z + 0.75), (0, 0, ang)))
mid = Vector((e3[0] + d6[0]) / 2, (e3[1] + d6[1]) / 2, cap_z + 0.3)
endA = mid - dirv * 1.8; endB = mid + dirv * 1.8
cap = cap_body + seg((e3[0], e3[1], cap_z + 0.3), endA, lead_r) + seg(endB, (d6[0], d6[1], cap_z + 0.3), lead_r)
for c in (e3, d6):
    cap += seg((c[0], c[1], bot - 1.0), (c[0], c[1], cap_z + 0.3 + lead_r), lead_r)
show(cap, "cap_100nF")
print(clearance(socket, cap)["status"], clearance(board, cap)["status"])
# chip body (not legs) vs socket
print(clearance(socket, Box(chip_w, chip_l, chip_h).move(Location((scx, scy, chip_z0 + chip_h / 2))))["status"])

parts = {"board": board, "pads": pads, "socket": socket, "attiny85": chip, "cap_100nF": cap,
         "resistor": resistor, "bridges": bridges, "wire_ring_5v": wire_5v_ring, "wire_usb_5v": wire_5v_usb,
         "wire_ring_gnd": wire_gnd_ring, "wire_usb_gnd": wire_gnd_usb, "wire_ring_din": wire_din}
kids = []
for n, s in parts.items():
    s.label = n
    kids.append(s)
assembly = Compound(children=kids, label="candle_board")
show(assembly, "assembly")