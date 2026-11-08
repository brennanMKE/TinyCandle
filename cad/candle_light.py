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

print(list(parts.keys()))

# ================= WS2812B 8-LED ring =================
ring_od = 32.0; ring_id = 17.5; ring_t = 1.6
ring_gap = 24.0                     # board top -> ring underside
ring_z0 = top + ring_gap            # ring underside
led_r = 12.5; led_size = 5.0; led_h = 1.6
ring_hole_d = 2.0; ring_hole_r = 11.0; ring_hole_angles = (112.5, 292.5)
pad_r_y = -14.0                     # back pads, toward board rows 8-9 side
ring_pads_x = {"GND": -3.81, "5V": -1.27, "DIN": 1.27, "DOUT": 3.81}

ring_pcb = Cylinder(ring_od / 2, ring_t) - Cylinder(ring_id / 2, ring_t * 2)
for a in ring_hole_angles:
    ring_pcb -= Cylinder(ring_hole_d / 2, ring_t * 2).move(Location((ring_hole_r * math.cos(math.radians(a)), ring_hole_r * math.sin(math.radians(a)), 0)))
ring_pcb = ring_pcb.move(Location((0, 0, ring_z0 + ring_t / 2)))
show(ring_pcb, "ring_pcb")

leds = []; lenses = []; ring_caps = []
for k in range(8):
    a = 90 + 45 * k
    c = (led_r * math.cos(math.radians(a)), led_r * math.sin(math.radians(a)))
    leds.append(Box(led_size, led_size, led_h).move(Location((c[0], c[1], ring_z0 + ring_t + led_h / 2), (0, 0, a))))
    lenses.append(Cylinder(1.8, 0.1).move(Location((c[0], c[1], ring_z0 + ring_t + led_h + 0.05))))
    b = a + 22.5
    ring_caps.append(Box(1.6, 0.8, 0.8).move(Location((14.6 * math.cos(math.radians(b)), 14.6 * math.sin(math.radians(b)), ring_z0 + ring_t + 0.4), (0, 0, b + 90))))
ring_leds = Compound(leds); show(ring_leds, "ring_leds")
ring_lenses = Compound(lenses); show(ring_lenses, "ring_lenses")
ring_smd_caps = Compound(ring_caps); show(ring_smd_caps, "ring_smd_caps")
ring_back_pads = Compound([Box(1.8, 1.6, 0.05).move(Location((x, pad_r_y, ring_z0 - 0.025))) for x in ring_pads_x.values()])
show(ring_back_pads, "ring_back_pads")
print(clearance(ring_pcb, Compound(ring_caps))["status"])

def polywire(points, r):
    s = None
    for p1, p2 in zip(points[:-1], points[1:]):
        c = seg(p1, p2, r)
        s = c if s is None else s + c
    for p in points[1:-1]:
        s = s + Sphere(r).move(Location(p))
    return s

def routed(cell, pad_xy, z_route, od):
    x, y = xy(*cell)
    pts = [(x, y, top), (x, y, z_route), (pad_xy[0], pad_xy[1], z_route), (pad_xy[0], pad_xy[1], ring_z0 - 0.05)]
    w = polywire(pts, od / 2)
    return w + seg((x, y, bot - 1.0), (x, y, top + 0.01), 0.32)

wire_ring_gnd = routed(("D", 8), (ring_pads_x["GND"], pad_r_y), 10.8, 1.6)
wire_ring_5v  = routed(("D", 2), (ring_pads_x["5V"], pad_r_y), 12.6, 1.6)
wire_ring_din = routed(("A", 4), (ring_pads_x["DIN"], pad_r_y), 14.4, 1.0)
show(wire_ring_gnd, "wire_ring_gnd"); show(wire_ring_5v, "wire_ring_5v"); show(wire_ring_din, "wire_ring_din")

# bulk electrolytic laid on its side under the ring, leads to 5V / GND pads
bulk_d = 6.3; bulk_l = 11.0
bulk_y = -8.8; bulk_x = -4.0
bulk_zc = ring_z0 - bulk_d / 2 - 0.2
bulk_cap = Cylinder(bulk_d / 2, bulk_l).move(Location((bulk_x, bulk_y, bulk_zc), (0, 90, 0)))
lead_end_x = bulk_x - bulk_l / 2
for px in (ring_pads_x["GND"], ring_pads_x["5V"]):
    pass
bulk_leads = polywire([(lead_end_x, bulk_y + 1.2, bulk_zc), (lead_end_x - 1.0, bulk_y + 1.2, bulk_zc), (lead_end_x - 1.0, pad_r_y + 0.6, ring_z0 - 0.5), (ring_pads_x["GND"], pad_r_y + 0.6, ring_z0 - 0.3)], 0.3)
bulk_leads += polywire([(lead_end_x, bulk_y - 1.2, bulk_zc), (lead_end_x - 0.3, pad_r_y + 0.6 - 0.2, ring_z0 - 1.6), (ring_pads_x["5V"], pad_r_y + 0.3, ring_z0 - 1.6), (ring_pads_x["5V"], pad_r_y + 0.3, ring_z0 - 0.3)], 0.3)
show(bulk_cap, "bulk_cap"); show(bulk_leads, "bulk_cap_leads")

