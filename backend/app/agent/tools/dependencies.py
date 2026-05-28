from app.agent.tools.registry import register

# ── Whitelists ───────────────────────────────────────────────

ALLOWED_CACHE_TARGETS = {
    "npm":    "npm cache clean --force",
    "pip":    "pip cache purge",
    "yarn":   "yarn cache clean",
    "docker": "docker system prune -f",
    "vite":   "rm -rf node_modules/.vite",
    "jest":   "jest --clearCache",
}

ALLOWED_PACKAGE_MANAGERS = {"npm", "pip", "yarn", "pnpm"}

# Simulated broken packages per package manager
_SIMULATED_BROKEN: dict[str, list[dict]] = {
    "npm": [
        {"package": "esbuild", "issue": "native binary mismatch", "fix": "npm rebuild esbuild"},
        {"package": "node-sass", "issue": "version incompatible with Node 20", "fix": "npm install sass"},
    ],
    "pip": [
        {"package": "psycopg2", "issue": "missing libpq-dev", "fix": "apt install libpq-dev && pip install psycopg2"},
    ],
    "yarn": [],
    "pnpm": [],
}

# Simulated version conflicts
_SIMULATED_CONFLICTS: dict[str, list[dict]] = {
    "npm": [
        {"package": "react", "required": "^18.0.0", "installed": "17.0.2", "conflict_with": "react-dom@18.3.1"},
    ],
    "pip": [],
    "yarn": [],
    "pnpm": [],
}

# Error pattern → fix suggestion
_FIX_PATTERNS: list[tuple[list[str], str, str]] = [
    (["cannot find module", "module not found"],
     "npm install", "Reinstala las dependencias del proyecto"),
    (["enoent", "no such file or directory"],
     "npm install && npm run build", "Asegúrate de que node_modules exista y vuelve a compilar"),
    (["permission denied", "eacces"],
     "sudo chown -R $USER:$GROUP . && npm install", "Corrige los permisos de la carpeta del proyecto"),
    (["modulenotfounderror", "no module named", "importerror"],
     "pip install -r requirements.txt", "Instala las dependencias de Python faltantes"),
    (["peer dep", "peer dependency", "conflicting peer dependency"],
     "npm install --legacy-peer-deps", "Ignora conflictos de peer dependencies (temporal)"),
    (["out of disk", "enospc", "no space left"],
     "docker system prune -f && npm cache clean --force", "Libera espacio en disco limpiando cachés y Docker"),
    (["network", "etimedout", "econnreset", "enotfound"],
     "npm install --prefer-offline", "Problema de red — intenta instalar desde caché local"),
    (["version conflict", "incompatible", "requires node"],
     "nvm use 20 && npm install", "Cambia a Node 20 LTS que es compatible con la mayoría de paquetes actuales"),
    (["gyp err", "node-gyp", "build failed"],
     "npm install --ignore-scripts", "Omite scripts de compilación nativa (solución rápida)"),
]


@register({
    "type": "function",
    "function": {
        "name": "detect_broken_dependencies",
        "description": "Detecta paquetes rotos o con problemas en el entorno. Úsala cuando el usuario reporta errores al instalar o importar módulos.",
        "parameters": {
            "type": "object",
            "properties": {
                "package_manager": {"type": "string", "description": "Gestor de paquetes: npm, pip, yarn, pnpm."},
            },
            "required": ["package_manager"],
        },
    },
})
async def detect_broken_dependencies(args: dict) -> dict:
    pm = args["package_manager"].lower().strip()
    if pm not in ALLOWED_PACKAGE_MANAGERS:
        return {"status": "error", "message": f"Package manager no soportado. Usa: {', '.join(ALLOWED_PACKAGE_MANAGERS)}."}
    broken = _SIMULATED_BROKEN.get(pm, [])
    if not broken:
        return {"status": "ok", "package_manager": pm, "broken_count": 0,
                "message": f"No se detectaron dependencias rotas en {pm}."}
    return {"status": "issues_found", "package_manager": pm,
            "broken_count": len(broken), "broken_packages": broken,
            "note": "Entorno simulado para demo. En producción esto ejecutaría npm ls --depth=0 2>&1 | grep ERR"}


