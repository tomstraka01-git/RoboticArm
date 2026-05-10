import tkinter as tk
import serial
import time
import json
import math
from kinematicArm import RobotKinematics, Position

try:
    ser = serial.Serial('COM4', 115200, timeout=1)
    time.sleep(2)
except:
    ser = None

kin = RobotKinematics()
last_send_time = 0
root = tk.Tk()
root.title("Robotic Arm Controller")
root.geometry("800x820")

top_frame = tk.Frame(root)
top_frame.pack(pady=5)
serial_frame = tk.Frame(root, bd=1, relief="sunken")
serial_frame.pack(fill="x", padx=10, pady=2)
content_frame = tk.Frame(root)
content_frame.pack(pady=5)
record_frame = tk.Frame(root, bd=2, relief="groove")
record_frame.pack(pady=5, fill="x")

toggle_state = tk.BooleanVar(value=False)
widgets = []
slider_values = {}
recorded_values_position = []
recorded_values_angle = []
serial_message1 = serial_message2 = serial_message3 = serial_message4 = ""
fk_label_ref = None
last_recorded_time = 0.0
STEPS = 50


def write_serial_values(a, b, c, d, e):
    if ser:
        ser.write(f"{a} {b} {c} {d} {e}\n".encode())

def read_serial_message():
    global serial_message1, serial_message2, serial_message3, serial_message4
    if ser and ser.in_waiting:
        try:
            parts = ser.readline().decode().strip().split(",")
            if len(parts) >= 4:
                serial_message1, serial_message2, serial_message3, serial_message4 = parts[:4]
        except:
            pass
    serial_read_label1.config(text=f"MSG1: {serial_message1}")
    serial_read_label2.config(text=f"MSG2: {serial_message2}")
    serial_read_label3.config(text=f"MSG3: {serial_message3}")
    serial_read_label4.config(text=f"MSG4: {serial_message4}")

def flush_serial():
    global serial_message1, serial_message2, serial_message3, serial_message4
    serial_message1 = serial_message2 = serial_message3 = serial_message4 = ""
    serial_read_label1.config(text="MSG1: ")
    serial_read_label2.config(text="MSG2: ")
    serial_read_label3.config(text="MSG3: ")
    serial_read_label4.config(text="MSG4: ")

def update_fk_label():
    if fk_label_ref is None or toggle_state.get():
        return
    pos = kin.solve_fk(
        slider_values["Base Servo"].get(),
        slider_values["Shoulder Servo"].get(),
        slider_values["Elbow Servo"].get(),
        slider_values["Phi Servo"].get()
    )
    fk_label_ref.config(text=f"X: {pos.x:.1f}  Y: {pos.y:.1f}  Z: {pos.z:.1f}")

def clear_widgets():
    global widgets, fk_label_ref
    for w in widgets:
        w.destroy()
    widgets = []
    fk_label_ref = None

def create_slider(name, ik_mode):
    frame = tk.Frame(content_frame)
    frame.pack(fill="x", padx=10, pady=1)
    tk.Label(frame, text=name, font=("Arial", 13), width=16, anchor="w").pack(side="left")
    var = tk.IntVar(value=100 if ik_mode else 90)
    slider_values[name] = var
    val_label = tk.Label(frame, text=str(var.get()), width=4)
    val_label.pack(side="right")
    last_send = [0]
    def on_slide(val):
        val_label.config(text=val)
        update_fk_label()
        now = time.time()
        if now - last_send[0] > 0.1:
            read_robot_state()
            last_send[0] = now
    slider = tk.Scale(frame, from_=50 if ik_mode else 0, to=200 if ik_mode else 180,
                  orient="horizontal", length=400, variable=var, command=on_slide, showvalue=0)
    slider.pack(side="left", padx=5)
    widgets.append(frame)

def show_position_mode():
    clear_widgets()
    for name in ["X Position", "Y Position", "Z Position", "Phi Angle", "Gripper Servo"]:
        create_slider(name, 1)

def show_angle_mode():
    global fk_label_ref
    clear_widgets()
    for name in ["Base Servo", "Shoulder Servo", "Elbow Servo", "Phi Servo", "Gripper Servo"]:
        create_slider(name, 0)
    fk_label_ref = tk.Label(content_frame, text="FK -> X: -  Y: -  Z: -", font=("Arial", 10))
    fk_label_ref.pack(pady=2)
    widgets.append(fk_label_ref)
    update_fk_label()

