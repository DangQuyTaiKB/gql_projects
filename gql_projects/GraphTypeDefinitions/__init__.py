from typing import List, Union
import typing
from unittest import result
import strawberry
import uuid
from contextlib import asynccontextmanager


@asynccontextmanager
async def withInfo(info):
    asyncSessionMaker = info.context["asyncSessionMaker"]
    async with asyncSessionMaker() as session:
        try:
            yield session
        finally:
            pass


def AsyncSessionFromInfo(info):
    print(
        "obsolete function used AsyncSessionFromInfo, use withInfo context manager instead"
    )
    return info.context["session"]

def getLoaders(info):
    return info.context['all']
###########################################################################################################################
#
# zde definujte sve GQL modely
# - nove, kde mate zodpovednost
# - rozsirene, ktere existuji nekde jinde a vy jim pridavate dalsi atributy
#
###########################################################################################################################
# GQL PROJECT
import datetime
from gql_projects.GraphResolvers import (
    resolveProjectById,
    resolveProjectAll,
    resolveUpdateProject,
    resolveInsertProject,
)

class BaseGQLModel:
    @classmethod
    def getLoader(cls, info):
        pass

    @classmethod
    async def resolve_reference(cls, info: strawberry.types.Info, id: uuid.UUID):
        if id is None:
            return None
        loader = cls.getLoader(info)
        if isinstance(id, str): id = uuid.UUID(id)
        result = await loader.load(id)
        if result is not None:
            result.__strawberry_definition__ = cls.__strawberry_definition__  # little hack :)
        return result
  

@strawberry.federation.type(extend=True, keys=["id"])
class UserGQLModel:
    id: uuid.UUID = strawberry.federation.field(external=True)
    @classmethod
    async def resolve_reference(cls, info: strawberry.types.Info, id: uuid.UUID):
        return cls(id=id)

@strawberry.field(description="""Entity primary key""")
def resolve_id(self) -> uuid.UUID:
    return self.id

@strawberry.field(description="""Name """)
def resolve_name(self) -> str:
    return self.name

@strawberry.field(description="""English name""")
def resolve_name_en(self) -> str:
    return self.name_en

@strawberry.field(description="""Time of last update""")
def resolve_lastchange(self) -> datetime.datetime:
    return self.lastchange

@strawberry.field(description="""Time of entity introduction""")
def resolve_created(self) -> typing.Optional[datetime.datetime]:
    return self.created

async def resolve_user(user_id):
    result = None if user_id is None else await UserGQLModel.resolve_reference(user_id)
    return result
    
@strawberry.field(description="""Who created entity""")
async def resolve_createdby(self) -> typing.Optional["UserGQLModel"]:
    return await resolve_user(self.created_by)

@strawberry.field(description="""Who made last change""")
async def resolve_changedby(self) -> typing.Optional["UserGQLModel"]:
    return await resolve_user(self.changedby)


@strawberry.federation.type(
    keys=["id"], description="""Entity representing a project"""
)
class ProjectGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoaders(info).projects

    id = resolve_id
    name = resolve_name
    lastchange = resolve_lastchange
    changedby = resolve_changedby
    created = resolve_created
    createdby = resolve_createdby

    @strawberry.field(description="""Start date""")
    def startdate(self) -> datetime.date:
        return self.startdate

    @strawberry.field(description="""End date""")
    def enddate(self) -> datetime.date:
        return self.enddate

    @strawberry.field(description="""Last change""")
    async def team(self) -> Union["GroupGQLModel", None]:
        result = await GroupGQLModel.resolve_reference(self.group_id)
        return result

    @strawberry.field(description="""Project type of project""")
    async def project_type(self, info: strawberry.types.Info) -> "ProjectTypeGQLModel":
        result = await ProjectTypeGQLModel.resolve_reference(info, self.projecttype_id)
        return result

    @strawberry.field(description="""List of finances, related to a project""")
    async def finances(
        self, info: strawberry.types.Info
    ) -> typing.List["FinanceGQLModel"]:
        loader = getLoaders(info).finances
        result = await loader.filter_by(project_id=self.id)
        return result

    @strawberry.field(description="""List of milestones, related to a project""")
    async def milestones(
        self, info: strawberry.types.Info
    ) -> typing.List["MilestoneGQLModel"]:
        loader = getLoaders(info).milestones
        result = await loader.filter_by(project_id=self.id)
        return result

    @strawberry.field(description="""Group, related to a project""")
    async def group(self, info: strawberry.types.Info) -> "GroupGQLModel":
        return GroupGQLModel(id=self.group_id)


