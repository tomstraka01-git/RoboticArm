import tkinter as tk
import serial
import time
import json

try:
    ser = serial.Serial('COM4', 115200, timeout=1)
    time.sleep(2)
except:
    ser = None


last_send_time = 0

root = tk.Tk()
root.title("Robotic Arm Controller")
root.geometry("800x1000")

top_frame = tk.Frame(root)
top_frame.pack(pady=10)

content_frame = tk.Frame(root)
content_frame.pack(pady=20)

record_frame = tk.Frame(root, bd=2, relief="groove")
record_frame.pack(pady=20, fill="x")


toggle_state = tk.BooleanVar(value=False)
ik_mode_on = False

widgets = []
slider_values = {}

recorded_values_position = []
recorded_values_angle = []

serial_message1 = ""
serial_message2 = ""
serial_message3 = ""
serial_message4 = ""


def save_animation():
    if toggle_state.get():
        data = {
            "mode": "ik",
            "sequence": recorded_values_position
        }

    else:
        data = {
            "mode": "angles",
            "sequence": recorded_values_angle
        }
    with open("animation.json", "w") as f:
        json.dump(data, f, indent=4)
    
    print("Animation Saved")

def load_animation():
    global recorded_values_position, recorded_values_angle, last_recorded_time

    try:
        with open("animation.json", "r") as f:
            data = json.load(f)
        mode = data["mode"]
        sequence = data["sequence"]
    
        record_listbox.delete(0, tk.END)
        last_recorded_time = 0.0
        
        if mode == "ik":
            recorded_values_position = sequence
            toggle_state.set(True)
        else:
            recorded_values_angle = sequence
            toggle_state.set(False)

        for value  in sequence:
            if mode == "ik":
                x, y, z, phi, grip, t = values
                record_listbox.insert(tk.END, f"X:{x} Y:{y} Z:{z} Phi:{phi} G:{grip} T:{t}")
            else:
                b, s, e, p, g, t = values
                record_listbox.insert(tk.END, f"B:{b} S:{s} E:{e} P:{p} G:{g} T:{t}")

        print("Animation loaded")
    except FileNotFoundError:
        
        print("No saved animation found")

def read_serial_message():
    global serial_message1, serial_message2, serial_message3, serial_message4

    if ser and ser.in_waiting:
        try:
            line = ser.readline().decode().strip()
            parts = line.split(",")

            if len(parts) >= 4:
                serial_message1 = parts[0]
                serial_message2 = parts[1]
                serial_message3 = parts[2]
                serial_message4 = parts[3]
        except:
            pass

    serial_read_label1.config(text=f"Message line 1: {serial_message1}")
    serial_read_label2.config(text=f"Message line 2: {serial_message2}")
    serial_read_label3.config(text=f"Message line 3: {serial_message3}")
    serial_read_label4.config(text=f"Message line 4: {serial_message4}")


def flush_serial():
    global serial_message1, serial_message2, serial_message3, serial_message4

    serial_message1 = ""
    serial_message2 = ""
    serial_message3 = ""
    serial_message4 = ""

    serial_read_label1.config(text="Message line 1:")
    serial_read_label2.config(text="Message line 2:")
    serial_read_label3.config(text="Message line 3:")
    serial_read_label4.config(text="Message line 4:")


def write_serial_values(a, b, c, d, e):
    if ser:
        ser.write(f"{a} {b} {c} {d}\n".encode())
        
        time.sleep(0.02)
        
        ser.write(f"g {e}\n".encode())


def change_mode_serial(mode):
    global ik_mode_on

    if mode != ik_mode_on:
        ik_mode_on = bool(mode)

        if ser:
            ser.write(b"m 1\n" if mode else b"m 0\n")


def clear_widgets():
    global widgets
    for w in widgets:
        w.destroy()
    widgets = []


def create_slider(name, ik_mode):
    label = tk.Label(content_frame, text=name, font=("Arial", 14))
    label.pack(pady=5)

    var = tk.IntVar(value=100 if ik_mode else 90)
    slider_values[name] = var

    value_label = tk.Label(content_frame, text=f"Value: {var.get()}")
    value_label.pack()

    last_send = [0]

    def on_slide(val):
        value_label.config(text=f"Value: {int(float(val))}")

        now = time.time()
        if now - last_send[0] > 0.1:
            read_robot_state()
            last_send[0] = now

    slider = tk.Scale(
        content_frame,
        from_=50 if ik_mode else 0,
        to=200 if ik_mode else 180,
        orient="horizontal",
        length=300,
        variable=var,
        command=on_slide
    )
    slider.pack(pady=5)

    widgets.extend([label, value_label, slider])


def show_position_mode():
    clear_widgets()
    create_slider("X Position", 1)
    create_slider("Y Position", 1)
    create_slider("Z Position", 1)
    create_slider("Phi Angle", 1)
    create_slider("Gripper Servo", 1)


def show_angle_mode():
    clear_widgets()
    create_slider("Base Servo", 0)
    create_slider("Shoulder Servo", 0)
    create_slider("Elbow Servo", 0)
    create_slider("Phi Servo", 0)
    create_slider("Gripper Servo", 0)


def update_mode():
    if toggle_state.get():
        toggle_button.config(text="Mode: POSITION")
        show_position_mode()
        change_mode_serial(1)
    else:
        toggle_button.config(text="Mode: ANGLES")
        show_angle_mode()
        change_mode_serial(0)