def update_mode():
    if toggle_state.get():
        toggle_button.config(text="Mode: POSITION")
        show_position_mode()
    else:
        toggle_button.config(text="Mode: ANGLES")
        show_angle_mode()

def record_position():
    global last_recorded_time
    if not toggle_state.get():
        return
    t = float(time_input.get())
    if t < last_recorded_time:
        time_input_label.config(text=f"t >= {last_recorded_time}")
        return
    last_recorded_time = t
    x, y, z = slider_values["X Position"].get(), slider_values["Y Position"].get(), slider_values["Z Position"].get()
    phi, grip = slider_values["Phi Angle"].get(), slider_values["Gripper Servo"].get()
    recorded_values_position.append((x, y, z, phi, grip, t))
    record_listbox.insert(tk.END, f"X:{x} Y:{y} Z:{z} P:{phi} G:{grip} T:{t}")

def record_angles():
    global last_recorded_time
    if toggle_state.get():
        return
    t = float(time_input.get())
    if t < last_recorded_time:
        time_input_label.config(text=f"t >= {last_recorded_time}")
        return
    last_recorded_time = t
    b = slider_values["Base Servo"].get()
    s = slider_values["Shoulder Servo"].get()
    e = slider_values["Elbow Servo"].get()
    p = slider_values["Phi Servo"].get()
    g = slider_values["Gripper Servo"].get()
    recorded_values_angle.append((b, s, e, p, g, t))
    record_listbox.insert(tk.END, f"B:{b} S:{s} E:{e} P:{p} G:{g} T:{t}")

def clear_records():
    global last_recorded_time
    recorded_values_position.clear()
    recorded_values_angle.clear()
    record_listbox.delete(0, tk.END)
    last_recorded_time = 0.0

def save_animation():
    data = {"mode": "ik", "sequence": recorded_values_position} if toggle_state.get() \
           else {"mode": "angles", "sequence": recorded_values_angle}
    with open("animation.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Animation saved")