# GQL PROJECT TYPE
from gql_projects.GraphResolvers import (
    resolveProjectTypeById,
    resolveProjectTypeAll,
    resolveUpdateProjectType,
    resolveInsertProjectType,
    resolveProjectsForProjectType,
    resolveFinancesForProject,
    resolveMilestonesForProject,
)


@strawberry.federation.type(
    keys=["id"], description="""Entity representing a project types"""
)
class ProjectTypeGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoaders(info).projecttypes

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    lastchange = resolve_lastchange
    changedby = resolve_changedby
    created = resolve_created
    createdby = resolve_createdby

    @strawberry.field(description="""List of projects, related to project type""")
    async def projects(
        self, info: strawberry.types.Info
    ) -> typing.List["ProjectGQLModel"]:
        async with withInfo(info) as session:
            result = await resolveProjectsForProjectType(session, self.id)
            return result


# GQL FINANCE
from gql_projects.GraphResolvers import (
    resolveFinanceById,
    resolveFinanceAll,
    resolveUpdateFinance,
    resolveInsertFinance,
)


@strawberry.federation.type(
    keys=["id"], description="""Entity representing a finance"""
)
class FinanceGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoaders(info).finances

    id = resolve_id
    name = resolve_name
    lastchange = resolve_lastchange
    changedby = resolve_changedby
    created = resolve_created
    createdby = resolve_createdby

    @strawberry.field(description="""Amount""")
    def amount(self) -> float:
        return self.amount

    @strawberry.field(description="""Project of finance""")
    async def project(self, info: strawberry.types.Info) -> "ProjectGQLModel":
        async with withInfo(info) as session:
            result = await resolveProjectById(session, self.project_id)
            return result

    @strawberry.field(description="""Finance type of finance""")
    async def financeType(self, info: strawberry.types.Info) -> "FinanceTypeGQLModel":
        async with withInfo(info) as session:
            result = await resolveFinanceTypeById(session, self.financetype_id)
            return result

    @strawberry.field(description="""Period which finances belongs to""")
    async def event(self, info: strawberry.types.Info) -> "EventGQLModel":
        result = await EventGQLModel.resolve_reference(self.event_id)
        return result

# GQL FINANCE TYPE
from gql_projects.GraphResolvers import (
    resolveFinanceTypeById,
    resolveFinanceTypeAll,
    resolveUpdateFinanceType,
    resolveInsertFinanceType,
    resolveFinancesForFinanceType,
)


@strawberry.federation.type(
    keys=["id"], description="""Entity representing a finance type"""
)
class FinanceTypeGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoaders(info).financetypes

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    lastchange = resolve_lastchange
    changedby = resolve_changedby
    created = resolve_created
    createdby = resolve_createdby

    @strawberry.field(description="""List of finances, related to finance type""")
    async def finances(
        self, info: strawberry.types.Info
    ) -> typing.List["FinanceGQLModel"]:
        async with withInfo(info) as session:
            result = await resolveFinancesForFinanceType(session, self.id)
            return result


# GQL MILESTONE
from gql_projects.GraphResolvers import (
    resolveMilestoneById,
    resolveMilestoneAll,
    resolveUpdateMilestone,
    resolveInsertMilestone,
)

import asyncio

