# Despliegue en Railway

## Paso 1: Crear cuenta en Railway

1. Ve a https://railway.app
2. Inicia sesion con GitHub

## Paso 2: Crear nuevo proyecto

1. Click en **"New Project"**
2. Selecciona **"Empty Project"**

## Paso 3: Agregar PostgreSQL

1. Click en **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway creara la base de datos automaticamente
3. Copia la variable `DATABASE_URL` (la necesitaras)

## Paso 4: Desplegar Backend

1. Click en **"+ New"** → **"GitHub Repo"**
2. Selecciona tu repositorio `vetassist`
3. En la configuracion:
   - **Root Directory**: `backend`
   - **Builder**: Dockerfile

4. Agrega las **variables de entorno**:
   ```
   DATABASE_URL=<pegar de PostgreSQL>
   SECRET_KEY=<genera-una-clave-segura-de-32-caracteres>
   OPENAI_API_KEY=sk-...
   TWILIO_ACCOUNT_SID=AC...
   TWILIO_AUTH_TOKEN=...
   TWILIO_PHONE_NUMBER=+1...
   CORS_ORIGINS=https://tu-frontend.railway.app
   ```

5. Click en **"Deploy"**
6. Una vez desplegado, ve a **Settings** → **Networking** → **Generate Domain**
7. Copia la URL del backend (ej: `https://vetassist-backend.up.railway.app`)

## Paso 5: Desplegar Frontend

1. Click en **"+ New"** → **"GitHub Repo"**
2. Selecciona el mismo repositorio
3. En la configuracion:
   - **Root Directory**: `frontend`
   - **Builder**: Dockerfile

4. Agrega las **variables de entorno**:
   ```
   NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app
   ```

5. **IMPORTANTE**: En Build Settings, agrega el build argument:
   ```
   NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app
   ```

6. Click en **"Deploy"**
7. Ve a **Settings** → **Networking** → **Generate Domain**

## Paso 6: Ejecutar migraciones

1. En el servicio del backend, abre **"Variables"**
2. Abre el **"Shell"** (terminal)
3. Ejecuta:
   ```bash
   alembic upgrade head
   ```

## Paso 7: Crear clinica inicial

En el shell del backend:
```python
python -c "
from app.database import SessionLocal
from app.models import Clinic, Staff
from passlib.hash import bcrypt
import uuid

db = SessionLocal()

# Crear clinica
clinic = Clinic(
    id=uuid.uuid4(),
    name='Mi Clinica Veterinaria',
    phone='+573001234567',
    email='clinica@ejemplo.com'
)
db.add(clinic)
db.commit()

# Crear usuario admin
staff = Staff(
    id=uuid.uuid4(),
    clinic_id=clinic.id,
    email='admin@ejemplo.com',
    password_hash=bcrypt.hash('password123'),
    name='Admin',
    role='admin'
)
db.add(staff)
db.commit()

print(f'Clinic ID: {clinic.id}')
print(f'Admin: admin@ejemplo.com / password123')
"
```

## URLs de acceso

Una vez desplegado:

- **Portal Veterinarios**: `https://tu-frontend.railway.app/login`
- **Portal Clientes**: `https://tu-frontend.railway.app/cliente/login?clinic=<CLINIC_ID>`

## Variables de entorno completas

### Backend
| Variable | Descripcion | Requerida |
|----------|-------------|-----------|
| DATABASE_URL | PostgreSQL connection string | Si |
| SECRET_KEY | JWT secret (min 32 chars) | Si |
| OPENAI_API_KEY | OpenAI API key | Si |
| TWILIO_ACCOUNT_SID | Twilio Account SID | Si |
| TWILIO_AUTH_TOKEN | Twilio Auth Token | Si |
| TWILIO_PHONE_NUMBER | Numero Twilio (+1...) | Si |
| CORS_ORIGINS | Frontend URL | Si |

### Frontend
| Variable | Descripcion | Requerida |
|----------|-------------|-----------|
| NEXT_PUBLIC_API_URL | URL del backend | Si |

## Costos estimados

Railway ofrece $5 USD gratis al mes, que cubre:
- ~500 horas de ejecucion
- Base de datos PostgreSQL pequena
- Ideal para desarrollo y demos

Para produccion, considera el plan Pro ($20/mes).