def record_position():
    global last_recorded_time

    if toggle_state.get():
        t = float(time_input.get())

        if t < last_recorded_time:
            time_input_label.config(text=f"Time must be >= {last_recorded_time}")
            return

        last_recorded_time = t

        x = slider_values["X Position"].get()
        y = slider_values["Y Position"].get()
        z = slider_values["Z Position"].get()
        phi = slider_values["Phi Angle"].get()
        grip = slider_values["Gripper Servo"].get()

        pos = (x, y, z, phi, grip, t)
        recorded_values_position.append(pos)

        record_listbox.insert(tk.END, f"X:{x} Y:{y} Z:{z} Phi:{phi} G:{grip} T:{t}")
def record_angles():
    global last_recorded_time

    if not toggle_state.get():
        t = float(time_input.get())

        if t < last_recorded_time:
            time_input_label.config(text=f"Time must be >= {last_recorded_time}")
            return

        last_recorded_time = t
        
        base = slider_values["Base Servo"].get()
        shoulder = slider_values["Shoulder Servo"].get()
        elbow = slider_values["Elbow Servo"].get()
        phi = slider_values["Phi Servo"].get()
        grip = slider_values["Gripper Servo"].get()
        
            

        ang = (base, shoulder, elbow, phi, grip, t)
        recorded_values_angle.append(ang)

        record_listbox.insert(tk.END, f"B:{base} S:{shoulder} E:{elbow} P:{phi} G:{grip} T:{t}")



def clear_records():
    recorded_values_position.clear()
    recorded_values_angle.clear()
    record_listbox.delete(0, tk.END)
    

def animate():
    if toggle_state.get():
        sequence = recorded_values_position
    else:
        sequence = recorded_values_angle

    if not sequence:
        print("No data recorded")
        return

    def play_step(index=0):
        if index >= len(sequence):
            return

        values = sequence[index]
        if toggle_state.get():
            slider_values["X Position"].set(values[0])
            slider_values["Y Position"].set(values[1])
            slider_values["Z Position"].set(values[2])
            slider_values["Phi Angle"].set(values[3])
            slider_values["Gripper Servo"].set(values[4])
        else:
            slider_values["Base Servo"].set(values[0])
            slider_values["Shoulder Servo"].set(values[1])
            slider_values["Elbow Servo"].set(values[2])
            slider_values["Phi Servo"].set(values[3])
            slider_values["Gripper Servo"].set(values[4])

        write_serial_values(*values[:5])

        if index < len(sequence) - 1:
            current_time = values[5]
            next_time = sequence[index + 1][5]

            delay = next_time - current_time
            delay = max(delay, 0.001)  

            root.after(int(delay * 1000), lambda: play_step(index + 1))
        else:
            print("Animation finished")

    play_step()

def read_robot_state():
    global last_send_time

    now = time.time()
    if now - last_send_time < 0.1:  
        return

    last_send_time = now    

    if toggle_state.get():
        x = slider_values["X Position"].get()
        y = slider_values["Y Position"].get()
        z = slider_values["Z Position"].get()
        phi = slider_values["Phi Angle"].get()
        grip = slider_values["Gripper Servo"].get()

        write_serial_values(x, y, z, phi, grip)

    else:
        base = slider_values["Base Servo"].get()
        shoulder = slider_values["Shoulder Servo"].get()
        elbow = slider_values["Elbow Servo"].get()
        phi = slider_values["Phi Servo"].get()
        grip = slider_values["Gripper Servo"].get()

        write_serial_values(base, shoulder, elbow, phi, grip)


def loop():
    read_serial_message()
    root.after(100, loop)


toggle_button = tk.Checkbutton(
    top_frame,
    text="Mode: ANGLES",
    variable=toggle_state,
    command=update_mode
)
toggle_button.pack()

serial_read_label1 = tk.Label(content_frame)
serial_read_label1.pack()

serial_read_label2 = tk.Label(content_frame)
serial_read_label2.pack()

serial_read_label3 = tk.Label(content_frame)
serial_read_label3.pack()

serial_read_label4 = tk.Label(content_frame)
serial_read_label4.pack()

flush_btn = tk.Button(content_frame, text="Flush Serial", command=flush_serial)
flush_btn.pack(pady=5)


record_label = tk.Label(record_frame, text="Recorded Positions")
record_label.pack()

record_listbox = tk.Listbox(record_frame, height=6)
record_listbox.pack(fill="x", padx=10)

btn_frame = tk.Frame(record_frame)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Record Pos", command=record_position).pack(side="left", padx=5)
tk.Button(btn_frame, text="Record Ang", command=record_angles).pack(side="left", padx=5)
tk.Button(btn_frame, text="Clear", command=clear_records).pack(side="left", padx=5)
tk.Button(btn_frame, text="Animate", command=animate).pack(side="left", padx=5)
tk.Button(btn_frame, text="Save anim", command=save_animation).pack(side="left", padx=5)
tk.Button(btn_frame, text="Load anim", command=load_animation).pack(side="left", padx=5)

time_input_label = tk.Label(content_frame, text="Enter Time example: 1.0")
time_input_label.pack()

time_input_var = tk.StringVar(value="0.0")
last_recorded_time = 0.0

time_input = tk.Entry(content_frame, textvariable=time_input_var)
time_input.pack()

show_angle_mode()
loop()
root.mainloop()