@strawberry.federation.type(
    keys=["id"], description="""Entity representing a milestone"""
)
class MilestoneGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoaders(info).milestones

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    lastchange = resolve_lastchange
    changedby = resolve_changedby
    created = resolve_created
    createdby = resolve_createdby

    @strawberry.field(description="""Date""")
    def startdate(self) -> datetime.date:
        return self.startdate

    @strawberry.field(description="""Date""")
    def enddate(self) -> datetime.date:
        return self.enddate

    @strawberry.field(description="""Project of milestone""")
    async def project(self, info: strawberry.types.Info) -> "ProjectGQLModel":
        async with withInfo(info) as session:
            result = await resolveProjectById(session, self.project_id)
            return result

    @strawberry.field(description="""Milestones which has this one as follower""")
    async def previous(self, info: strawberry.types.Info) -> List["MilestoneGQLModel"]:
        # async with withInfo(info) as session:
        #     result = await resolveProjectById(session, self.project_id)
        #     return result
        loader = getLoaders(info).milestonelinks
        rows = await loader.filter_by(next_id=self.id)
        awaitable = (MilestoneGQLModel.resolve_reference(info, row.previous_id) for row in rows)
        return await asyncio.gather(*awaitable)

    @strawberry.field(description="""Milestone which follow this milestone""")
    async def nexts(self, info: strawberry.types.Info) -> List["MilestoneGQLModel"]:
        # async with withInfo(info) as session:
        #     result = await resolveProjectById(session, self.project_id)
        #     return result
        loader = getLoaders(info).milestonelinks
        rows = await loader.filter_by(previous_id=self.id)
        awaitable = (MilestoneGQLModel.resolve_reference(info, row.next_id) for row in rows)
        return await asyncio.gather(*awaitable)


# GQL GROUP
from gql_projects.GraphResolvers import resolveProjectsForGroup

@strawberry.federation.type(extend=True, keys=["id"])
class EventGQLModel:
    id: uuid.UUID = strawberry.federation.field(external=True)

    @classmethod
    async def resolve_reference(cls, id: uuid.UUID):
        return EventGQLModel(id=id)

@strawberry.federation.type(extend=True, keys=["id"])
class GroupGQLModel:
    id: uuid.UUID = strawberry.federation.field(external=True)

    @classmethod
    async def resolve_reference(cls, id: uuid.UUID):
        return GroupGQLModel(id=id)

    @strawberry.field(description="""List of projects, related to group""")
    async def projects(
        self, info: strawberry.types.Info
    ) -> typing.List["ProjectGQLModel"]:
        async with withInfo(info) as session:
            result = await resolveProjectsForGroup(session, self.id)
            return result


###########################################################################################################################
#
# zde definujte svuj Query model
#
###########################################################################################################################

from gql_projects.DBFeeder import randomDataStructure


@strawberry.type(description="""Type for query root""")
class Query:
    @strawberry.field(description="""Returns a list of projects""")
    async def project_page(
        self, info: strawberry.types.Info, skip: int = 0, limit: int = 10
    ) -> List[ProjectGQLModel]:
        async with withInfo(info) as session:
            result = await resolveProjectAll(session, skip, limit)
            return result

    @strawberry.field(description="""Returns project by its id""")
    async def project_by_id(
        self, info: strawberry.types.Info, id: uuid.UUID
    ) -> Union[ProjectGQLModel, None]:
        async with withInfo(info) as session:
            result = await resolveProjectById(session, id)
            return result

    @strawberry.field(description="""Returns a list of project types""")
    async def project_type_page(
        self, info: strawberry.types.Info, skip: int = 0, limit: int = 10
    ) -> List[ProjectTypeGQLModel]:
        async with withInfo(info) as session:
            result = await resolveProjectTypeAll(session, skip, limit)
            return result

    @strawberry.field(description="""Returns a list of finances""")
    async def finance_page(
        self, info: strawberry.types.Info, skip: int = 0, limit: int = 10
    ) -> List[FinanceGQLModel]:
        async with withInfo(info) as session:
            result = await resolveFinanceAll(session, skip, limit)
            return result

    @strawberry.field(description="""Returns a list of finance types""")
    async def finance_type_page(
        self, info: strawberry.types.Info, skip: int = 0, limit: int = 10
    ) -> List[FinanceTypeGQLModel]:
        async with withInfo(info) as session:
            result = await resolveFinanceTypeAll(session, skip, limit)
            return result

    @strawberry.field(description="""Returns a list of milestones""")
    async def milestone_page(
        self, info: strawberry.types.Info, skip: int = 0, limit: int = 10
    ) -> List[MilestoneGQLModel]:
        async with withInfo(info) as session:
            result = await resolveMilestoneAll(session, skip, limit)
            return result

    @strawberry.field(description="""Returns a list of projects for group""")
    async def project_by_group(
        self, info: strawberry.types.Info, id: uuid.UUID
    ) -> List[ProjectGQLModel]:
        async with withInfo(info) as session:
            result = await resolveProjectsForGroup(session, id)
            return result

    @strawberry.field(description="""Random publications""")
    async def randomProject(
        self, info: strawberry.types.Info
    ) -> Union[ProjectGQLModel, None]:
        async with withInfo(info) as session:
            result = await randomDataStructure(AsyncSessionFromInfo(info))
            return result


