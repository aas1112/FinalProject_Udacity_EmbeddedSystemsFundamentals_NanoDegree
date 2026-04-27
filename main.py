import machine
import time

# --- CONFIGURATION ---
# Default passcode is [0, 2, 1]
PASSCODE = [0, 2, 1] 
LED_START_PIN = 7
BTN_START_PIN = 16

# --- PIN DEFINITIONS ---
# Map the LEDs D0 - D8 as outputs 0-8 (Total of 9)
leds = []
for i in range(9):
    leds.append(machine.Pin(LED_START_PIN + i, machine.Pin.OUT))

# Map buttons connected to B0 - B2 as numeric keys 0 to 2
buttons = []
for i in range(3):
    buttons.append(machine.Pin(BTN_START_PIN + i, machine.Pin.IN, machine.Pin.PULL_DOWN))

# Multiplexer (MUX) Pins
mux_s0 = machine.Pin(27, machine.Pin.OUT) # Mux-1 Select (LSB)
mux_s1 = machine.Pin(28, machine.Pin.OUT) # Mux-2 Select (MSB)
mux_out = machine.Pin(26, machine.Pin.IN) # Mux-2 Out

# --- GLOBAL VARIABLES ---
key_presses = []
last_button_time = 0

# --- INTERRUPT HANDLER ---
def interrupt_callback(pin):
    global last_button_time
    current_time = time.ticks_ms()
    
    # 200 ms debouncing guard window
    if time.ticks_diff(current_time, last_button_time) > 200:
        last_button_time = current_time
        
        button_idx = -1
        if pin == buttons[0]:
            button_idx = 0
        elif pin == buttons[1]:
            button_idx = 1
        elif pin == buttons[2]:
            button_idx = 2
            
        if button_idx != -1:
            key_presses.append(button_idx)
            print(f"Key pressed: {button_idx}")

# --- READ SWITCHES (POLLING MUX) ---
def read_switches():
    val = 0
    
    # Read SW0 (S1=0, S0=0)
    mux_s1.value(0)
    mux_s0.value(0)
    time.sleep(0.01) # Tiny sleep to stabilize MUX signal
    val += mux_out.value() * 1
    
    # Read SW1 (S1=0, S0=1)
    mux_s1.value(0)
    mux_s0.value(1)
    time.sleep(0.01)
    val += mux_out.value() * 2
    
    # Read SW2 (S1=1, S0=0)
    mux_s1.value(1)
    mux_s0.value(0)
    time.sleep(0.01)
    val += mux_out.value() * 4
    
    # Read SW3 (S1=1, S0=1)
    mux_s1.value(1)
    mux_s0.value(1)
    time.sleep(0.01)
    val += mux_out.value() * 8
    
    return val

# --- MAIN PROGRAM ---
def main():
    global key_presses, last_button_time
    
    # Attach interrupts to buttons
    for btn in buttons:
        btn.irq(trigger=machine.Pin.IRQ_RISING, handler=interrupt_callback)
        
    last_decimal_val = -1
    
    # Print at the program start
    print("System started. Please set the switches or enter passcode.")
    
    while True:
        # Poll mux inputs in sequence and convert to decimal
        current_decimal_val = read_switches()
        if current_decimal_val != last_decimal_val:
            print(f"Selected output: {current_decimal_val}")
            last_decimal_val = current_decimal_val
            
        # Timeout feature: clear sequence after 3 seconds of inactivity
        if len(key_presses) > 0 and len(key_presses) < 3:
            if time.ticks_diff(time.ticks_ms(), last_button_time) > 3000:
                print("Timeout: Sequence cleared due to inactivity.")
                key_presses.clear()
                
        # Passcode evaluation
        if len(key_presses) >= 3:
            attempt = key_presses[:3]
            print(f"Passcode entered: {attempt}")
            
            if attempt == PASSCODE:
                print("Correct passcode!")
                if last_decimal_val <= 8:
                    leds[last_decimal_val].toggle()
                    print(f"Success: Toggled LED {last_decimal_val}")
                else:
                    print(f"Error: Selected output {last_decimal_val} is out of range. Valid range: 0-8.")
            else:
                print("Incorrect passcode! LEDs remain unchanged.")
            
            # Remove the first 3 evaluated keys
            for _ in range(3):
                key_presses.pop(0)
                
        time.sleep(0.05)

if __name__ == "__main__":
    main()