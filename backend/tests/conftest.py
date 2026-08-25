"""
Fixtures de teste: sobe a app com um banco SQLite em memória, substituindo
a dependência get_db. Cria as tabelas via metadata do SQLAlchemy.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.domain.enums import PerfilUsuario
from app.infrastructure.database.models import (
    ModalidadeModel,
    PoloModel,
    TurmaModel,
    UsuarioModel,
)
from app.main import app


@pytest.fixture(autouse=True)
def _resetar_rate_limiter():
    """O rate limiter é um contador global em memória (ver app/core/rate_limit.py)
    — sem isso, os testes compartilhariam o mesmo contador entre si e um teste
    esbarraria no limite por causa de chamadas de login de outro teste."""
    limiter.reset()
    yield

# SQLite em memória compartilhada entre conexões
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_basico(db_session):
    """Cria MASTER, 2 polos, gestores de cada polo, modalidade e turmas."""
    master = UsuarioModel(
        nome="Master", email="master@test.com", senha_hash=hash_password("senha123"),
        perfil=PerfilUsuario.MASTER.value, polo_id=None,
    )
    db_session.add(master)
    db_session.flush()

    polo_a = PoloModel(nome="Polo A", endereco="End A", status="ATIVO")
    polo_b = PoloModel(nome="Polo B", endereco="End B", status="ATIVO")
    db_session.add_all([polo_a, polo_b])
    db_session.flush()

    gestor_a = UsuarioModel(
        nome="Gestor A", email="gestor.a@test.com", senha_hash=hash_password("senha123"),
        perfil=PerfilUsuario.GESTOR_POLO.value, polo_id=polo_a.id,
    )
    gestor_b = UsuarioModel(
        nome="Gestor B", email="gestor.b@test.com", senha_hash=hash_password("senha123"),
        perfil=PerfilUsuario.GESTOR_POLO.value, polo_id=polo_b.id,
    )
    db_session.add_all([gestor_a, gestor_b])
    db_session.flush()

    modalidade = ModalidadeModel(nome="Judô", descricao="Arte marcial")
    db_session.add(modalidade)
    db_session.flush()

    db_session.commit()
    return {
        "master": master, "polo_a": polo_a, "polo_b": polo_b,
        "gestor_a": gestor_a, "gestor_b": gestor_b, "modalidade": modalidade,
    }


def login(client, email: str, senha: str = "senha123") -> str:
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": senha})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