for n, s in [("gnd", wire_ring_gnd), ("5v", wire_ring_5v), ("din", wire_ring_din), ("bulk", bulk_cap)]:
    for m, t in [("chip", chip), ("res", resistor), ("socket", socket), ("ring", ring_pcb)]:
        st = clearance(s, t)["status"]
        if st == "interpenetrating": print("HIT", n, m)
for a_, b_ in [("gnd", "5v"), ("gnd", "din"), ("5v", "din")]:
    d_ = {"gnd": wire_ring_gnd, "5v": wire_ring_5v, "din": wire_ring_din}
    print(a_, b_, clearance(d_[a_], d_[b_])["status"])
for n, s in [("gnd", wire_ring_gnd), ("5v", wire_ring_5v), ("din", wire_ring_din)]:
    print("bulk", n, clearance(bulk_cap, s)["status"])

# ================= mount, USB cable, jar (PLACEHOLDER jar dims) =================
standoff_h = 6.0; standoff_d = 4.2
z_lid = bot - standoff_h            # lid inner (upward) surface
mxy = (mx, my)
standoff = Cylinder(standoff_d / 2, standoff_h).move(Location((mx, my, bot - standoff_h / 2)))
screw = (Cylinder(2.7, 1.8).move(Location((mx, my, top + 0.9)))
         + Cylinder(1.25, standoff_h + board_t + 2.0 + 1.6 + 2.4).move(Location((mx, my, (top + 1.8 + z_lid - 2.4 - 0.8) / 2)))
         + Cylinder(2.9, 2.0, ).move(Location((mx, my, z_lid - 0.5 - 1.0))))
show(standoff, "standoff"); show(screw, "screw_m2_5")

# USB power lead: two wires drop off the board edge into one cable through the lid
cable_xy = (16.0, 0.0); cable_d = 3.5
cable_top = z_lid + 4.0
usb_cable = Cylinder(cable_d / 2, cable_top - (z_lid - 25)).move(Location((cable_xy[0], cable_xy[1], (cable_top + z_lid - 25) / 2)))
def usb_wire(cell, dy):
    x, y = xy(*cell)
    return polywire([(x, y, top), (x, y, top + 2.5), (cable_xy[0] - 0.6, dy, top + 2.5), (cable_xy[0] - 0.6, dy, cable_top - 0.1)], 0.8) \
        + seg((x, y, bot - 1.0), (x, y, top + 0.01), 0.32)
wire_usb_5v = usb_wire(("H", 2), 0.9); wire_usb_gnd = usb_wire(("H", 8), -0.9)
show(usb_cable, "usb_cable"); show(wire_usb_5v, "wire_usb_5v"); show(wire_usb_gnd, "wire_usb_gnd")

# lid used as the base, jar inverted over the light
lid_od = 63.0; lid_h = 9.0; lid_t = 0.6
lid = Cylinder(lid_od / 2, lid_h).move(Location((0, 0, z_lid - lid_t + lid_h / 2))) \
    - Cylinder(lid_od / 2 - lid_t, lid_h).move(Location((0, 0, z_lid + lid_h / 2)))
lid -= Cylinder(2.0, 5).move(Location((cable_xy[0], cable_xy[1], z_lid)))
lid -= Cylinder(1.4, 5).move(Location((mx, my, z_lid)))
show(lid, "jar_lid")

jar_od = 66.0; jar_h = 85.0; jar_wall = 2.5; neck_od = 61.0; neck_h = 12.0
jz0 = z_lid + 0.5
with BuildPart() as jp:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline((neck_od / 2, jz0), (neck_od / 2, jz0 + neck_h), (jar_od / 2, jz0 + neck_h + 6),
                     (jar_od / 2, jz0 + jar_h), (0, jz0 + jar_h), (0, jz0 + jar_h - jar_wall),
                     (jar_od / 2 - jar_wall, jz0 + jar_h - jar_wall), (jar_od / 2 - jar_wall, jz0 + neck_h + 6),
                     (neck_od / 2 - jar_wall, jz0 + neck_h), (neck_od / 2 - jar_wall, jz0), close=True)
        make_face()
    revolve(axis=Axis.Z)
jar = jp.part
show(jar, "jar")
print(clearance(jar, ring_pcb)["clearance"], clearance(lid, standoff)["status"], clearance(usb_cable, board)["status"])
print(clearance(wire_usb_5v, wire_usb_gnd)["status"], clearance(standoff, bridges)["status"], clearance(bulk_leads, wire_ring_5v)["status"])

