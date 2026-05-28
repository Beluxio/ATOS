from app.agent.tools.registry import register

ALLOWED_TOOLS = {
    "node", "npm", "python", "python3", "pip", "pip3",
    "git", "docker", "yarn", "pnpm", "java", "mvn",
    "curl", "wget", "make", "gcc", "go", "rustc",
}

# Simulated tool versions for demo
_SIMULATED_VERSIONS: dict[str, dict] = {
    "node":    {"installed": True,  "version": "v20.11.0", "status": "ok"},
    "npm":     {"installed": True,  "version": "10.2.4",   "status": "ok"},
    "python":  {"installed": True,  "version": "3.12.1",   "status": "ok"},
    "python3": {"installed": True,  "version": "3.12.1",   "status": "ok"},
    "pip":     {"installed": True,  "version": "24.0",     "status": "ok"},
    "pip3":    {"installed": True,  "version": "24.0",     "status": "ok"},
    "git":     {"installed": True,  "version": "2.43.0",   "status": "ok"},
    "docker":  {"installed": True,  "version": "26.1.0",   "status": "ok"},
    "yarn":    {"installed": False, "version": None,        "status": "missing"},
    "pnpm":    {"installed": True,  "version": "9.0.0",    "status": "ok"},
    "java":    {"installed": False, "version": None,        "status": "missing"},
    "go":      {"installed": False, "version": None,        "status": "missing"},
    "rustc":   {"installed": False, "version": None,        "status": "missing"},
    "curl":    {"installed": True,  "version": "8.5.0",    "status": "ok"},
    "wget":    {"installed": True,  "version": "1.21.4",   "status": "ok"},
    "make":    {"installed": True,  "version": "4.3",      "status": "ok"},
    "gcc":     {"installed": True,  "version": "13.2.0",   "status": "ok"},
}

# Simulated PATH validation patterns
_VALID_PATH_PATTERNS = [
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/local/sbin",
    "/usr/sbin",
    "/home/user/.local/bin",
    "/home/user/.nvm/versions/node/v20.11.0/bin",
]

_MINIMUM_REQUIREMENTS = {
    "node": {"min_version": "18.0.0", "installed": "20.11.0", "ok": True},
    "python": {"min_version": "3.10", "installed": "3.12.1", "ok": True},
    "npm": {"min_version": "9.0.0", "installed": "10.2.4", "ok": True},
    "git": {"min_version": "2.30.0", "installed": "2.43.0", "ok": True},
    "docker": {"min_version": "24.0.0", "installed": "26.1.0", "ok": True},
    "disk_space_gb": {"min": 5, "available": 42, "ok": True},
    "ram_gb": {"min": 4, "available": 16, "ok": True},
}


@register({
    "type": "function",
    "function": {
        "name": "check_tool_installed",
        "description": "Verifica si una herramienta o CLI está instalada en el sistema y devuelve su versión.",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": f"Nombre de la herramienta. Permitidas: {', '.join(sorted(ALLOWED_TOOLS))}.",
                },
            },
            "required": ["tool_name"],
        },
    },
})
async def check_tool_installed(args: dict) -> dict:
    tool = args["tool_name"].lower().strip()
    if tool not in ALLOWED_TOOLS:
        return {
            "status": "error",
            "message": f"Herramienta '{tool}' no está en la lista permitida. Permitidas: {', '.join(sorted(ALLOWED_TOOLS))}.",
        }
    info = _SIMULATED_VERSIONS.get(tool, {"installed": False, "version": None, "status": "unknown"})
    if info["installed"]:
        return {
            "status": "ok",
            "tool": tool,
            "installed": True,
            "version": info["version"],
            "note": "Entorno simulado — en producción ejecuta `which <tool> && <tool> --version`.",
        }
    return {
        "status": "missing",
        "tool": tool,
        "installed": False,
        "version": None,
        "suggestion": f"Instala {tool} antes de continuar. Consulta la documentación oficial.",
    }


