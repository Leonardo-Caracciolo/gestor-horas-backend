*** Settings ***
Documentation    Keywords compartidos — Gestor de Horas
Library          RequestsLibrary
Library          Collections
Library          DateTime
Library          OperatingSystem


*** Keywords ***

Initialize Test Environment
    [Documentation]    Prepara el entorno antes de cada suite.
    Log    Iniciando suite de tests — Gestor de Horas    INFO
    ${time}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Set Global Variable    ${TEST_START_TIME}    ${time}

Clean Test Environment
    [Documentation]    Limpia recursos post-suite.
    Log    Suite finalizada — ${TEST_START_TIME}    INFO

Obtener Token
    [Documentation]    Realiza login y retorna el token JWT.
    ...
    ...    Args:
    ...        username: Email o username del usuario.
    ...        password: Contraseña del usuario.
    ...
    ...    Returns:
    ...        str: Token JWT de acceso.
    [Arguments]    ${username}    ${password}
    ${payload}=    Create Dictionary
    ...    username=${username}
    ...    password=${password}
    ${response}=    POST    ${BASE_URL}/auth/login    json=${payload}
    Status Should Be    200    ${response}
    ${body}=    Set Variable    ${response.json()}
    ${token}=    Get From Dictionary    ${body}    access_token
    [Return]    ${token}

Headers Con Token
    [Documentation]    Crea un dict de headers con el token Bearer.
    [Arguments]    ${token}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    [Return]    ${headers}