parts = {"board": board, "pads": pads, "socket": socket, "attiny85": chip, "cap_100nF": cap,
         "resistor": resistor, "bridges": bridges, "wire_ring_5v": wire_ring_5v, "wire_usb_5v": wire_usb_5v,
         "wire_ring_gnd": wire_ring_gnd, "wire_usb_gnd": wire_usb_gnd, "wire_ring_din": wire_ring_din,
         "ring_pcb": ring_pcb, "ring_leds": ring_leds, "ring_lenses": ring_lenses, "ring_smd_caps": ring_smd_caps,
         "ring_back_pads": ring_back_pads, "bulk_cap": bulk_cap, "bulk_cap_leads": bulk_leads,
         "standoff": standoff, "screw_m2_5": screw, "usb_cable": usb_cable, "jar_lid": lid, "jar": jar}
kids = []
for n, s in parts.items():
    s.label = n; kids.append(s)
assembly = Compound(children=kids, label="candle_light")
show(assembly, "assembly")
light = Compound(children=[s for n, s in parts.items() if n not in ("jar",)])
show(light, "light_only")

import copy as _c
def mk(names, label):
    ks = []
    for n in names:
        s = parts[n].moved(Location()); s.label = n; ks.append(s)
    return Compound(children=ks, label=label)
assembly = mk(list(parts), "candle_light"); show(assembly, "assembly")
light = mk([n for n in parts if n != "jar"], "light_only"); show(light, "light_only")

# ===== revision: bulk cap on the protoboard, ring centred over the ATtiny85 =====
# bulk cap: 470uF 6.3V, 6.3 x 7.7, laid flat over columns H-I, leads in H7 (-) and I7 (+)
bulk_d = 6.3; bulk_l = 7.7; bulk_bend = 1.0
h7 = xy("H", 7); i7 = xy("I", 7)
bulk_x = (h7[0] + i7[0]) / 2
bulk_y0 = h7[1] + bulk_bend                  # lead end of the body
bulk_zc = top + bulk_d / 2 + 0.05
bulk_cap = Cylinder(bulk_d / 2, bulk_l).move(Location((bulk_x, bulk_y0 + bulk_l / 2, bulk_zc), (-90, 0, 0)))
bulk_cap -= Box(bulk_d, 0.6, 0.3).move(Location((bulk_x - 1.6, bulk_y0 + bulk_l / 2, bulk_zc + bulk_d / 2), (0, 0, 90)))  # minus stripe groove (cosmetic)
bulk_leads = None
for (cx, cy) in (h7, i7):
    l = polywire([(cx, cy, bot - 1.0), (cx, cy, bulk_zc + (0.9 if cx == h7[0] else -0.9) * 0), (cx, bulk_y0 + 0.2, bulk_zc)], 0.3)
    bulk_leads = l if bulk_leads is None else bulk_leads + l
show(bulk_cap, "bulk_cap"); show(bulk_leads, "bulk_cap_leads")

bridge_pairs = [(("D", 2), ("H", 2)), (("F", 2), ("F", 3)),
                (("C", 8), ("H", 8)), (("C", 6), ("C", 8)),
                (("E", 3), ("F", 3)), (("D", 6), ("C", 6)),
                (("C", 5), ("B", 5)), (("A", 5), ("A", 4)),
                (("H", 7), ("H", 8)),                       # bulk cap - to GND rail
                (("I", 7), ("I", 2)), (("I", 2), ("H", 2))] # bulk cap + to 5V rail
bridges = Compound([seg(pt(a, bz), pt(b, bz), bridge_r) for a, b in bridge_pairs])
show(bridges, "bridges")
for n, s in [("socket", socket), ("chip", chip), ("res", resistor)]:
    print(n, clearance(bulk_cap, s)["status"])

print(bulk_cap.bounding_box())
ring_c = (scx, scy)                      # ring centred over the ATtiny85
ring_gap = 16.0
ring_z0 = top + ring_gap
def P(x, y): return (ring_c[0] + x, ring_c[1] + y)

ring_pcb = Cylinder(ring_od / 2, ring_t) - Cylinder(ring_id / 2, ring_t * 2)
for a in ring_hole_angles:
    ring_pcb -= Cylinder(ring_hole_d / 2, ring_t * 2).move(Location((ring_hole_r * math.cos(math.radians(a)), ring_hole_r * math.sin(math.radians(a)), 0)))
ring_pcb = ring_pcb.move(Location((ring_c[0], ring_c[1], ring_z0 + ring_t / 2)))
leds = []; lenses = []; ring_caps = []
for k in range(8):
    a = 90 + 45 * k
    c = P(led_r * math.cos(math.radians(a)), led_r * math.sin(math.radians(a)))
    leds.append(Box(led_size, led_size, led_h).move(Location((c[0], c[1], ring_z0 + ring_t + led_h / 2), (0, 0, a))))
    lenses.append(Cylinder(1.8, 0.1).move(Location((c[0], c[1], ring_z0 + ring_t + led_h + 0.05))))
    b = a + 22.5
    cc = P(14.6 * math.cos(math.radians(b)), 14.6 * math.sin(math.radians(b)))
    ring_caps.append(Box(1.6, 0.8, 0.8).move(Location((cc[0], cc[1], ring_z0 + ring_t + 0.4), (0, 0, b + 90))))
