# QA Checklist — Sprint [N] — Gestor de Horas
**Proceso:** Gestor de Horas — [módulo bajo test]
**Entorno:** Homologación
**Fecha QA:** [YYYY-MM-DD]
**Dev Analista:** [nombre]
**Estado general:** 🟡 EN PROGRESO

---

## Resultados por criterio

| ID     | Criterio (del PDD)                                        | Verificación                          | Estado     | Bug    |
|--------|-----------------------------------------------------------|---------------------------------------|------------|--------|
| CRT-01 | El usuario puede iniciar sesión con credenciales válidas  | TC-SMOKE-02 Robot — login 200 + JWT   | ⬜ PENDING | —      |
| CRT-02 | Credenciales incorrectas retornan 401                     | TC-SMOKE-03 Robot — login 401         | ⬜ PENDING | —      |
| CRT-03 | Registro de horas acepta valores de 0.25 a 24hs           | test_horas_validas_se_persisten pytest| ⬜ PENDING | —      |
| CRT-04 | Solo roles con permiso ven horas del equipo               | test_tiene_permiso_* pytest           | ⬜ PENDING | —      |
| CRT-05 | El Excel generado tiene las columnas oficiales correctas  | TC-SMOKE-07 Robot — export 200        | ⬜ PENDING | —      |
| CRT-06 | Feriados México no piden carga de horas                   | test_feriado_* pytest integration     | ⬜ PENDING | —      |
| CRT-07 | Usuario inactivo no puede iniciar sesión                  | test_usuario_inactivo_* pytest unit   | ⬜ PENDING | —      |
| CRT-08 | Timer registra horas correctamente al pausar              | test_timer_* pytest unit              | ⬜ PENDING | —      |

---

## Cómo ejecutar los tests

```bash
# ── Tests unitarios ────────────────────────────────────────
cd backend
pytest -m unit -v

# ── Tests de integración ───────────────────────────────────
pytest -m integration -v

# ── Smoke tests (Robot Framework) ─────────────────────────
robot --outputdir results/smoke \
      --variable ENTORNO:homologacion \
      tests/e2e/robot/suites/smoke_suite.robot

# ── Suite completa con reporte Allure ─────────────────────
pytest --alluredir=results/allure
allure serve results/allure

# ── Solo tests fallidos del último run ────────────────────
pytest --lf -v
```

---

## Bugs registrados

_(sin bugs al inicio del sprint)_

---

## Firma

QA completado el [fecha] por [nombre].
