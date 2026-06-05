from __future__ import annotations
import asyncio, uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.core.database import async_session_maker, init_models
from app.models.organization import Organization
from app.models.pipeline import Pipeline, PipelineSource, RunStatus
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance, TaskStatus
from app.models.dag_definition import DagDefinition
H=chr(104)+chr(101)+chr(108)+chr(105)+chr(111)+chr(115)+chr(45)+chr(101)+chr(101)+chr(105)+chr(112)+chr(45)+chr(105)+chr(110)+chr(103)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)
BRT=timezone(timedelta(hours=-3))
START=datetime(2026,6,4,5,0,0,tzinfo=BRT)
T=[dict(task_id=chr(105)+chr(110)+chr(103)+chr(101)+chr(115)+chr(116)+chr(95)+chr(100)+chr(101)+chr(112)+chr(115)+chr(95)+chr(100)+chr(101)+chr(118),label=chr(73)+chr(110)+chr(103)+chr(101)+chr(115)+chr(116)+chr(32)+chr(100)+chr(101)+chr(112)+chr(115)+chr(46)+chr(100)+chr(101)+chr(118)+chr(32)+chr(65)+chr(80)+chr(73),status=TaskStatus.success,duration_ms=8342),dict(task_id=chr(100)+chr(98)+chr(116)+chr(95)+chr(98)+chr(114)+chr(111)+chr(110)+chr(122)+chr(101)+chr(95)+chr(116)+chr(111)+chr(95)+chr(115)+chr(105)+chr(108)+chr(118)+chr(101)+chr(114),label=chr(100)+chr(98)+chr(116)+chr(58)+chr(32)+chr(66)+chr(114)+chr(111)+chr(110)+chr(122)+chr(101)+chr(32)+chr(116)+chr(111)+chr(32)+chr(83)+chr(105)+chr(108)+chr(118)+chr(101)+chr(114),status=TaskStatus.success,duration_ms=4210),dict(task_id=chr(100)+chr(98)+chr(116)+chr(95)+chr(115)+chr(105)+chr(108)+chr(118)+chr(101)+chr(114)+chr(95)+chr(116)+chr(111)+chr(95)+chr(103)+chr(111)+chr(108)+chr(100),label=chr(100)+chr(98)+chr(116)+chr(58)+chr(32)+chr(83)+chr(105)+chr(108)+chr(118)+chr(101)+chr(114)+chr(32)+chr(116)+chr(111)+chr(32)+chr(71)+chr(111)+chr(108)+chr(100),status=TaskStatus.success,duration_ms=5230),dict(task_id=chr(101)+chr(120)+chr(112)+chr(111)+chr(114)+chr(116)+chr(95)+chr(103)+chr(111)+chr(108)+chr(100)+chr(95)+chr(112)+chr(97)+chr(114)+chr(113)+chr(117)+chr(101)+chr(116),label=chr(69)+chr(120)+chr(112)+chr(111)+chr(114)+chr(116)+chr(32)+chr(71)+chr(111)+chr(108)+chr(100)+chr(32)+chr(80)+chr(97)+chr(114)+chr(113)+chr(117)+chr(101)+chr(116)+chr(32)+chr(116)+chr(111)+chr(32)+chr(65)+chr(68)+chr(76)+chr(83),status=TaskStatus.success,duration_ms=1890)]

async def main():
 await init_models()
 async with async_session_maker() as s:
  o=(await s.execute(select(Organization).limit(1))).scalar_one_or_none()
  if o is None:
   print(chr(91)+H+chr(45)+chr(115)+chr(101)+chr(101)+chr(100)+chr(93)+chr(32)+chr(78)+chr(111)+chr(32)+chr(111)+chr(114)+chr(103))
   return
  p=(await s.execute(select(Pipeline).where(Pipeline.dag_id==H))).scalar_one_or_none()
  if p is None:
   p=Pipeline(id=uuid.uuid4(),org_id=o.id,name=chr(72)+chr(101)+chr(108)+chr(105)+chr(111)+chr(115)+chr(32)+chr(69)+chr(69)+chr(73)+chr(80)+chr(32)+chr(73)+chr(110)+chr(103)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110),source=PipelineSource.azure_function,dag_id=H,last_run_status=RunStatus.success,last_run_at=START)
   s.add(p);await s.flush()
   n=[{chr(105)+chr(100):x[chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)],chr(108)+chr(97)+chr(98)+chr(101)+chr(108):x[chr(108)+chr(97)+chr(98)+chr(101)+chr(108)],chr(116)+chr(121)+chr(112)+chr(101):chr(116)+chr(97)+chr(115)+chr(107)} for x in T]
   e=[{chr(115)+chr(111)+chr(117)+chr(114)+chr(99)+chr(101):T[i][chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)],chr(116)+chr(97)+chr(114)+chr(103)+chr(101)+chr(116):T[i+1][chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)]} for i in range(len(T)-1)]
   s.add(DagDefinition(pipeline_id=p.id,nodes=n,edges=e))
   print(chr(91)+H+chr(45)+chr(115)+chr(101)+chr(101)+chr(100)+chr(93)+chr(32)+chr(80)+chr(105)+chr(112)+chr(101)+chr(108)+chr(105)+chr(110)+chr(101)+chr(32)+chr(43)+chr(32)+chr(68)+chr(65)+chr(71))
  r=PipelineRun(id=uuid.uuid4(),pipeline_id=p.id,run_id=H+chr(45)+chr(50)+chr(48)+chr(50)+chr(54)+chr(45)+chr(48)+chr(54)+chr(45)+chr(48)+chr(52)+chr(84)+chr(48)+chr(53)+chr(58)+chr(48)+chr(48)+chr(58)+chr(48)+chr(48),status=RunStatus.success,started_at=START,finished_at=datetime(2026,6,4,5,0,22,tzinfo=BRT),duration_ms=22150)
  s.add(r);await s.flush()
  a=0
  for x in T:
   ts=START+timedelta(milliseconds=a)
   a+=x[chr(100)+chr(117)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(109)+chr(115)]+250
   s.add(TaskInstance(id=uuid.uuid4(),run_id=r.id,task_id=x[chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)],status=x[chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)],started_at=ts,finished_at=ts+timedelta(milliseconds=x[chr(100)+chr(117)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(109)+chr(115)]),duration_ms=x[chr(100)+chr(117)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(109)+chr(115)],try_number=1))
  await s.commit()
  print(chr(91)+H+chr(45)+chr(115)+chr(101)+chr(101)+chr(100)+chr(93)+chr(32)+chr(100)+chr(111)+chr(110)+chr(101))
if __name__==chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):asyncio.run(main())