@register({
    "type": "function",
    "function": {
        "name": "validate_path",
        "description": "Verifica si un directorio está correctamente incluido en la variable PATH del sistema.",
        "parameters": {
            "type": "object",
            "properties": {
                "path_value": {
                    "type": "string",
                    "description": "Ruta a verificar (ej: /usr/local/bin o /home/user/.local/bin).",
                },
            },
            "required": ["path_value"],
        },
    },
})
async def validate_path(args: dict) -> dict:
    path = args["path_value"].strip()
    if not path.startswith("/") and not path.startswith("~"):
        return {
            "status": "warning",
            "path": path,
            "valid_format": False,
            "message": "La ruta debería ser absoluta (empieza con / o ~).",
        }
    in_path = any(path in p or p in path for p in _VALID_PATH_PATTERNS)
    if in_path:
        return {
            "status": "ok",
            "path": path,
            "in_path": True,
            "message": f"✅ '{path}' está incluida en PATH.",
            "note": "Entorno simulado.",
        }
    return {
        "status": "warning",
        "path": path,
        "in_path": False,
        "message": f"⚠️ '{path}' NO está en PATH.",
        "fix": f'Añade esto a ~/.bashrc o ~/.zshrc: export PATH="$PATH:{path}"',
    }


@register({
    "type": "function",
    "function": {
        "name": "check_minimum_requirements",
        "description": "Verifica que el sistema cumple los requisitos mínimos para el proyecto (versiones, espacio en disco, RAM).",
        "parameters": {
            "type": "object",
            "properties": {
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de requisitos a verificar: node, python, npm, git, docker, disk_space_gb, ram_gb.",
                },
            },
            "required": ["requirements"],
        },
    },
})
async def check_minimum_requirements(args: dict) -> dict:
    reqs = args["requirements"]
    results = []
    all_ok = True

    for req in reqs:
        key = req.lower().strip()
        if key not in _MINIMUM_REQUIREMENTS:
            results.append({"requirement": req, "status": "unknown", "message": "Requisito no reconocido."})
            continue
        info = _MINIMUM_REQUIREMENTS[key]
        ok = info["ok"]
        if not ok:
            all_ok = False
        if key in ("disk_space_gb", "ram_gb"):
            results.append({
                "requirement": req,
                "status": "ok" if ok else "insufficient",
                "minimum": info["min"],
                "available": info["available"],
                "unit": "GB",
            })
        else:
            results.append({
                "requirement": req,
                "status": "ok" if ok else "outdated",
                "min_version": info["min_version"],
                "installed_version": info["installed"],
            })

    return {
        "status": "ok" if all_ok else "requirements_not_met",
        "summary": f"{'Todos' if all_ok else 'Algunos'} los requisitos {'cumplidos' if all_ok else 'NO cumplidos'}.",
        "results": results,
        "note": "Entorno simulado — en producción ejecuta comandos reales de verificación.",
    }


@register({
    "type": "function",
    "function": {
        "name": "generate_environment_report",
        "description": "Genera un reporte completo del entorno del sistema: herramientas instaladas, versiones, PATH, recursos disponibles.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
})
async def generate_environment_report(args: dict) -> dict:
    installed = []
    missing = []

    core_tools = ["node", "npm", "python3", "pip3", "git", "docker", "curl"]
    for tool in core_tools:
        info = _SIMULATED_VERSIONS.get(tool, {"installed": False, "version": None})
        if info["installed"]:
            installed.append({"tool": tool, "version": info["version"]})
        else:
            missing.append(tool)

    return {
        "status": "ok",
        "report": {
            "os": "Linux (Ubuntu 22.04 LTS) — simulado",
            "architecture": "x86_64",
            "installed_tools": installed,
            "missing_tools": missing,
            "path_entries": _VALID_PATH_PATTERNS[:4],
            "resources": {
                "ram_gb": {"total": 16, "available": 12},
                "disk_gb": {"total": 512, "available": 42},
                "cpu_cores": 8,
            },
            "environment_variables": {
                "NODE_ENV": "development",
                "PYTHONPATH": "/app",
                "VIRTUAL_ENV": "/app/.venv",
                "DATABASE_URL": "postgresql+asyncpg://atos:***@db:5432/atos",
            },
        },
        "health": "good" if not missing else "warnings",
        "warnings": [f"{t} no está instalado" for t in missing],
        "note": "Entorno simulado — en producción este reporte consulta el sistema real.",
    }
