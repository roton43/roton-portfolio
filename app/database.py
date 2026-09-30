import os
from pathlib import Path
from sqlalchemy import create_engine, Integer, String, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).resolve().parent.parent


class Base(DeclarativeBase):
    pass


class ProfileRow(Base):
    __tablename__ = 'profile'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


class Record(Base):
    __tablename__ = 'records'
    __table_args__ = (UniqueConstraint('kind', 'slug', name='uq_record_kind_slug'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)
    slug: Mapped[str] = mapped_column(String(160))
    data: Mapped[dict] = mapped_column(JSON)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[str] = mapped_column(String(40))


def database_url():
    url = os.getenv('DATABASE_URL', '')
    if not url:
        (ROOT / 'data').mkdir(exist_ok=True)
        return f'sqlite:///{ROOT / "data" / "portfolio.db"}'
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql+psycopg://', 1)
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


def build_database():
    url = database_url()
    if os.getenv('APP_ENV') == 'production' and not url.startswith('postgresql+psycopg://'):
        raise RuntimeError('Production requires persistent PostgreSQL. Set DATABASE_URL.')
    options = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite:') else {'pool_size': 3, 'max_overflow': 2, 'pool_recycle': 300}
    engine = create_engine(url, pool_pre_ping=True, **options)
    return engine, sessionmaker(engine, expire_on_commit=False)
