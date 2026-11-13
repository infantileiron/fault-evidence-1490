import math
import numpy as np
from scipy.special import logsumexp
from .network_validation import validate_network,validate_cpt,validate_evidence,validate_weights
from .log_factor import cpt_factors,weight_factors,product

def _eliminate(nodes,rows,evidence,target,weights,extra_evidence=None):
 if extra_evidence:evidence={**evidence,**extra_evidence}
 factors=[factor.restrict(evidence) for factor in cpt_factors(nodes,rows)]
 if weights:factors+= [factor.restrict(evidence) for factor in weight_factors(weights)]
 order=sorted({n['node_id'] for n in nodes}-set(evidence)-{target});trace=[]
 for variable in order:
  bucket=[f for f in factors if variable in f.variables];factors=[f for f in factors if variable not in f.variables]
  joined=product(bucket);reduced=joined.sum_out(variable);factors.append(reduced)
  trace.append({'variable':variable,'input_scopes':[list(f.variables) for f in bucket],'product_scope':list(joined.variables),'product_cells':int(joined.values.size),'output_scope':list(reduced.variables),'output_cells':int(reduced.values.size)})
 return product(factors),order,trace

def _underflow(log_probability):
 if log_probability==-math.inf:return 0.,False
 value=math.exp(log_probability);return value,value==0

def infer(nodes,cpt,evidence,target,weights=None,allow_conflict=False):
 graph=validate_network(nodes);nodes=graph['nodes'];rows=validate_cpt(nodes,cpt);validate_evidence(nodes,evidence,target,None,weights,allow_conflict)
 clean_weights=validate_weights(nodes,weights,evidence,target,allow_conflict)
 final,order,trace=_eliminate(nodes,rows,evidence,target,clean_weights);log_normalizer=float(logsumexp(final.values))
 if math.isnan(log_normalizer) or log_normalizer==math.inf:raise ValueError('归一常数logZ非有限，推理失败')
 if clean_weights:
  evidence_log,_,_=_eliminate(nodes,rows,evidence,target,None);log_evidence_probability=float(logsumexp(evidence_log.values))
 else:
  log_evidence_probability=log_normalizer
 if log_normalizer==-math.inf and log_evidence_probability>-math.inf and not allow_conflict:raise ValueError('权重与证据冲突：加权归一常数为0，但确定证据概率为正')
 if log_normalizer==-math.inf and log_evidence_probability==-math.inf:raise ValueError('不可能证据：logZ=-inf，给定模型下证据概率严格为0')
 if math.isnan(log_evidence_probability) or log_evidence_probability==math.inf:raise ValueError('证据概率非有限，推理失败')
 normalizer_probability,normalizer_underflow=_underflow(log_normalizer)
 evidence_probability,evidence_underflow=_underflow(log_evidence_probability)
 if target in evidence:log_probabilities=[0. if state==evidence[target] else -math.inf for state in (0,1)]
 else:
  if final.variables!=(target,):raise ValueError('消元后目标作用域异常')
  log_probabilities=(final.values-log_normalizer).tolist()
 posterior=[]
 for state,log_p in enumerate(log_probabilities):
  probability=0. if log_p==-math.inf else math.exp(log_p)
  posterior.append({'state':state,'probability':probability,'log_probability':None if log_p==-math.inf else log_p,'probability_underflow':log_p!=-math.inf and probability==0})
 return {'target':target,'evidence':dict(evidence),'weights':dict(clean_weights),'weights_applied':bool(clean_weights),'posterior':posterior,'log_normalizer':log_normalizer,'normalizer_probability':normalizer_probability,'normalizer_underflow':normalizer_underflow,'log_evidence_probability':log_evidence_probability,'evidence_probability':evidence_probability,'evidence_probability_underflow':evidence_underflow,'log_evidence':log_normalizer,'evidence_possible':True,'elimination_order':order,'trace':trace,'method':'exact variable elimination / log factors + logsumexp','log_base':'natural','probability_sum':math.fsum(p['probability'] for p in posterior),'normalizer':'logZ','note':'logZ为含软权重因子的归一常数，不等于证据概率P(E)；旧字段log_evidence保留为logZ别名。exp下溢单独标注；只有logZ=-inf为不可能证据。查询已观测时先核对Z再给one-hot。'}
