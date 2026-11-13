import json
from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.case import EvidenceCase
from ..models.revision import CptRevision
from ..models.network import BayesNetwork
from .network_service import nodes
from .network_validation import validate_evidence,validate_weights
def create(db,body):
 revision=db.get(CptRevision,body.revision_id)
 if not revision:raise HTTPException(422,'CPT版本不存在')
 try:
  graph=nodes(db,db.get(BayesNetwork,revision.network_id));evidence=json.loads(body.evidence_json)
  weights={} if body.weights_json in (None,'','null') else json.loads(body.weights_json)
  candidates=validate_evidence(graph,evidence,body.target,json.loads(body.candidates_json),weights)
  weights=validate_weights(graph,weights,evidence,body.target)
 except (ValueError,TypeError) as error:raise HTTPException(422,str(error))
 if db.scalar(select(EvidenceCase).where(EvidenceCase.name==body.name)):raise HTTPException(409,'案例名称已存在')
 row=EvidenceCase(id=str(uuid4()),name=body.name,revision_id=revision.id,target=body.target,evidence=evidence,weights=weights or None,candidates=candidates);db.add(row);db.commit();return row
