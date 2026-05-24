import serial
import time
import pywhatkit
import datetime

# ============================================================
#  LPG Gas Leak WhatsApp Alert System — FINAL STABLE VERSION
# ============================================================

print("============================================")
print("   LPG Gas Leak WhatsApp Alert System      ")
print("============================================")

phone_number = input("Enter phone number (with country code): ").strip()

SERIAL_PORT = "COM5"
BAUD_RATE   = 9600

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    print("Arduino connected. Monitoring started...")
except:
    print("Error connecting to Arduino")
    exit()

# ---- STATE CONTROL -----------------------------------------
leak_active = False
safe_timer_start = None
SAFE_DELAY = 5   # seconds

# ---- MESSAGE BUILDER ---------------------------------------
def build_message(danger_level, gas_value, valve_status):
    now = datetime.datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    return (
        f"🚨 GAS ALERT\n\n"
        f"Level: {danger_level}\n"
        f"Gas Value: {gas_value}\n"
        f"Valve: {valve_status}\n"
        f"Time: {now}"
    )

# ---- WHATSAPP SENDER (FIXED) -------------------------------
def send_whatsapp(message):
    try:
        print("[WhatsApp] Opening Web...")

        pywhatkit.sendwhatmsg_instantly(
            f"+{phone_number}",
            message,
            wait_time=20,      # ⬅️ increased wait time
            tab_close=False    # ⬅️ prevent auto closing
        )

        # Wait for message to fully send
        print("[WhatsApp] Sending message...")
        time.sleep(15)

        print("[WhatsApp] Message sent successfully\n")

    except Exception as e:
        print("Error sending:", e)

# ---- HELPERS -----------------------------------------------
def get_danger_level(line):
    if "EMERGENCY" in line:
        return "EMERGENCY"
    elif "DANGEROUS" in line:
        return "DANGEROUS"
    elif "MODERATE LEAK" in line:
        return "MODERATE LEAK"
    elif "MILD LEAK" in line:
        return "MILD LEAK"
    return None

def extract_gas(line):
    try:
        if "Gas level:" in line:
            return line.split("Gas level:")[1].strip().split()[0]
    except:
        pass
    return "N/A"

# ---- MAIN LOOP ---------------------------------------------
gas_value = "N/A"
valve_status = "OPEN 🔓"

while True:
    try:
        line = arduino.readline().decode(errors="ignore").strip()

        if not line:
            continue

        print(line)

        # Update gas value
        if "Gas level:" in line:
            gas_value = extract_gas(line)

        # Update valve status
        if "Valve closed" in line:
            valve_status = "CLOSED 🔒"
        elif "Valve opened" in line:
            valve_status = "OPEN 🔓"

        danger = get_danger_level(line)

        # 🔴 LEAK DETECTED (ONLY ONCE)
        if danger and not leak_active:
            leak_active = True
            safe_timer_start = None

            print("[System] Leak detected → sending ALERT")

            msg = build_message(danger, gas_value, valve_status)
            send_whatsapp(msg)

        # 🟢 SAFE DETECTION (WITH STABILITY DELAY)
        if "Kitchen safe" in line or "Gas cleared" in line:
            if leak_active:
                if safe_timer_start is None:
                    safe_timer_start = time.time()

                elif time.time() - safe_timer_start >= SAFE_DELAY:
                    leak_active = False
                    safe_timer_start = None

                    print("[System] Gas stable → sending SAFE message")

                    now = datetime.datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                    msg = (
                        f"✅ Gas leak resolved\n\n"
                        f"Valve: OPEN 🔓\n"
                        f"Time: {now}"
                    )

                    send_whatsapp(msg)

        # ❗ Cancel safe timer if gas rises again
        if danger:
            safe_timer_start = None

    except Exception as e:
        print("Error:", e)
        continue

