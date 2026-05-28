# Cloudflare Tunnel — Exponer ATOS al Internet

## ¿Qué es?
Cloudflare Tunnel crea un túnel seguro entre tu PC y la red de Cloudflare,
exponiendo tu servidor local con una URL pública sin abrir puertos en tu router.

---

## Instalación de cloudflared (una sola vez)

### Windows
Descarga el instalador desde:
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

O via winget:
```powershell
winget install Cloudflare.cloudflared
```

### Verificar instalación
```powershell
cloudflared --version
```

---

## Levantar el tunnel temporal (URL cambia al reiniciar)

```powershell
# 1. Primero levanta Docker
docker-compose up -d

# 2. Luego abre el tunnel
cloudflared tunnel --url http://localhost:8002
```

Verás algo como:
```
Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):
https://abc-xyz-123.trycloudflare.com
```

---

## Actualizar el frontend con el nuevo URL

Cada vez que reinicies cloudflared obtienes un URL diferente.
Debes actualizar el frontend:

1. Abre `frontend/src/config.ts`
2. Cambia `BACKEND_URL` al nuevo URL del tunnel:
   ```typescript
   export const BACKEND_URL = "https://abc-xyz-123.trycloudflare.com";
   ```
3. Rebuild y deploy:
   ```powershell
   cd frontend
   npm run build
   npx gh-pages -d dist
   ```

---

## Tunnel fijo (URL permanente — gratis con cuenta Cloudflare)

Si quieres el mismo URL siempre:

1. Crea cuenta gratis en https://dash.cloudflare.com
2. Ve a Zero Trust → Networks → Tunnels
3. Crea un tunnel con nombre (ej: "atos-tunnel")
4. Sigue las instrucciones para instalar el conector
5. Configura el hostname público → localhost:8000

Con esto el URL nunca cambia y no necesitas actualizar el frontend.

---

## Flujo de trabajo diario

```powershell
# Cada vez que quieras que ATOS esté disponible públicamente:
docker-compose up -d
cloudflared tunnel --url http://localhost:8002

# Cuando termines:
docker-compose down
# (cerrar la ventana de cloudflared detiene el tunnel)
```

---

## URL de GitHub Pages (siempre disponible)

El frontend React está desplegado en:
https://<tu-usuario>.github.io/ATOS/

Cuando el tunnel está activo → funciona completamente.
Cuando el tunnel está apagado → muestra "Servidor offline".
