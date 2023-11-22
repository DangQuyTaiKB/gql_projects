import sqlalchemy
import datetime

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Integer,
    DateTime,
    ForeignKey,
    Sequence,
    Table,
    Boolean,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid


from uuid import uuid4, UUID
from sqlalchemy import Column, Uuid
uuid = uuid4


BaseModel = declarative_base()

def UUIDFKey(comment=None, nullable=True, **kwargs):
    return Column(Uuid, index=True, comment=comment, nullable=nullable, **kwargs)

def UUIDColumn():
    return Column(Uuid, primary_key=True, comment="primary key", default=uuid)

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#


class ProjectModel(BaseModel):
    __tablename__ = "projects"

    id = UUIDColumn()

    name = Column(String)
    startdate = Column(DateTime)
    enddate = Column(DateTime)

    projecttype_id = Column(ForeignKey("projecttypes.id"), index=True)
    projecttype = relationship("ProjectTypeModel", back_populates="projects")

    group_id = UUIDFKey(nullable=True)#Column(ForeignKey("groups.id"), index=True)
    #group = relationship("groupModel")

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)


class ProjectTypeModel(BaseModel):
    __tablename__ = "projecttypes"

    id = UUIDColumn()
    name = Column(String)
    name_en = Column(String)

    category_id = Column(ForeignKey("projectcategories.id"), index=True, nullable=True)
    projects = relationship("ProjectModel", back_populates="projecttype")

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)


class ProjectCategoryModel(BaseModel):
    __tablename__ = "projectcategories"

    id = UUIDColumn()
    name = Column(String)
    name_en = Column(String)

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)

class FinanceModel(BaseModel):
    __tablename__ = "projectfinances"

    id = UUIDColumn()
    name = Column(String)
    amount = Column(sqlalchemy.types.DECIMAL(precision=13, scale=3))
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())

    project_id = Column(ForeignKey("projects.id"), index=True)

    financetype_id = Column(ForeignKey("projectfinancetypes.id"), index=True)
    financetype = relationship("FinanceTypeModel", back_populates="finances")
    
    event_id = UUIDFKey(nullable=True) # ucetni obdobi

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)


class FinanceTypeModel(BaseModel):
    __tablename__ = "projectfinancetypes"

    id = UUIDColumn()
    name = Column(String)
    name_en = Column(String)

    finances = relationship("FinanceModel", back_populates="financetype")

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)

class FinanceCategory(BaseModel):
    __tablename__ = "projectfinancecategories"

    id = UUIDColumn()
    name = Column(String)
    name_en = Column(String)

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)


class MilestoneModel(BaseModel):
    __tablename__ = "projectmilestones"

    id = UUIDColumn()
    name = Column(String)
    startdate = Column(DateTime)
    enddate = Column(DateTime)

    project_id = Column(ForeignKey("projects.id"), index=True)

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)

class MilestoneLinkModel(BaseModel):
    __tablename__ = "projectmilestonelinks"

    id = UUIDColumn()

    previous_id = Column(ForeignKey("projectmilestones.id"), index=True, nullable=True)
    next_id = Column(ForeignKey("projectmilestones.id"), index=True, nullable=True)

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)

###########################################################################################################################

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine


async def startEngine(connectionstring, makeDrop=False, makeUp=True):
    """Provede nezbytne ukony a vrati asynchronni SessionMaker"""
    asyncEngine = create_async_engine(connectionstring)

    async with asyncEngine.begin() as conn:
        if makeDrop:
            await conn.run_sync(BaseModel.metadata.drop_all)
            print("BaseModel.metadata.drop_all finished")
        if makeUp:
            try:
                await conn.run_sync(BaseModel.metadata.create_all)
                print("BaseModel.metadata.create_all finished")
            except sqlalchemy.exc.NoReferencedTableError as e:
                print(e)
                print("Unable automaticaly create tables")
                return None

    async_sessionMaker = sessionmaker(
        asyncEngine, expire_on_commit=False, class_=AsyncSession
    )
    return async_sessionMaker


import os


def ComposeConnectionString():
    """Odvozuje connectionString z promennych prostredi (nebo z Docker Envs, coz je fakticky totez).
    Lze predelat na napr. konfiguracni file.
    """
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "example")
    database = os.environ.get("POSTGRES_DB", "data")
    hostWithPort = os.environ.get("POSTGRES_HOST", "postgres:5432")

    driver = "postgresql+asyncpg"  # "postgresql+psycopg2"
    connectionstring = f"{driver}://{user}:{password}@{hostWithPort}/{database}"

    return connectionstring