###########################################################################################################################
#
#
# Mutations
#
#
###########################################################################################################################

from typing import Optional

@strawberry.input
class ProjectInsertGQLModel:
    projecttype_id: uuid.UUID
    name: str

    id: Optional[uuid.UUID] = None
    name: Optional[str] = "Project"
    startdate: Optional[datetime.datetime] = datetime.datetime.now()
    enddate: Optional[datetime.datetime] = datetime.datetime.now()

    group_id: Optional[uuid.UUID] = None

@strawberry.input
class ProjectUpdateGQLModel:
    lastchange: datetime.datetime
    id: uuid.UUID
    name: Optional[str] = None
    projecttype_id: Optional[uuid.UUID] = None
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None
    group_id: Optional[uuid.UUID] = None
    
@strawberry.type
class ProjectResultGQLModel:
    id: uuid.UUID = None
    msg: str = None

    @strawberry.field(description="""Result of user operation""")
    async def project(self, info: strawberry.types.Info) -> Union[ProjectGQLModel, None]:
        result = await ProjectGQLModel.resolve_reference(info, self.id)
        return result

@strawberry.input
class FinanceInsertGQLModel:
    name: str
    financetype_id: uuid.UUID
    project_id: uuid.UUID
    id: Optional[uuid.UUID] = None
    amount: Optional[float] = 0

@strawberry.input
class FinanceUpdateGQLModel:
    lastchange: datetime.datetime
    id: uuid.UUID

    name: Optional[str]
    financetype_id: Optional[uuid.UUID]
    amount: Optional[float] = None
    
@strawberry.type
class FinanceResultGQLModel:
    id: uuid.UUID = None
    project_id: strawberry.Private[uuid.UUID] = None
    msg: str = None

    @strawberry.field(description="""Result of finance operation""")
    async def finance(self, info: strawberry.types.Info) -> Union[FinanceGQLModel, None]:
        result = await FinanceGQLModel.resolve_reference(info, self.id)
        return result
    
    @strawberry.field(description="""Project related to finance operation result""")
    async def project(self, info: strawberry.types.Info) -> Union[ProjectGQLModel, None]:
        result = await ProjectGQLModel.resolve_reference(info, self.project_id)
        return result

@strawberry.input
class MilestoneInsertGQLModel:
    name: str
    project_id: uuid.UUID
    startdate: Optional[datetime.datetime] = datetime.datetime.now()
    enddate: Optional[datetime.datetime] = datetime.datetime.now() + datetime.timedelta(days=30)
    id: Optional[uuid.UUID] = None

@strawberry.input
class MilestoneUpdateGQLModel:
    lastchange: datetime.datetime
    id: uuid.UUID

    name: Optional[str] = None
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None
    
@strawberry.type
class MilestoneResultGQLModel:
    id: uuid.UUID = None
    project_id: strawberry.Private[uuid.UUID] = None
    msg: str = None

    @strawberry.field(description="""Result of user operation""")
    async def milestone(self, info: strawberry.types.Info) -> Union[MilestoneGQLModel, None]:
        result = await MilestoneGQLModel.resolve_reference(info, self.id)
        return result

    @strawberry.field(description="""Project related to milestone operation result""")
    async def project(self, info: strawberry.types.Info) -> Union[ProjectGQLModel, None]:
        result = await ProjectGQLModel.resolve_reference(info, self.project_id)
        return result

@strawberry.input
class MilestoneLinkAddGQLModel:
    previous_id: uuid.UUID
    next_id: uuid.UUID
    
