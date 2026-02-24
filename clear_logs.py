#!/usr/bin/env python3
"""clear_logs.py

Vacía (trunca) todos los archivos regulares encontrados dentro de la carpeta `logs`.

Uso:
  python3 clear_logs.py            # pide confirmación
  python3 clear_logs.py --yes      # sin confirmación
  python3 clear_logs.py --dry-run  # muestra qué archivos se vaciarían
  python3 clear_logs.py --path my_logs

Seguridad:
 - No borra directorios ni enlaces, solo trunca archivos regulares.
 - No intenta restaurar datos; úsalo con precaución.
"""
import argparse
import sys
from pathlib import Path


def human_readable(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024.0:
            return f"{n:.2f}{unit}"
        n /= 1024.0
    return f"{n:.2f}TB"


def find_files(logs_path: Path):
    if not logs_path.exists() or not logs_path.is_dir():
        print(f"Error: {logs_path} no existe o no es un directorio.")
        sys.exit(1)
    return [p for p in logs_path.rglob("*") if p.is_file()]


def summary(files):
    total = sum(f.stat().st_size for f in files)
    print(f"Archivos encontrados: {len(files)} — tamaño total: {human_readable(total)}")
    for f in files:
        print(f" - {f} ({human_readable(f.stat().st_size)})")


def truncate_files(files, dry_run: bool):
    freed = 0
    truncated = 0
    for f in files:
        try:
            size = f.stat().st_size
            if size == 0:
                continue
            if dry_run:
                truncated += 1
                freed += size
                continue
            # Truncar abriendo en modo escritura (esto deja el archivo vacío)
            with open(f, "w"):
                pass
            freed += size
            truncated += 1
            print(f"Truncado: {f} ({human_readable(size)})")
        except Exception as e:
            print(f"Error truncando {f}: {e}")
    return truncated, freed


def parse_args():
    p = argparse.ArgumentParser(description="Vacía todos los archivos de logs en una carpeta")
    p.add_argument("--path", default="logs", help="Ruta al directorio de logs (default: logs)")
    p.add_argument("--yes", action="store_true", help="No pedir confirmación")
    p.add_argument("--dry-run", action="store_true", help="Mostrar qué se haría sin modificar archivos")
    return p.parse_args()


def main():
    args = parse_args()
    logs_path = Path(args.path)
    files = find_files(logs_path)

    if not files:
        print(f"No se encontraron archivos en {logs_path}.")
        return

    print(f"Preparado para vaciar archivos en: {logs_path}")
    summary(files)

    if args.dry_run:
        print("--dry-run activado: no se realizarán cambios.")
        return

    if not args.yes:
        confirm = input("¿Continuar y vaciar estos archivos? (y/N): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Abortado por el usuario.")
            return

    truncated, freed = truncate_files(files, dry_run=False)
    print(f"Operación completada: {truncated} archivos truncados — espacio liberado: {human_readable(freed)}")


if __name__ == "__main__":
    main()
