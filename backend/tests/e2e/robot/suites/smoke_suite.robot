*** Settings ***
Documentation       Suite de Smoke Tests — Gestor de Horas
...                 Verifica que los endpoints críticos del sistema
...                 responden correctamente antes de cada release.
...
...                 Ejecutar con:
...                 robot --outputdir results/smoke
...                       --variable ENTORNO:homologacion
...                       tests/e2e/robot/suites/smoke_suite.robot

Library             Collections
Library             RequestsLibrary
Library             DateTime
Resource            ../resources/keywords.resource
Resource            ../resources/variables.resource

Suite Setup         Initialize Test Environment
Suite Teardown      Clean Test Environment


*** Variables ***
# Override desde CLI: --variable BASE_URL:http://mi-servidor
${BASE_URL}         http://localhost:8000/api/v1
${ADMIN_USER}       admin@empresa.com
${ADMIN_PASS}       TestPassword123!


*** Test Cases ***

TC-SMOKE-01 Health Check — API responde 200
    [Documentation]    Verifica que la API está levantada y responde.
    [Tags]    smoke    p1    health
    ${response}=    GET    ${BASE_URL.replace('/api/v1', '')}/health
    Status Should Be    200    ${response}
    ${body}=    Set Variable    ${response.json()}
    Should Be Equal    ${body}[status]    ok

TC-SMOKE-02 Login — Usuario válido recibe token JWT
    [Documentation]    Verifica que el endpoint de login retorna un JWT válido
    ...                para un usuario activo con credenciales correctas.
    [Tags]    smoke    p1    auth
    ${token}=    Obtener Token    ${ADMIN_USER}    ${ADMIN_PASS}
    Should Not Be Empty    ${token}
    Should Contain    ${token}    .    # JWT tiene 3 partes separadas por "."

TC-SMOKE-03 Login — Credenciales incorrectas retorna 401
    [Documentation]    El login con contraseña incorrecta debe retornar 401.
    [Tags]    smoke    p1    auth    error
    ${response}=    POST    ${BASE_URL}/auth/login
    ...    json={"username": "${ADMIN_USER}", "password": "Incorrecta"}
    Status Should Be    401    ${response}

TC-SMOKE-04 Proyectos — Listado accesible con token válido
    [Documentation]    El endpoint de proyectos debe retornar 200 con token.
    [Tags]    smoke    p1    proyectos
    ${token}=    Obtener Token    ${ADMIN_USER}    ${ADMIN_PASS}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${response}=    GET    ${BASE_URL}/proyectos    headers=${headers}
    Status Should Be    200    ${response}

TC-SMOKE-05 Horas — Endpoint accesible para usuario autenticado
    [Documentation]    El endpoint de horas debe retornar 200 con token.
    [Tags]    smoke    p1    horas
    ${token}=    Obtener Token    ${ADMIN_USER}    ${ADMIN_PASS}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${response}=    GET    ${BASE_URL}/horas/semana-actual    headers=${headers}
    Status Should Be    200    ${response}

TC-SMOKE-06 Horas — Sin token retorna 401
    [Documentation]    El endpoint de horas sin token debe retornar 401.
    [Tags]    smoke    p1    horas    security
    ${response}=    GET    ${BASE_URL}/horas/semana-actual
    Status Should Be    401    ${response}

TC-SMOKE-07 Export — Excel se genera sin errores
    [Documentation]    Verifica que el endpoint de exportación de Excel
    ...                genera un archivo válido sin lanzar errores.
    [Tags]    smoke    p2    export
    ${token}=    Obtener Token    ${ADMIN_USER}    ${ADMIN_PASS}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${response}=    GET    ${BASE_URL}/export/excel    headers=${headers}
    Status Should Be    200    ${response}
    ${content_type}=    Get From Dictionary    ${response.headers}    content-type
    Should Contain    ${content_type}    spreadsheetml