@strawberry.federation.type(extend=True)
class Mutation:
    @strawberry.mutation(description="Adds a new milestones link.")
    async def milestones_link_add(self, info: strawberry.types.Info, link: MilestoneLinkAddGQLModel) -> MilestoneResultGQLModel:
        loader = getLoaders(info).milestonelinks
        rows = await loader.filter_by(previous_id=link.previous_id, next_id=link.next_id)
        row = next(rows, None)
        result = MilestoneResultGQLModel()
        if row is None:
            row = await loader.insert(link)
            result.msg = "ok"
        else:
            result.msg = "exists"
        result.id = link.previous_id
        result.project_id = row.project_id
        return result

    @strawberry.mutation(description="Removes the milestones link.")
    async def milestones_link_remove(self, info: strawberry.types.Info, link: MilestoneLinkAddGQLModel) -> MilestoneResultGQLModel:
        loader = getLoaders(info).milestonelinks
        rows = await loader.filter_by(previous_id=link.previous_id, next_id=link.next_id)
        row = next(rows, None)
        result = MilestoneResultGQLModel()
        if row is None:
            result.msg = "fail"
        else:
            await loader.delete(row.id)
            result.msg = "ok"
        result.id = link.previous_id
        return result

    @strawberry.mutation(description="Adds a new milestone.")
    async def milestone_insert(self, info: strawberry.types.Info, milestone: MilestoneInsertGQLModel) -> MilestoneResultGQLModel:
        loader = getLoaders(info).milestones
        row = await loader.insert(milestone)
        result = MilestoneResultGQLModel()
        result.msg = "ok"
        result.id = row.id
        return result

    @strawberry.mutation(description="Update the milestone.")
    async def milestone_update(self, info: strawberry.types.Info, milestone: MilestoneUpdateGQLModel) -> MilestoneResultGQLModel:
        loader = getLoaders(info).milestones
        row = await loader.update(milestone)
        result = MilestoneResultGQLModel()
        result.msg = "ok"
        result.id = milestone.id
        if row is None:
            result.msg = "fail"
            
        return result

    @strawberry.mutation(description="Delete the milestone.")
    async def milestone_delete(self, info: strawberry.types.Info, id: uuid.UUID) -> ProjectResultGQLModel:
        loader = getLoaders(info).milestonelinks
        rows = await loader.filter_by(previous_id=id)
        linksids = [row.id for row in rows]
        rows = await loader.filter_by(next_id=id)
        linksids.extend([row.id for row in rows])
        for id in linksids:
            await loader.delete(id)

        loader = getLoaders(info).milestones
        row = await loader.load(id)
        result = ProjectResultGQLModel()
        result.id = row.project_id
        await loader.delete(id)       
        result.msg = "ok"
        return result

    @strawberry.mutation(description="Adds a new finance record.")
    async def finance_insert(self, info: strawberry.types.Info, finance: FinanceInsertGQLModel) -> FinanceResultGQLModel:
        loader = getLoaders(info).finances
        row = await loader.insert(finance)
        result = FinanceResultGQLModel()
        result.msg = "ok"
        result.id = row.id
        return result

    @strawberry.mutation(description="Update the finance record.")
    async def finance_update(self, info: strawberry.types.Info, finance: FinanceUpdateGQLModel) -> FinanceResultGQLModel:
        loader = getLoaders(info).finances
        row = await loader.update(finance)
        result = FinanceResultGQLModel()
        result.msg = "ok"
        result.id = finance.id
        if row is None:
            result.msg = "fail"
            
        return result

    @strawberry.mutation(description="Adds a new project.")
    async def project_insert(self, info: strawberry.types.Info, project: ProjectInsertGQLModel) -> ProjectResultGQLModel:
        loader = getLoaders(info).projects
        row = await loader.insert(project)
        result = ProjectResultGQLModel()
        result.msg = "ok"
        result.id = row.id
        return result

    @strawberry.mutation(description="Update the project.")
    async def project_update(self, info: strawberry.types.Info, project: ProjectUpdateGQLModel) -> ProjectResultGQLModel:
        loader = getLoaders(info).projects
        row = await loader.update(project)
        result = ProjectResultGQLModel()
        result.msg = "ok"
        result.id = project.id
        if row is None:
            result.msg = "fail"
            
        return result

###########################################################################################################################
#
# Schema je pouzito v main.py, vsimnete si parametru types, obsahuje vyjmenovane modely. Bez explicitniho vyjmenovani
# se ve schema objevi jen ty struktury, ktere si strawberry dokaze odvodit z Query. Protoze v teto konkretni implementaci
# nektere modely nejsou s Query propojene je potreba je explicitne vyjmenovat. Jinak ve federativnim schematu nebude
# dostupne rozsireni, ktere tento prvek federace implementuje.
#
###########################################################################################################################

schema = strawberry.federation.Schema(Query, types=(GroupGQLModel,), mutation=Mutation)
