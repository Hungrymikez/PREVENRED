"""Pruebas de la API de punta a punta (CU-01 y CU-02)."""

BODY = {
    "full_name": "Camila Pérez",
    "email": "camila@mail.com",
    "password": "clave-segura-1",
    "role": "ciudadano",
    "neighborhood": "Cuba",
    "accepted_terms": True,
}


def test_registro_y_login_y_me(client):
    assert client.post("/api/v1/auth/register", json=BODY).status_code == 201
    creds = {"email": BODY["email"], "password": BODY["password"]}
    r = client.post("/api/v1/auth/login", json=creds)
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "camila@mail.com"


def test_correo_duplicado_da_409(client):  # CU-01 E1
    client.post("/api/v1/auth/register", json=BODY)
    assert client.post("/api/v1/auth/register", json=BODY).status_code == 409


def test_login_incorrecto_es_generico(client):  # CU-02 E1
    client.post("/api/v1/auth/register", json=BODY)
    r = client.post("/api/v1/auth/login", json={"email": BODY["email"], "password": "mala-clave"})
    assert r.status_code == 401
    r2 = client.post("/api/v1/auth/login", json={"email": "nadie@mail.com", "password": "x"})
    assert r.json()["error"]["message"] == r2.json()["error"]["message"]


def test_registro_rechaza_rol_administrador(client):  # criterio de aceptación CU-01
    body = {**BODY, "role": "administrador"}
    assert client.post("/api/v1/auth/register", json=body).status_code == 422


def test_me_sin_token_da_401(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_consecutivo_genera_tokens_diferentes(client):
    """Valida que dos inicios de sesión consecutivos generen tokens distintos y válidos."""
    client.post("/api/v1/auth/register", json=BODY)
    creds = {"email": BODY["email"], "password": BODY["password"]}

    r1 = client.post("/api/v1/auth/login", json=creds)
    r2 = client.post("/api/v1/auth/login", json=creds)

    assert r1.status_code == 200
    assert r2.status_code == 200

    token1 = r1.json()["access_token"]
    token2 = r2.json()["access_token"]

    assert token1 != token2, "Los tokens de peticiones consecutivas deben ser únicos"

    # Ambos tokens deben ser válidos y permitir acceder a /me sin ExpiredSignatureError
    me1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}"})
    me2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"})

    assert me1.status_code == 200
    assert me2.status_code == 200
    assert me1.json()["email"] == BODY["email"]
    assert me2.json()["email"] == BODY["email"]