ring_leds = Compound(leds); ring_lenses = Compound(lenses); ring_smd_caps = Compound(ring_caps)
pad_xy = {k: P(v, pad_r_y) for k, v in ring_pads_x.items()}
ring_back_pads = Compound([Box(1.8, 1.6, 0.05).move(Location((x, y, ring_z0 - 0.025))) for x, y in pad_xy.values()])
for n, s in [("ring_pcb", ring_pcb), ("ring_leds", ring_leds), ("ring_lenses", ring_lenses), ("ring_smd_caps", ring_smd_caps), ("ring_back_pads", ring_back_pads)]:
    show(s, n)

wire_ring_gnd = routed(("D", 8), pad_xy["GND"], 10.6, 1.6)
wire_ring_5v  = routed(("D", 2), pad_xy["5V"], 12.4, 1.6)
wire_ring_din = routed(("A", 4), pad_xy["DIN"], 14.4, 1.0)
show(wire_ring_gnd, "wire_ring_gnd"); show(wire_ring_5v, "wire_ring_5v"); show(wire_ring_din, "wire_ring_din")

# USB leads now drop out the solder side straight to the cable through the lid
cable_top = z_lid + 1.5
usb_cable = Cylinder(cable_d / 2, cable_top - (z_lid - 25)).move(Location((cable_xy[0], cable_xy[1], (cable_top + z_lid - 25) / 2)))
usb_z = z_lid + 2.6
def usb_wire(cell, dy):
    x, y = xy(*cell)
    return polywire([(x, y, top + 0.6), (x, y, usb_z), (cable_xy[0] - 0.6, dy, usb_z), (cable_xy[0] - 0.6, dy, cable_top - 0.1)], 0.8)
wire_usb_5v = usb_wire(("H", 2), 0.9); wire_usb_gnd = usb_wire(("H", 8), -0.9)
show(usb_cable, "usb_cable"); show(wire_usb_5v, "wire_usb_5v"); show(wire_usb_gnd, "wire_usb_gnd")

ring_wires = {"gnd": wire_ring_gnd, "5v": wire_ring_5v, "din": wire_ring_din}
others = {"chip": chip, "res": resistor, "socket": socket, "bulk": bulk_cap, "bulk_leads": bulk_leads, "ring": ring_pcb, "cap": cap}
for n, s in ring_wires.items():
    for m, t in others.items():
        if clearance(s, t)["status"] == "interpenetrating": print("HIT", n, m)
for a_, b_ in [("gnd", "5v"), ("gnd", "din"), ("5v", "din")]:
    print(a_, b_, clearance(ring_wires[a_], ring_wires[b_])["status"])
for n, s in [("usb5", wire_usb_5v), ("usbg", wire_usb_gnd)]:
    for m, t in [("standoff", standoff), ("lid", lid), ("screw", screw), ("socket", socket), ("bulk_leads", bulk_leads)]:
        if clearance(s, t)["status"] == "interpenetrating": print("HIT", n, m)
print("ring-chip gap", round(clearance(ring_pcb, chip)["clearance"], 2), "ring-jar", round(clearance(ring_pcb, jar)["clearance"], 2))

# ===== accurate machined-pin DIP-8 socket + DIP-8 legs =====
sock_standoff = 0.5      # moulded feet
frame_h = 3.0
collar_h = 0.35; collar_od = 1.9; contact_id = 1.0
tail_d = 0.5; tail_len = 3.2
frame_z0 = top + sock_standoff
frame_top = frame_z0 + frame_h
pin_xy = {}
for n_ in range(1, 9):
    if n_ <= 4: pin_xy[n_] = xy("C", 2 + n_)
    else: pin_xy[n_] = xy("F", 11 - n_)

sock = Box(sock_w, sock_len, frame_h)
sock -= Box(sock_w - 2 * rail_w, win_y, frame_h * 2)                        # open centre window
sock -= Box(2.0, 1.2, frame_h * 2).move(Location((0, sock_len / 2, 0)))      # pin-1 end notch
sock -= Box(sock_w - 2 * rail_w, sock_len, 1.2).move(Location((0, 0, -frame_h / 2)))  # relief under end bars
sock = sock.move(Location((scx, scy, frame_z0 + frame_h / 2)))
for fx in (-1, 1):
    for fy in (-1, 1):
        sock += Box(1.2, 1.2, sock_standoff + 0.05).move(Location((scx + fx * (sock_w / 2 - 0.6), scy + fy * (sock_len / 2 - 0.6), top + (sock_standoff + 0.05) / 2)))
contacts = []
for (x, y) in pin_xy.values():
    sock -= Cylinder(collar_od / 2, frame_h * 2).move(Location((x, y, frame_z0)))
    sleeve = Cylinder(collar_od / 2, frame_h + collar_h).move(Location((x, y, frame_z0 + (frame_h + collar_h) / 2)))
    sleeve -= Cylinder(contact_id / 2, frame_h * 3).move(Location((x, y, frame_z0 + frame_h)))
    sleeve -= Cone(contact_id / 2, collar_od / 2 - 0.2, 0.3).move(Location((x, y, frame_top + collar_h - 0.15)))
    tail = Cylinder(tail_d / 2, tail_len + sock_standoff + board_t).move(Location((x, y, frame_z0 - (tail_len + sock_standoff + board_t) / 2 + 0.01)))
    contacts.append(sleeve + tail)