def load_animation():
    global recorded_values_position, recorded_values_angle, last_recorded_time
    try:
        with open("animation.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("No saved animation found")
        return
    record_listbox.delete(0, tk.END)
    last_recorded_time = 0.0
    if data["mode"] == "ik":
        recorded_values_position = [tuple(kf) for kf in data["sequence"]]
        toggle_state.set(True)
        update_mode()
        for x, y, z, phi, grip, t in recorded_values_position:
            record_listbox.insert(tk.END, f"X:{x} Y:{y} Z:{z} P:{phi} G:{grip} T:{t}")
    else:
        recorded_values_angle = [tuple(kf) for kf in data["sequence"]]
        toggle_state.set(False)
        update_mode()
        for b, s, e, p, g, t in recorded_values_angle:
            record_listbox.insert(tk.END, f"B:{b} S:{s} E:{e} P:{p} G:{g} T:{t}")
    print("Animation loaded")

def cosine_ease(a, b, t):
    return a + (b - a) * (1 - math.cos(t * math.pi)) / 2

def animate():
    sequence = recorded_values_position if toggle_state.get() else recorded_values_angle
    keys = ["X Position", "Y Position", "Z Position", "Phi Angle", "Gripper Servo"] \
           if toggle_state.get() else \
           ["Base Servo", "Shoulder Servo", "Elbow Servo", "Phi Servo", "Gripper Servo"]
    if not sequence:
        print("No data recorded")
        return

    def play_segment(seg_index=0, step=0):
        if seg_index >= len(sequence) - 1:
            final = sequence[-1]
            for i, key in enumerate(keys):
                slider_values[key].set(int(final[i]))
            if toggle_state.get():
                angles = kin.solve_ik(x=int(final[0]), y=int(final[1]), z=int(final[2]), phi_deg=int(final[3]))
                if angles:
                    write_serial_values(*angles, int(final[4]))
            else:
                write_serial_values(*[int(final[i]) for i in range(5)])
                update_fk_label()
            print("Animation finished")
            return

        start_kf, end_kf = sequence[seg_index], sequence[seg_index + 1]
        step_delay_ms = max(1, int((end_kf[5] - start_kf[5]) / STEPS * 1000))
        t = step / STEPS
        interpolated = [int(cosine_ease(start_kf[i], end_kf[i], t)) for i in range(5)]

        for i, key in enumerate(keys):
            slider_values[key].set(interpolated[i])

        if toggle_state.get():
            angles = kin.solve_ik(x=interpolated[0], y=interpolated[1], z=interpolated[2], phi_deg=interpolated[3])
            if angles:
                write_serial_values(*angles, interpolated[4])
        else:
            write_serial_values(*interpolated)
            update_fk_label()

        if step < STEPS - 1:
            root.after(step_delay_ms, lambda: play_segment(seg_index, step + 1))
        else:
            root.after(step_delay_ms, lambda: play_segment(seg_index + 1, 0))

    play_segment()

def read_robot_state():
    global last_send_time
    now = time.time()
    if now - last_send_time < 0.1:
        return
    last_send_time = now
    if toggle_state.get():
        angles = kin.solve_ik(
            x=slider_values["X Position"].get(), y=slider_values["Y Position"].get(),
            z=slider_values["Z Position"].get(), phi_deg=slider_values["Phi Angle"].get()
        )
        if angles:
            write_serial_values(*angles, slider_values["Gripper Servo"].get())
        else:
            print("Not reachable")
    else:
        write_serial_values(
            slider_values["Base Servo"].get(), slider_values["Shoulder Servo"].get(),
            slider_values["Elbow Servo"].get(), slider_values["Phi Servo"].get(),
            slider_values["Gripper Servo"].get()
        )

def loop():
    read_serial_message()
    root.after(100, loop)


toggle_button = tk.Checkbutton(top_frame, text="Mode: ANGLES", variable=toggle_state, command=update_mode)
toggle_button.pack(side="left", padx=10)

flush_btn = tk.Button(top_frame, text="Flush Serial", command=flush_serial)
flush_btn.pack(side="left", padx=5)

serial_row1 = tk.Frame(serial_frame)
serial_row1.pack(fill="x", padx=6, pady=1)
serial_row2 = tk.Frame(serial_frame)
serial_row2.pack(fill="x", padx=6, pady=1)

serial_read_label1 = tk.Label(serial_row1, text="MSG1: ", font=("Courier", 10), anchor="w", width=35)
serial_read_label1.pack(side="left")
serial_read_label2 = tk.Label(serial_row1, text="MSG2: ", font=("Courier", 10), anchor="w")
serial_read_label2.pack(side="left")
serial_read_label3 = tk.Label(serial_row2, text="MSG3: ", font=("Courier", 10), anchor="w", width=35)
serial_read_label3.pack(side="left")
serial_read_label4 = tk.Label(serial_row2, text="MSG4: ", font=("Courier", 10), anchor="w")
serial_read_label4.pack(side="left")

record_label = tk.Label(record_frame, text="Recorded Keyframes", font=("Arial", 10, "bold"))
record_label.pack()

record_listbox = tk.Listbox(record_frame, height=4, font=("Courier", 9))
record_listbox.pack(fill="x", padx=10)

btn_frame = tk.Frame(record_frame)
btn_frame.pack(pady=3)

time_row = tk.Frame(record_frame)
time_row.pack(pady=2)
time_input_label = tk.Label(time_row, text="Time (s):")
time_input_label.pack(side="left")
time_input_var = tk.StringVar(value="0.0")
time_input = tk.Entry(time_row, textvariable=time_input_var, width=6)
time_input.pack(side="left", padx=4)

for text, cmd in [("Rec Pos", record_position), ("Rec Ang", record_angles),
                  ("Clear", clear_records), ("Animate", animate),
                  ("Save", save_animation), ("Load", load_animation)]:
    tk.Button(btn_frame, text=text, command=cmd, width=7).pack(side="left", padx=3)

def on_key(event):
    global time_input_var
    
    print(event.keysym)  
    
    match event.keysym:
        case "q":
            if ser:
                ser.close()
            root.destroy()

        case "r":
            record_angles()
            record_position()

        case "space":

            animate()

        case "t":
            
            current = float(time_input_var.get())
            time_input_var.set(str(current + 0.5))

        case "l":
            load_animation()

        case "s":
            save_animation()
    

root.bind("<KeyPress>", on_key)



show_angle_mode()
loop()
root.mainloop()