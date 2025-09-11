# Alerta Vía 🚨

**Plataforma de Seguridad Ciudadana Predictiva**

---

## Descripción del Proyecto 🗺 

**Alerta Vía** es una aplicación web diseñada para fortalecer la seguridad ciudadana mediante el uso de tecnologías modernas.  

### Objetivo General 🎯
- Visualizar incidentes de seguridad (hurtos, violencia, etc.) en un **mapa interactivo**.
- Predecir zonas de mayor riesgo utilizando **modelos de machine learning**.
- Trazar **rutas seguras** que minimicen la exposición a zonas críticas.
- Informar a la ciudadanía y apoyar a las autoridades en la **planificación de políticas de prevención**.

---

## Tecnologías Principales 🛠️

### Frontend
- **Angular** (SPA - Single Page Aplication)
- Integración con **Open Street Map**

### Backend
- **NestJS** como API Gateway
- Conexión a **PostgreSQL** (Neon) mediante **Prisma ORM**
- Módulo `DatabaseDAO` para consultas y persistencia
- Orquestación de servicios:
  - Open Street Map API
  - Medata API
  - ML Service (FastAPI en Python)

### Machine Learning Service
- **Python + FastAPI**
- Modelos predictivos de zonas de riesgo
- Integración con el backend

### Base de Datos
- **PostgreSQL en Neon** (Version Gratuita)

---

## 🏗️ Arquitectura

- Arquitectura **cliente-servidor con microservicios**.  
- Backend como **API Gateway**.  
- Estilo **Hexagonal / Ports & Adapters**:
  - Cada integración externa (DB, Maps, Medata, ML) aislada mediante su propio DAO.

---

## ⚙️ CI/CD y Despliegue (En Desarrollo)

- **CI/CD con GitHub Actions**
  - Ejecuta test y build en cada push.
  - Despliegues automáticos por módulo.

### Servicios Gratuitos a usar con la gestion en la nube:
- **Frontend:** Vercel  
- **Backend:** Render (Version Gratuita)  
- **ML Service:** Render (Version Gratuita)  
- **Base de Datos:** Neon (PostgreSQL en la nube)

Render hace **auto-deploy** cuando se realiza un push al repositorio.

---
