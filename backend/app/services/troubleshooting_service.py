from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.troubleshooting import TroubleshootingFlow

# ── Seed data ─────────────────────────────────────────────────

SEED_FLOWS = [
    {
        "name": "Error de módulo Node.js no encontrado",
        "description": "Diagnostica errores de 'Cannot find module' y problemas con node_modules.",
        "category": "nodejs",
        "trigger_patterns": ["cannot find module", "module not found", "npm err", "node_modules", "enoent", "require("],
        "steps": [
            {"step": 1, "title": "Verificar que node_modules existe", "action": "Ejecuta: ls node_modules (Linux/Mac) o dir node_modules (Windows)", "expected": "Carpeta node_modules presente", "hint": "Si no existe, salta al paso 2"},
            {"step": 2, "title": "Reinstalar dependencias", "action": "Ejecuta: npm install", "expected": "Sin errores, carpeta node_modules creada", "hint": "Si falla, borra node_modules primero: rm -rf node_modules && npm install"},
            {"step": 3, "title": "Verificar versión de Node.js", "action": "Ejecuta: node --version", "expected": "v16.x o superior", "hint": "Si la versión es antigua, actualiza Node.js desde nodejs.org"},
            {"step": 4, "title": "Limpiar caché de npm", "action": "Ejecuta: npm cache clean --force", "expected": "Cache cleared", "hint": "Útil si npm install falla con errores de red o integridad"},
            {"step": 5, "title": "Verificar package.json", "action": "Revisa que el paquete faltante esté en dependencies o devDependencies", "expected": "Paquete listado en package.json", "hint": "Si falta, añádelo con: npm install <nombre-paquete>"},
        ],
    },
    {
        "name": "Entorno Python / pip no funciona",
        "description": "Resuelve problemas con entornos virtuales, pip y paquetes Python.",
        "category": "python",
        "trigger_patterns": ["modulenotfounderror", "importerror", "pip", "venv", "virtualenv", "no module named", "python", "requirements.txt"],
        "steps": [
            {"step": 1, "title": "Verificar que el entorno virtual está activo", "action": "Verifica que el prompt muestre (venv) o (.env) al inicio", "expected": "Prefijo del entorno virtual visible en terminal", "hint": "Actívalo: source venv/bin/activate (Linux/Mac) o venv\\Scripts\\activate (Windows)"},
            {"step": 2, "title": "Verificar versión de Python", "action": "Ejecuta: python --version o python3 --version", "expected": "Python 3.8 o superior", "hint": "Si usas python y tienes Python 2, usa python3 explícitamente"},
            {"step": 3, "title": "Instalar dependencias desde requirements.txt", "action": "Ejecuta: pip install -r requirements.txt", "expected": "Successfully installed ... paquetes", "hint": "Si falla por permisos, añade --user o usa el entorno virtual"},
            {"step": 4, "title": "Verificar que el paquete está instalado", "action": "Ejecuta: pip list | grep <nombre-paquete>", "expected": "Paquete listado con su versión", "hint": "Si no aparece, instálalo: pip install <nombre-paquete>"},
            {"step": 5, "title": "Reinstalar en modo editable (proyectos propios)", "action": "Ejecuta: pip install -e .", "expected": "Successfully installed", "hint": "Necesario si el error es en un paquete propio del proyecto"},
        ],
    },
    {
        "name": "Error de conexión / timeout",
        "description": "Diagnostica problemas de red, timeouts y errores de conexión rechazada.",
        "category": "network",
        "trigger_patterns": ["connection refused", "timeout", "econnrefused", "econnreset", "network", "dns", "cannot connect", "unreachable", "no route to host"],
        "steps": [
            {"step": 1, "title": "Verificar que el servicio está corriendo", "action": "Ejecuta: docker ps (si usa Docker) o verifica el proceso con ps aux | grep <servicio>", "expected": "Servicio listado y en estado 'Up' o 'running'", "hint": "Si no está corriendo, inícialo con docker-compose up -d o el comando correspondiente"},
            {"step": 2, "title": "Verificar el puerto correcto", "action": "Confirma el puerto en la configuración (ej: .env, config.ts, docker-compose.yml)", "expected": "El puerto en la URL coincide con el puerto del servicio", "hint": "Error 'connection refused' casi siempre es puerto incorrecto o servicio caído"},
            {"step": 3, "title": "Probar conectividad básica", "action": "Ejecuta: curl http://localhost:<puerto>/health o ping <host>", "expected": "Respuesta 200 OK o respuesta al ping", "hint": "Si curl falla, el problema es el servicio; si ping falla, es la red"},
            {"step": 4, "title": "Verificar firewall y reglas de red", "action": "Verifica que el puerto no esté bloqueado: netstat -tulpn | grep <puerto>", "expected": "Puerto escuchando (LISTEN)", "hint": "En Windows usa: netstat -ano | findstr <puerto>"},
            {"step": 5, "title": "Revisar DNS si es dominio externo", "action": "Ejecuta: nslookup <dominio> o ping <dominio>", "expected": "IP resuelta correctamente", "hint": "Si falla, prueba con la IP directa para confirmar que es DNS"},
        ],
    },
    {
        "name": "Error de permisos (EACCES / Permission denied)",
        "description": "Resuelve errores de permisos en archivos, carpetas y comandos.",
        "category": "permissions",
        "trigger_patterns": ["permission denied", "eacces", "access denied", "sudo", "not permitted", "operation not permitted", "privileged"],
        "steps": [
            {"step": 1, "title": "Identificar qué archivo o carpeta causa el error", "action": "Lee el mensaje de error completo — suele indicar la ruta exacta", "expected": "Ruta del archivo/carpeta identificada", "hint": "El mensaje dice: EACCES: permission denied, open '/ruta/archivo'"},
            {"step": 2, "title": "Verificar propietario del archivo", "action": "Ejecuta: ls -la <ruta> (Linux/Mac) o icacls <ruta> (Windows)", "expected": "Ver usuario propietario y permisos", "hint": "Si el propietario es root y tú eres otro usuario, ese es el problema"},
            {"step": 3, "title": "Corregir permisos (Linux/Mac)", "action": "Ejecuta: sudo chown -R $USER <carpeta> para cambiar propietario", "expected": "Sin errores al ejecutar", "hint": "Alternativa: chmod 755 <carpeta> para dar permisos de lectura/ejecución"},
            {"step": 4, "title": "Nunca instalar npm con sudo", "action": "Si usas npm con sudo, configura npm para tu usuario: npm config set prefix '~/.npm-global'", "expected": "npm funciona sin sudo", "hint": "Instalar con sudo crea archivos con propietario root, causando problemas futuros"},
            {"step": 5, "title": "En Docker: verificar volúmenes montados", "action": "Verifica que los volúmenes en docker-compose.yml tengan permisos correctos", "expected": "Contenedor puede leer/escribir en los volúmenes", "hint": "Añade user: '1000:1000' en el servicio de docker-compose si persiste"},
        ],
    },
    {
        "name": "Docker: contenedor no inicia o cae",
        "description": "Diagnostica problemas con contenedores Docker que fallan al arrancar.",
        "category": "docker",
        "trigger_patterns": ["docker", "container", "contenedor", "docker-compose", "image", "dockerfile", "exited", "exit code", "healthcheck"],
        "steps": [
            {"step": 1, "title": "Ver los logs del contenedor", "action": "Ejecuta: docker logs <nombre-contenedor> o docker-compose logs <servicio>", "expected": "Error específico visible en los logs", "hint": "El log casi siempre muestra exactamente qué falló"},
            {"step": 2, "title": "Verificar que la imagen existe", "action": "Ejecuta: docker images | grep <nombre>", "expected": "Imagen listada con su tag", "hint": "Si no existe, ejecuta: docker-compose build o docker pull <imagen>"},
            {"step": 3, "title": "Verificar conflicto de puertos", "action": "Ejecuta: netstat -tulpn | grep <puerto> para ver si el puerto ya está en uso", "expected": "Puerto libre (no aparece en LISTEN)", "hint": "Si está ocupado, cambia el puerto en docker-compose.yml o detén el proceso que lo usa"},
            {"step": 4, "title": "Verificar variables de entorno", "action": "Confirma que el archivo .env existe y tiene todas las variables requeridas", "expected": "Todas las variables del .env.example presentes en .env", "hint": "Docker Compose carga el .env del directorio actual automáticamente"},
            {"step": 5, "title": "Forzar recreación del contenedor", "action": "Ejecuta: docker-compose up -d --force-recreate <servicio>", "expected": "Contenedor recreado y en estado Up", "hint": "Útil cuando los cambios en .env no se aplican con solo restart"},
        ],
    },
    {
        "name": "Git: conflictos y errores comunes",
        "description": "Resuelve conflictos de merge, estado detached HEAD y otros errores de Git.",
        "category": "git",
        "trigger_patterns": ["git", "merge conflict", "detached head", "branch", "rebase", "conflict", "stash", "untracked"],
        "steps": [
            {"step": 1, "title": "Ver el estado actual del repositorio", "action": "Ejecuta: git status", "expected": "Lista de archivos modificados, en conflicto o sin trackear", "hint": "Archivos en conflicto aparecen como 'both modified'"},
            {"step": 2, "title": "Resolver conflictos de merge", "action": "Abre cada archivo en conflicto, busca <<<<<<< y edita manualmente para quedarte con los cambios correctos", "expected": "Sin marcadores <<<, ===, >>> en los archivos", "hint": "Después de resolver: git add <archivo> && git commit"},
            {"step": 3, "title": "Salir de estado detached HEAD", "action": "Ejecuta: git checkout -b <nombre-rama> para crear una rama desde el estado actual", "expected": "Cambiado a nueva rama", "hint": "O usa git checkout main para descartar los cambios del detached HEAD"},
            {"step": 4, "title": "Guardar cambios temporalmente con stash", "action": "Ejecuta: git stash push -m 'descripción' para guardar cambios sin commitear", "expected": "Directorio de trabajo limpio", "hint": "Recupera los cambios después con: git stash pop"},
            {"step": 5, "title": "Sincronizar con el remoto", "action": "Ejecuta: git fetch origin && git pull origin <rama>", "expected": "Rama local actualizada con el remoto", "hint": "Si hay conflictos al hacer pull, resuélvelos con el paso 2"},
        ],
    },
    {
        "name": "Variable de entorno no definida",
        "description": "Diagnostica errores causados por variables de entorno faltantes o mal configuradas.",
        "category": "environment",
        "trigger_patterns": ["undefined", "env", ".env", "environment variable", "variable de entorno", "keyerror", "process.env", "os.environ", "not defined", "missing"],
        "steps": [
            {"step": 1, "title": "Identificar la variable faltante", "action": "Lee el error — suele indicar el nombre exacto: KeyError: 'VARIABLE' o process.env.VARIABLE is undefined", "expected": "Nombre de la variable identificado", "hint": "En Python es KeyError o os.environ['VAR']; en Node.js es process.env.VAR undefined"},
            {"step": 2, "title": "Verificar que el archivo .env existe", "action": "Ejecuta: ls -la .env o dir .env (Windows)", "expected": "Archivo .env presente en la raíz del proyecto", "hint": "Si no existe, cópialo desde: cp .env.example .env"},
            {"step": 3, "title": "Verificar que la variable está en .env", "action": "Abre .env y busca la variable por nombre", "expected": "VARIABLE=valor presente en .env", "hint": "Revisa .env.example para ver todas las variables requeridas"},
            {"step": 4, "title": "Recargar variables de entorno", "action": "Reinicia el proceso o servidor después de editar .env", "expected": "Sin error de variable indefinida", "hint": "En Docker: docker-compose up -d --force-recreate. En Node.js/Python: reinicia el proceso"},
            {"step": 5, "title": "Verificar que el valor no está vacío", "action": "Comprueba que la variable tiene valor: VARIABLE=valor (no solo VARIABLE=)", "expected": "Variable con valor no vacío", "hint": "Una variable vacía (VARIABLE=) puede causar el mismo error que no existir"},
        ],
    },
]


