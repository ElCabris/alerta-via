# 🚀 Instrucciones para Iniciar el Proyecto

## Pasos para ejecutar la aplicación completa

### 1. Entrenar el Modelo (primera vez o cuando necesites actualizar)

Abre una terminal y ejecuta:

```bash
cd modelo_ML
python train_density_model.py
```

Esto generará:
- `backend/models/density_hotspot_model.pkl` - Modelo de densidad entrenado
- `backend/models/density_model_stats.json` - Estadísticas del modelo

**Nota:** Este paso puede tardar varios minutos dependiendo del tamaño del dataset.

### 2. Iniciar el Backend (Servidor FastAPI)

Abre una **nueva terminal** y ejecuta:

```bash
cd backend
python run_server.py
```

El servidor estará disponible en: `http://localhost:8000`

**Verificación:** Abre tu navegador en `http://localhost:8000/docs` para ver la documentación interactiva de la API.

### 3. Iniciar el Frontend (Angular)

Abre una **tercera terminal** y ejecuta:

```bash
cd frontend
npm start
```

La aplicación estará disponible en: `http://localhost:4200`

### 4. Usar la Aplicación

1. Abre `http://localhost:4200` en tu navegador
2. Navega al dashboard
3. Completa el formulario (edad, sexo, estado civil, medio de transporte)
4. Haz clic en el mapa para establecer:
   - **Primer clic:** Origen (marcador verde "O")
   - **Segundo clic:** Destino (marcador rojo "D")
5. Haz clic en "Trazar Ruta Segura"
6. La ruta se mostrará con colores según el nivel de riesgo:
   - 🔴 **Rojo:** Riesgo alto (> 70%)
   - 🟡 **Amarillo:** Riesgo medio (40-70%)
   - 🟢 **Verde:** Riesgo bajo (< 40%)

## ⚠️ Solución de Problemas

### Error: "No se puede conectar al servidor backend"
- **Solución:** Asegúrate de que el backend esté ejecutándose (paso 2)
- Verifica que no haya otro proceso usando el puerto 8000

### Error: "El modelo no está disponible"
- **Solución:** Ejecuta primero `train_density_model.py` (paso 1)

### Error de Geolocalización
- **Normal:** Si no permites la ubicación o no estás en HTTPS/localhost
- La aplicación usará Medellín como ubicación por defecto

### Error de CORS
- El backend ya está configurado para permitir CORS desde cualquier origen
- Si persiste, verifica que el backend esté ejecutándose

## 📝 Notas Importantes

- El backend debe estar corriendo **antes** de usar el frontend
- El modelo debe estar entrenado **antes** de iniciar el backend
- Puedes usar el dashboard incluso sin geolocalización (usa clics en el mapa)

## 🔍 Verificar que Todo Funciona

1. **Backend:** `http://localhost:8000/health` debería devolver `{"status": "healthy"}`
2. **Frontend:** Debería cargar sin errores en la consola
3. **Integración:** Intenta trazar una ruta y verifica que aparezcan colores en el mapa

---

**¡Listo para usar!** 🎉

