from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- CÓDIGO ADICIONADO POR NÓS ---
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
from app.models.domain_models import *
from dotenv import load_dotenv

load_dotenv()
import geoalchemy2
from pgvector.sqlalchemy import Vector
# ---------------------------------

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Seleciona o banco de acordo com o arquivo de configuração.
arquivo_configuracao = os.path.basename(
    config.config_file_name or ""
)

if arquivo_configuracao == "alembic_test.ini":
    nome_variavel = "TEST_DATABASE_URL"
else:
    nome_variavel = "DATABASE_URL"

url_banco = os.getenv(nome_variavel)

if not url_banco:
    raise RuntimeError(
        f"A variável {nome_variavel} não foi configurada."
    )

# Define a URL que será utilizada nas migrações.
config.set_main_option(
    "sqlalchemy.url",
    url_banco.replace("%", "%%")
)


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

def include_name(name, type_, parent_names):
    """
    Considera apenas as tabelas definidas nos modelos
    SQLAlchemy do NexTrip durante o autogenerate.
    """
    if type_ == "table":
        return parent_names.get("schema_qualified_table_name") in target_metadata.tables

    return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here. By skipping the Engine creation we don't
    even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_name=include_name,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()



def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
