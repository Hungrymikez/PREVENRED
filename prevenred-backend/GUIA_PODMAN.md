# Guía: MongoDB local con Podman (sin Docker)

Podman no necesita el servicio permanente que usa Docker Desktop. En Windows y Mac igual corre los
contenedores dentro de una máquina virtual pequeña, pero esa máquina se puede limitar (paso 2) para
que gaste poco. Para PrevenRed solo necesitas **un contenedor: MongoDB**.

> Los comandos son los estándar de Podman; en el entorno donde se preparó el kit no se pudo
> ejecutar Podman, así que si alguno falla en tu equipo, copia el error y lo resolvemos.

**¿Quieres cero contenedores?** Usa MongoDB Atlas gratis (sección 8): no instalas nada y además trae
*replica set* (transacciones). Para este proyecto es la opción más liviana.

---

## 1. Instalar Podman

### Windows 10/11
1. Activa WSL2 (una sola vez; pide reiniciar): abre PowerShell **como administrador**
   ```powershell
   wsl --install
   ```
2. Instala Podman:
   ```powershell
   winget install RedHat.Podman
   ```
   Si `winget` no lo encuentra, descarga el instalador desde https://podman.io y ábrelo.
3. Cierra y abre la terminal, y comprueba: `podman --version`

### Linux
```bash
sudo apt install podman        # Debian/Ubuntu
sudo dnf install podman        # Fedora
```
En Linux no hay máquina virtual: salta al paso 3.

### macOS
```bash
brew install podman
```

## 2. Crear la máquina de Podman (solo Windows y Mac)

Limita los recursos para que el equipo no se ahogue (2 CPU y 2 GB de memoria alcanzan para MongoDB):

```powershell
podman machine init --cpus 2 --memory 2048
podman machine start
podman info
```

Si ya la habías creado sin límites: `podman machine stop`, luego
`podman machine set --cpus 2 --memory 2048` y `podman machine start`.

**Cada vez que reinicies el computador** vuelve a hacer `podman machine start` (en Windows/Mac).

## 3. Levantar MongoDB

Desde la carpeta del proyecto (usa el archivo `compose.yaml` del kit):

```powershell
podman compose up -d
```

`podman compose` necesita un proveedor instalado. Si te dice que no lo encuentra:

```powershell
pip install podman-compose
podman-compose up -d
```

**Alternativa sin compose** (un solo comando, funciona siempre):

```powershell
podman run -d --name mongo -p 27017:27017 -v mongo_data:/data/db docker.io/library/mongo:7 --wiredTigerCacheSizeGB 0.25
```

Notas:
- Siempre `docker.io/library/mongo:7` completo: Podman no asume el registro y de lo contrario
  pregunta o falla con «short-name resolution».
- `-v mongo_data:/data/db` guarda tus datos aunque borres el contenedor.
- `--wiredTigerCacheSizeGB 0.25` limita la memoria de caché de Mongo.

## 4. Comprobar que funciona

```powershell
podman ps                      # debe aparecer "mongo" con estado Up
podman logs mongo              # últimas líneas del servidor
```

Prueba desde Python (con el entorno virtual del proyecto activo):

```powershell
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000).server_info()['version'])"
```

Debe imprimir un número de versión (por ejemplo `7.0.x`). Tu `.env` ya apunta a ese servidor:
`MONGO_URI=mongodb://localhost:27017`.

## 5. Correr el backend y las pruebas contra Mongo real

```powershell
uvicorn prevenred.main:app --reload --app-dir src        # http://localhost:8000/docs
```

Pruebas normales (no necesitan Mongo): `pytest -q` → `16 passed, 1 skipped`.
Pruebas contra Mongo real (verifican índices únicos de verdad):

```powershell
$env:MONGO_TEST_URI="mongodb://localhost:27017"          # PowerShell
pytest -q                                                 # → 17 passed
```
En Linux/Mac: `MONGO_TEST_URI=mongodb://localhost:27017 pytest -q`.
Las pruebas crean una base temporal y la borran al terminar.

## 6. Uso diario

| Acción | Comando |
|---|---|
| Encender (Windows/Mac) | `podman machine start` |
| Iniciar Mongo | `podman start mongo` |
| Apagar Mongo | `podman stop mongo` |
| Apagar todo y liberar memoria | `podman stop mongo` y `podman machine stop` |
| Ver estado | `podman ps -a` |
| Ver la base con una consola | `podman exec -it mongo mongosh` |
| **Borrar todos los datos y empezar limpio** | `podman rm -f mongo` y `podman volume rm mongo_data` |

Con compose: `podman compose down` apaga y quita el contenedor (los datos quedan en el volumen).

## 7. Problemas comunes

| Síntoma | Causa y solución |
|---|---|
| `Cannot connect to Podman` / `unable to connect to Podman socket` | La máquina está apagada: `podman machine start` |
| `short-name resolution` o pide elegir registro | Usa el nombre completo `docker.io/library/mongo:7` |
| `address already in use` en el puerto 27017 | Otro Mongo está corriendo. Ciérralo o cambia a `-p 27018:27017` y usa `MONGO_URI=mongodb://localhost:27018` |
| `ServerSelectionTimeoutError` al arrancar la API | Mongo no está iniciado: `podman ps`; si no aparece, `podman start mongo` |
| `podman compose` no existe o falla | `pip install podman-compose` y usa `podman-compose up -d`, o el comando `podman run` de arriba |
| La máquina consume mucha memoria | Revisa el paso 2 (`--memory 2048`) y apágala cuando no programes |

## 8. Alternativa sin contenedores: MongoDB Atlas (gratis)

1. Crea una cuenta en https://www.mongodb.com/atlas y un clúster gratuito (M0).
2. En *Database Access* crea un usuario y contraseña. En *Network Access* permite tu IP.
3. En *Connect → Drivers* copia la cadena `mongodb+srv://...`.
4. Pégala en tu `.env`:
   ```
   MONGO_URI=mongodb+srv://usuario:contraseña@cluster0.xxxxx.mongodb.net
   MONGO_DB_NAME=pereira_responde
   ```
5. No ejecutes `podman`. Con Atlas puedes usar transacciones (es *replica set*).

Cuidado: el plan gratuito es compartido y tiene límites; no uses datos reales de personas ahí.

## 9. Avanzado (solo si algún día necesitas transacciones en local)

Las transacciones multi-documento exigen *replica set*. Un nodo local de prueba:

```powershell
podman rm -f mongo
podman run -d --name mongo -p 27017:27017 -v mongo_data:/data/db docker.io/library/mongo:7 --replSet rs0 --bind_ip_all
podman exec mongo mongosh --eval "rs.initiate()"
```
y en `.env`: `MONGO_URI=mongodb://localhost:27017/?directConnection=true`.
El kit **no lo necesita** hasta las fases 2 y 4 (cambio de modo y estado de incidente); decide entonces.