@register({
    "type": "function",
    "function": {
        "name": "clean_cache",
        "description": (
            "Limpia la caché de un gestor de paquetes o herramienta. "
            "IMPORTANTE: muestra el comando al usuario antes de ejecutarlo (dry-run mode). "
            "Solo limpia targets de la whitelist permitida."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": f"Target a limpiar. Permitidos: {', '.join(ALLOWED_CACHE_TARGETS)}."},
                "confirmed": {"type": "boolean", "description": "True si el usuario ya confirmó ejecutar el comando."},
            },
            "required": ["target"],
        },
    },
})
async def clean_cache(args: dict) -> dict:
    target = args["target"].lower().strip()
    command = ALLOWED_CACHE_TARGETS.get(target)
    if not command:
        return {"status": "error",
                "message": f"Target '{target}' no está en la whitelist. Permitidos: {', '.join(ALLOWED_CACHE_TARGETS)}."}
    if not args.get("confirmed"):
        return {"status": "pending_confirmation", "target": target, "command": command,
                "message": f"⚠️ Para limpiar la caché de {target} ejecutaré: `{command}`. ¿Confirmas?"}
    return {"status": "ok", "target": target, "command": command,
            "message": f"✅ Caché de {target} limpiada (simulado). Comando ejecutado: {command}",
            "note": "Entorno simulado — en producción esto ejecuta el comando real."}


@register({
    "type": "function",
    "function": {
        "name": "reinstall_dependency",
        "description": "Reinstala un paquete específico. Muestra el comando exacto antes de ejecutarlo (dry-run).",
        "parameters": {
            "type": "object",
            "properties": {
                "package_name": {"type": "string", "description": "Nombre del paquete a reinstalar."},
                "package_manager": {"type": "string", "description": "Gestor de paquetes: npm, pip, yarn, pnpm."},
                "confirmed": {"type": "boolean", "description": "True si el usuario ya confirmó."},
            },
            "required": ["package_name", "package_manager"],
        },
    },
})
async def reinstall_dependency(args: dict) -> dict:
    pm = args["package_manager"].lower().strip()
    pkg = args["package_name"].strip()
    if pm not in ALLOWED_PACKAGE_MANAGERS:
        return {"status": "error", "message": f"Package manager no soportado: {pm}."}

    commands = {
        "npm":  f"npm uninstall {pkg} && npm install {pkg}",
        "pip":  f"pip uninstall -y {pkg} && pip install {pkg}",
        "yarn": f"yarn remove {pkg} && yarn add {pkg}",
        "pnpm": f"pnpm remove {pkg} && pnpm add {pkg}",
    }
    command = commands[pm]

    if not args.get("confirmed"):
        return {"status": "pending_confirmation", "package": pkg, "package_manager": pm,
                "command": command,
                "message": f"⚠️ Voy a reinstalar `{pkg}` con: `{command}`. ¿Confirmas?"}
    return {"status": "ok", "package": pkg, "package_manager": pm, "command": command,
            "message": f"✅ Paquete `{pkg}` reinstalado (simulado). Comando: {command}",
            "note": "Entorno simulado — en producción esto ejecuta el comando real."}


@register({
    "type": "function",
    "function": {
        "name": "check_version_conflicts",
        "description": "Detecta conflictos de versiones entre paquetes instalados.",
        "parameters": {
            "type": "object",
            "properties": {
                "package_manager": {"type": "string", "description": "Gestor de paquetes: npm, pip, yarn, pnpm."},
            },
            "required": ["package_manager"],
        },
    },
})
async def check_version_conflicts(args: dict) -> dict:
    pm = args["package_manager"].lower().strip()
    if pm not in ALLOWED_PACKAGE_MANAGERS:
        return {"status": "error", "message": f"Package manager no soportado: {pm}."}
    conflicts = _SIMULATED_CONFLICTS.get(pm, [])
    if not conflicts:
        return {"status": "ok", "package_manager": pm,
                "message": f"No se detectaron conflictos de versiones en {pm}."}
    return {"status": "conflicts_found", "package_manager": pm,
            "conflict_count": len(conflicts), "conflicts": conflicts,
            "fix_suggestion": "npm install --legacy-peer-deps" if pm == "npm" else "pip install --upgrade <paquete>"}


@register({
    "type": "function",
    "function": {
        "name": "suggest_fix",
        "description": "Analiza un mensaje de error y sugiere el comando exacto para resolverlo, con explicación.",
        "parameters": {
            "type": "object",
            "properties": {
                "error_output": {"type": "string", "description": "Texto del error a analizar."},
            },
            "required": ["error_output"],
        },
    },
})
async def suggest_fix(args: dict) -> dict:
    text = args["error_output"].lower()
    for patterns, command, explanation in _FIX_PATTERNS:
        if any(p in text for p in patterns):
            return {"found": True, "suggested_command": command, "explanation": explanation,
                    "warning": "Verifica el comando antes de ejecutarlo. Úsalo en un entorno de desarrollo primero."}
    return {"found": False,
            "message": "No encontré un patrón conocido para ese error. Comparte el mensaje completo para un análisis más detallado.",
            "tip": "Prueba buscarlo en la FAQ o abriendo un ticket con el error completo."}