socket = sock
socket_contacts = Compound(contacts)
show(socket, "socket"); show(socket_contacts, "socket_contacts")

# DIP-8 body + legs
chip_z0 = frame_top + collar_h + 0.5
chip_body = Box(chip_w, chip_l, chip_h)
chip_body = chamfer(chip_body.edges().group_by(Axis.Z)[-1], 0.3)
chip_body -= Cylinder(0.75, 1.0).move(Location((0, chip_l / 2, chip_h / 2)))
chip_body -= Cylinder(0.45, 0.3).move(Location((-chip_w / 2 + 1.2, chip_l / 2 - 1.3, chip_h / 2)))
chip_body = chip_body.move(Location((scx, scy, chip_z0 + chip_h / 2)))
legs = []
leg_t = 0.25; shoulder_w = 1.5; tip_w = 0.46; shoulder_drop = 1.1; tip_len = 3.0
leg_z = chip_z0 + chip_h * 0.4
for n_, (x, y) in pin_xy.items():
    sgn = -1 if n_ <= 4 else 1
    body_edge = scx + sgn * chip_w / 2
    legs.append(Box(abs(x - body_edge) + leg_t / 2 + 0.1, shoulder_w, leg_t).move(Location(((body_edge + x) / 2 - sgn * 0.05, y, leg_z))))
    sh_len = leg_z - (chip_z0 - shoulder_drop)
    legs.append(Box(leg_t, shoulder_w, sh_len).move(Location((x, y, leg_z - sh_len / 2 + leg_t / 2))))
    legs.append(Box(leg_t, tip_w, tip_len).move(Location((x, y, chip_z0 - shoulder_drop - tip_len / 2 + 0.01))))
chip = chip_body + Compound(legs)
show(chip, "attiny85")
print("chip-socket", clearance(chip, socket)["status"], "| cap-socket", clearance(cap, socket)["status"],
      "| shoulders above collar:", round(chip_z0 - shoulder_drop - (frame_top + collar_h), 2))
print("ring-chip gap", round(clearance(ring_pcb, chip)["clearance"], 2))

shoulder_drop = chip_z0 - (frame_top + collar_h) - 0.02    # shoulders rest on the contact collars
legs = []
for n_, (x, y) in pin_xy.items():
    sgn = -1 if n_ <= 4 else 1
    body_edge = scx + sgn * chip_w / 2
    legs.append(Box(abs(x - body_edge) + leg_t / 2 + 0.1, shoulder_w, leg_t).move(Location(((body_edge + x) / 2 - sgn * 0.05, y, leg_z))))
    sh_len = leg_z - (chip_z0 - shoulder_drop)
    legs.append(Box(leg_t, shoulder_w, sh_len).move(Location((x, y, leg_z - sh_len / 2 + leg_t / 2))))
    legs.append(Box(leg_t, tip_w, tip_len).move(Location((x, y, chip_z0 - shoulder_drop - tip_len / 2 + 0.01))))
chip = chip_body + Compound(legs)
show(chip, "attiny85")
print(clearance(chip, socket_contacts)["status"], clearance(chip, socket)["status"], clearance(socket_contacts, board)["status"])
closeup = Compound(children=[s.moved(Location()) for s in (board, socket, socket_contacts, chip, cap)])
show(closeup, "closeup")

parts.update({"socket": socket, "socket_contacts": socket_contacts, "attiny85": chip, "bulk_cap": bulk_cap, "bulk_cap_leads": bulk_leads,
              "bridges": bridges, "ring_pcb": ring_pcb, "ring_leds": ring_leds, "ring_lenses": ring_lenses, "ring_smd_caps": ring_smd_caps,
              "ring_back_pads": ring_back_pads, "wire_ring_5v": wire_ring_5v, "wire_ring_gnd": wire_ring_gnd, "wire_ring_din": wire_ring_din,
              "wire_usb_5v": wire_usb_5v, "wire_usb_gnd": wire_usb_gnd, "usb_cable": usb_cable})
for n, s in parts.items(): show(s, n)
assembly = mk(list(parts), "candle_light"); show(assembly, "assembly")

# ===== ring mount: rotate ring so its two holes sit over free grid holes G1 and B8, M2 x 16 F-F standoffs =====
g1 = xy("G", 1); b8 = xy("B", 8)
ring_c = ((g1[0] + b8[0]) / 2, (g1[1] + b8[1]) / 2)
print("ring centre", ring_c, "chip centre", (scx, scy))
ring_hole_r = math.hypot(g1[0] - ring_c[0], g1[1] - ring_c[1])
rot = math.degrees(math.atan2(g1[1] - ring_c[1], g1[0] - ring_c[0])) - 112.5
print("hole radius", round(ring_hole_r, 2), "rotation", round(rot, 2))

