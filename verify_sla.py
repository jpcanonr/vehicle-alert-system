import re
from datetime import datetime

# Archivos de logs
API_LOG = "logs/api.log"
PROCESSOR_LOG = "logs/processor.log"
NOTIFIER_LOG = "logs/notifier.log"

# Patrones para extraer timestamps
api_pattern = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+).*Evento recibido.*Placa (?P<plate>\S+)")
processor_pattern = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+).*Detectado Emergency.*'vehicle_plate': '(?P<plate>\S+)'")
notifier_pattern = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+).*Correo enviado exitosamente.*")

def parse_log(file, pattern):
    events = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                ts = datetime.strptime(match.group("time"), "%Y-%m-%d %H:%M:%S,%f")
                plate = match.groupdict().get("plate", None)
                events.append((ts, plate))
    return events

def main():
    api_events = parse_log(API_LOG, api_pattern)
    processor_events = parse_log(PROCESSOR_LOG, processor_pattern)
    notifier_events = parse_log(NOTIFIER_LOG, notifier_pattern)

    print("=== SLA Verification Report ===")
    for i, (api_time, plate) in enumerate(api_events):
        proc_time = next((t for t, p in processor_events if p == plate), None)
        notif_time = notifier_events[i][0] if i < len(notifier_events) else None

        if proc_time and notif_time:
            delta = (notif_time - api_time).total_seconds()
            status = "OK (<15s)" if delta < 15 else "FAIL (>15s)"
            print(f"Placa {plate}: {delta:.2f}s → {status}")
        else:
            print(f"Placa {plate}: evento incompleto (no procesado o no notificado)")

if __name__ == "__main__":
    main()
