import psutil
from fastapi import APIRouter

router = APIRouter(tags=["monitor"])


@router.get("/system-monitor")
def system_monitor():
    """Live machine stats — the 'suit diagnostics' equivalent."""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot = psutil.boot_time()
    import time

    battery = None
    try:
        bat = psutil.sensors_battery()
        if bat:
            battery = {
                "percent": round(bat.percent, 1),
                "plugged": bat.power_plugged,
            }
    except Exception:
        pass

    # Top processes by CPU and memory
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append({
                "pid": p.info["pid"],
                "name": p.info["name"],
                "cpu": round(p.info["cpu_percent"] or 0, 1),
                "mem": round(p.info["memory_percent"] or 0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["cpu"], reverse=True)

    cpu_freq = psutil.cpu_freq()

    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.3),
            "cores": psutil.cpu_count(logical=True),
            "physical": psutil.cpu_count(logical=False),
            "freq_mhz": round(cpu_freq.current) if cpu_freq else None,
        },
        "memory": {
            "percent": vm.percent,
            "used_gb": round(vm.used / 1e9, 1),
            "total_gb": round(vm.total / 1e9, 1),
            "available_gb": round(vm.available / 1e9, 1),
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": round(disk.used / 1e9, 1),
            "total_gb": round(disk.total / 1e9, 1),
            "free_gb": round(disk.free / 1e9, 1),
        },
        "battery": battery,
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / 1e6, 1),
            "bytes_recv_mb": round(net.bytes_recv / 1e6, 1),
            "connections": len(psutil.net_connections(kind="inet")) if hasattr(psutil, "net_connections") else None,
        },
        "uptime_seconds": int(time.time() - boot),
        "top_processes": procs[:8],
        "os": f"{psutil.uname().system} {psutil.uname().release}",
    }