def R(x, y, deg=rot):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (ring_c[0] + x * c - y * s, ring_c[1] + x * s + y * c)

ring_pcb = Cylinder(ring_od / 2, ring_t) - Cylinder(ring_id / 2, ring_t * 2)
ring_pcb = ring_pcb.move(Location((ring_c[0], ring_c[1], ring_z0 + ring_t / 2)))
for hp in (g1, b8):
    ring_pcb -= Cylinder(ring_hole_d / 2, ring_t * 3).move(Location((hp[0], hp[1], ring_z0)))
leds = []; lenses = []; ring_caps = []
for k in range(8):
    a = 90 + 45 * k
    c = R(led_r * math.cos(math.radians(a)), led_r * math.sin(math.radians(a)))
    leds.append(Box(led_size, led_size, led_h).move(Location((c[0], c[1], ring_z0 + ring_t + led_h / 2), (0, 0, a + rot))))
    lenses.append(Cylinder(1.8, 0.1).move(Location((c[0], c[1], ring_z0 + ring_t + led_h + 0.05))))
    b = a + 22.5
    cc = R(14.6 * math.cos(math.radians(b)), 14.6 * math.sin(math.radians(b)))
    ring_caps.append(Box(1.6, 0.8, 0.8).move(Location((cc[0], cc[1], ring_z0 + ring_t + 0.4), (0, 0, b + 90 + rot))))
ring_leds = Compound(leds); ring_lenses = Compound(lenses); ring_smd_caps = Compound(ring_caps)
pad_xy = {k: R(v, pad_r_y) for k, v in ring_pads_x.items()}
ring_back_pads = Compound([Box(1.8, 1.6, 0.05).move(Location((x, y, ring_z0 - 0.025), (0, 0, rot))) for x, y in pad_xy.values()])
print({k: (round(v[0], 2), round(v[1], 2)) for k, v in pad_xy.items()})

# M2 x 16 mm female-female nylon hex standoffs, M2 x 5 screws top and bottom
so_len = ring_z0 - top; so_af = 4.0
def hexpost(p):
    with BuildPart() as hp_:
        with BuildSketch(Plane.XY.offset(top)):
            with Locations((p[0], p[1])):
                RegularPolygon(so_af / math.sqrt(3), 6)
                Circle(1.0, mode=Mode.SUBTRACT)
        extrude(amount=so_len)
    return hp_.part
ring_standoffs = Compound([hexpost(p) for p in (g1, b8)])
def m2screw(p, z_face, up):
    head = Cylinder(1.9, 1.3).move(Location((p[0], p[1], z_face + (0.65 if up else -0.65))))
    head -= Box(0.5, 2.6, 0.6).move(Location((p[0], p[1], z_face + (1.3 if up else -1.3))))
    shank = Cylinder(1.0, 5.0).move(Location((p[0], p[1], z_face + (-2.5 if up else 2.5))))
    return head + shank
ring_screws = Compound([m2screw(p, ring_z0 + ring_t, True) for p in (g1, b8)] + [m2screw(p, bot - pad_t, False) for p in (g1, b8)])
show(ring_pcb, "ring_pcb"); show(ring_leds, "ring_leds"); show(ring_lenses, "ring_lenses"); show(ring_smd_caps, "ring_smd_caps")
show(ring_back_pads, "ring_back_pads"); show(ring_standoffs, "ring_standoffs"); show(ring_screws, "ring_screws")

ring_gap = 15.0                          # = standoff length (common size)
ring_z0 = top + ring_gap
def build_ring():
    pcb = Cylinder(ring_od / 2, ring_t) - Cylinder(ring_id / 2, ring_t * 2)
    pcb = pcb.move(Location((ring_c[0], ring_c[1], ring_z0 + ring_t / 2)))
    for hp in (g1, b8):
        pcb -= Cylinder(ring_hole_d / 2, ring_t * 3).move(Location((hp[0], hp[1], ring_z0)))
    L = []; Ln = []; C = []
    for k in range(8):
        a = 90 + 45 * k
        c = R(led_r * math.cos(math.radians(a)), led_r * math.sin(math.radians(a)))
        L.append(Box(led_size, led_size, led_h).move(Location((c[0], c[1], ring_z0 + ring_t + led_h / 2), (0, 0, a + rot))))
        Ln.append(Cylinder(1.8, 0.1).move(Location((c[0], c[1], ring_z0 + ring_t + led_h + 0.05))))
        b = a + 22.5
        cc = R(14.6 * math.cos(math.radians(b)), 14.6 * math.sin(math.radians(b)))
        C.append(Box(1.6, 0.8, 0.8).move(Location((cc[0], cc[1], ring_z0 + ring_t + 0.4), (0, 0, b + 90 + rot))))
    pads_ = Compound([Box(1.8, 1.6, 0.05).move(Location((x, y, ring_z0 - 0.025), (0, 0, rot))) for x, y in pad_xy.values()])
    return pcb, Compound(L), Compound(Ln), Compound(C), pads_