# ── Service functions ─────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    count = await db.execute(select(func.count()).select_from(TroubleshootingFlow))
    if count.scalar() > 0:
        return
    for flow in SEED_FLOWS:
        db.add(TroubleshootingFlow(**flow))
    await db.commit()


async def identify_error(db: AsyncSession, error_message: str) -> list[dict]:
    text = error_message.lower()
    result = await db.execute(select(TroubleshootingFlow))
    flows = result.scalars().all()

    scored: list[tuple[int, TroubleshootingFlow]] = []
    for flow in flows:
        score = sum(1 for p in flow.trigger_patterns if p.lower() in text)
        if score > 0:
            scored.append((score, flow))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [_serialize(f, include_steps=False) for _, f in scored[:3]]


async def get_flow(db: AsyncSession, flow_id: int) -> dict | None:
    result = await db.execute(select(TroubleshootingFlow).where(TroubleshootingFlow.id == flow_id))
    flow = result.scalar_one_or_none()
    return _serialize(flow, include_steps=True) if flow else None


async def list_flows(db: AsyncSession, category: str | None = None) -> list[dict]:
    q = select(TroubleshootingFlow).order_by(TroubleshootingFlow.category, TroubleshootingFlow.name)
    if category:
        q = q.where(TroubleshootingFlow.category == category)
    result = await db.execute(q)
    return [_serialize(f, include_steps=False) for f in result.scalars().all()]


async def search_flows(db: AsyncSession, query: str) -> list[dict]:
    text = query.lower()
    result = await db.execute(select(TroubleshootingFlow))
    flows = result.scalars().all()
    matched = [
        f for f in flows
        if text in f.name.lower() or text in f.description.lower()
        or any(text in p for p in f.trigger_patterns)
        or text in f.category.lower()
    ]
    return [_serialize(f, include_steps=False) for f in matched]


def _serialize(f: TroubleshootingFlow, include_steps: bool = True) -> dict:
    data: dict = {
        "id": f.id,
        "name": f.name,
        "description": f.description,
        "category": f.category,
        "trigger_patterns": f.trigger_patterns,
        "step_count": len(f.steps),
    }
    if include_steps:
        data["steps"] = f.steps
    return data