ring_pcb, ring_leds, ring_lenses, ring_smd_caps, ring_back_pads = build_ring()

# M2 male-female nylon hex standoff (15 mm body + 6 mm male thread), nut under the board, M2 x 5 nylon screw on top
so_len = ring_gap; so_af = 4.0; thread_len = 6.0; nut_af = 4.0; nut_h = 1.6
drill_d = 2.2
board = board - Compound([Cylinder(drill_d / 2, board_t * 2).move(Location((p[0], p[1], 0))) for p in (g1, b8)])
pads = Compound([pad_ring.moved(Location((x, y, bot - pad_t / 2))) for x, y in keep if (x, y) not in (g1, b8)])
def hexprism(p, af, z0, h, hole_d=0):
    with BuildPart() as hp_:
        with BuildSketch(Plane.XY.offset(z0)):
            with Locations((p[0], p[1])):
                RegularPolygon(af / math.sqrt(3), 6, major_radius=True, rotation=30)
                if hole_d: Circle(hole_d / 2, mode=Mode.SUBTRACT)
        extrude(amount=h)
    return hp_.part
standoffs, nuts, scr = [], [], []
for p in (g1, b8):
    body = hexprism(p, so_af, top, so_len)
    body -= Cylinder(1.0, 5.0).move(Location((p[0], p[1], top + so_len - 2.5)))              # female thread at top
    body += Cylinder(1.0, thread_len).move(Location((p[0], p[1], top - thread_len / 2 + 0.01)))  # male thread down
    standoffs.append(body)
    nuts.append(hexprism(p, nut_af, bot - pad_t - nut_h, nut_h, 2.0))
    head = Cylinder(1.9, 1.3).move(Location((p[0], p[1], ring_z0 + ring_t + 0.65)))
    head -= Box(0.5, 4, 0.5).move(Location((p[0], p[1], ring_z0 + ring_t + 1.3), (0, 0, 30)))
    scr.append(head + Cylinder(1.0, 4.4).move(Location((p[0], p[1], ring_z0 + ring_t - 2.2))))
ring_standoffs = Compound(standoffs); ring_nuts = Compound(nuts); ring_screws = Compound(scr)
for n, s in [("board", board), ("pads", pads), ("ring_pcb", ring_pcb), ("ring_leds", ring_leds), ("ring_lenses", ring_lenses),
             ("ring_smd_caps", ring_smd_caps), ("ring_back_pads", ring_back_pads), ("ring_standoffs", ring_standoffs),
             ("ring_nuts", ring_nuts), ("ring_screws", ring_screws)]:
    show(s, n)
print("thread below nut:", round((top - thread_len) - (bot - pad_t - nut_h), 2))

import itertools
obst = {"chip": chip, "res": resistor, "socket": socket, "contacts": socket_contacts, "bulk": bulk_cap, "bulk_leads": bulk_leads,
        "ring": ring_pcb, "standoffs": ring_standoffs, "screws": ring_screws, "cap": cap}
src = {"GND": (("D", 8), 1.6), "5V": (("D", 2), 1.6), "DIN": (("A", 4), 1.0)}
best = None
for zs in itertools.permutations([10.0, 11.9, 13.8]):
    ws = {k: routed(src[k][0], pad_xy[k], z, src[k][1]) for k, z in zip(["GND", "5V", "DIN"], zs)}
    hits = [f"{k}-{m}" for k, w in ws.items() for m, o in obst.items() if clearance(w, o)["status"] == "interpenetrating"]
    hits += [f"{a}-{b}" for a, b in itertools.combinations(ws, 2) if clearance(ws[a], ws[b])["status"] == "interpenetrating"]
    print(zs, hits)
    if not hits and best is None: best = (zs, ws)

def routed_via(cell, via_xy, pad_xy_, z_route, od):
    x, y = xy(*cell)
    pts = [(x, y, top), (x, y, z_route), (via_xy[0], via_xy[1], z_route), (pad_xy_[0], pad_xy_[1], z_route), (pad_xy_[0], pad_xy_[1], ring_z0 - 0.05)]
    return polywire(pts, od / 2) + seg((x, y, bot - 1.0), (x, y, top + 0.01), 0.32)
wire_ring_gnd = routed_via(("D", 8), (xy("D", 8)[0], pad_xy["GND"][1]), pad_xy["GND"], 10.0, 1.6)
wire_ring_5v = routed(("D", 2), pad_xy["5V"], 11.9, 1.6)
wire_ring_din = routed(("A", 4), pad_xy["DIN"], 13.8, 1.0)
ws = {"GND": wire_ring_gnd, "5V": wire_ring_5v, "DIN": wire_ring_din}
obst.update({"nuts": ring_nuts, "usb5": wire_usb_5v, "usbg": wire_usb_gnd})
hits = [f"{k}-{m}" for k, w in ws.items() for m, o in obst.items() if clearance(w, o)["status"] == "interpenetrating"]
hits += [f"{a}-{b}" for a, b in itertools.combinations(ws, 2) if clearance(ws[a], ws[b])["status"] == "interpenetrating"]
for m, o in [("bridges", bridges), ("usb5", wire_usb_5v), ("usbg", wire_usb_gnd), ("lid_standoff", standoff), ("screw_m2_5", screw), ("socket", socket), ("contacts", socket_contacts), ("bulk", bulk_cap), ("leads", bulk_leads), ("res", resistor), ("cap", cap), ("chip", chip), ("ledpcb", ring_pcb)]:
    for n, s in [("standoffs", ring_standoffs), ("nuts", ring_nuts), ("screws", ring_screws)]:
        if clearance(s, o)["status"] == "interpenetrating": hits.append(f"{n}-{m}")
print("HITS:", hits)
print("ring underside to chip top:", round(ring_z0 - (chip_z0 + chip_h), 2), "| min standoff gap to socket:", round(clearance(ring_standoffs, socket)["clearance"], 2),
      "| nut to bridges:", round(clearance(ring_nuts, bridges)["clearance"], 2))
show(wire_ring_gnd, "wire_ring_gnd"); show(wire_ring_5v, "wire_ring_5v"); show(wire_ring_din, "wire_ring_din")

def nut(p):
    with BuildPart() as hp_:
        with BuildSketch(Plane.XY.offset(bot - pad_t - nut_h)):
            with Locations((p[0], p[1])):
                RegularPolygon(nut_af / math.sqrt(3), 6, rotation=0)
                Circle(1.0, mode=Mode.SUBTRACT)
        extrude(amount=nut_h)
    return hp_.part
ring_nuts = Compound([nut(p) for p in (g1, b8)])
print(ring_nuts.bounding_box())
print("nut-bridges", clearance(ring_nuts, bridges)["status"], round(clearance(ring_nuts, bridges)["clearance"], 2),
      "| nut-usb", clearance(ring_nuts, wire_usb_5v)["status"], "| nut-lid standoff", clearance(ring_nuts, standoff)["status"])
show(ring_nuts, "ring_nuts")

def nut(p, rotation):
    with BuildPart() as hp_:
        with BuildSketch(Plane.XY.offset(bot - pad_t - nut_h)):
            with Locations((p[0], p[1])):
                RegularPolygon(nut_af / math.sqrt(3), 6, rotation=rotation)
                Circle(1.0, mode=Mode.SUBTRACT)
        extrude(amount=nut_h)
    return hp_.part
ring_nuts = Compound([nut(g1, 0), nut(b8, 30)])
print("nut-bridges", round(clearance(ring_nuts, bridges)["clearance"], 2), clearance(ring_nuts, bridges)["status"])
show(ring_nuts, "ring_nuts")

print("screw-leds", round(clearance(ring_screws, ring_leds)["clearance"], 2), "screw-smd", round(clearance(ring_screws, ring_smd_caps)["clearance"], 2),
      "standoff-wires", min(round(clearance(ring_standoffs, w)["clearance"], 2) for w in ws.values()))
parts.update({"board": board, "pads": pads, "ring_pcb": ring_pcb, "ring_leds": ring_leds, "ring_lenses": ring_lenses, "ring_smd_caps": ring_smd_caps,
              "ring_back_pads": ring_back_pads, "ring_standoffs": ring_standoffs, "ring_nuts": ring_nuts, "ring_screws": ring_screws,
              "wire_ring_gnd": wire_ring_gnd, "wire_ring_5v": wire_ring_5v, "wire_ring_din": wire_ring_din})
for n, s in parts.items(): show(s, n)
assembly = mk(list(parts), "candle_light"); show(assembly, "assembly")
light = mk([n for n in parts if n not in ("jar", "jar_lid", "usb_cable", "standoff", "screw_m2_5")], "light_only"); show(light, "light_only")

probe = Cylinder(0.01, 0.5).move(Location((g1[0], g1[1], ring_z0 + ring_t + 0.8)))
print("hole centre to nearest LED body:", round(clearance(probe, ring_leds)["clearance"] + 0.01, 2), "mm")

head_d = 3.2   # fits the 1.68 mm radius between hole and LED in this (assumed) ring geometry
scr = []
for p in (g1, b8):
    head = Cylinder(head_d / 2, 1.3).move(Location((p[0], p[1], ring_z0 + ring_t + 0.65)))
    head -= Box(0.5, 4, 0.5).move(Location((p[0], p[1], ring_z0 + ring_t + 1.3), (0, 0, 30)))
    scr.append(head + Cylinder(1.0, 4.4).move(Location((p[0], p[1], ring_z0 + ring_t - 2.2))))
ring_screws = Compound(scr)
print("screw-leds", clearance(ring_screws, ring_leds)["status"], round(clearance(ring_screws, ring_leds)["clearance"], 2))
parts["ring_screws"] = ring_screws; show(ring_screws, "ring_screws")
assembly = mk(list(parts), "candle_light"); show(assembly, "assembly")
light = mk([n for n in parts if n not in ("jar", "jar_lid", "usb_cable", "standoff", "screw_m2_5")], "light_only"); show(light, "light_only")

print("ok")