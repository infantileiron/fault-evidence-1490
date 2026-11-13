"""Standalone acceptance checks for soft (weighted) evidence. Pure numerical layer; no DB/Redis needed."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.demo_data import DEMO_NODES,DEMO_CPT,HAND_NODES,HAND_CPT
from src.services.variable_elimination import infer
from src.services.information_gain import information_gain

def close(a,b,tol=1e-10):return abs(a-b)<=tol*max(1,abs(a),abs(b))

def main():
 failures=[]
 def check(name,condition,detail=''):
  if not condition:failures.append(name+' '+detail)
 baseline=infer(DEMO_NODES,DEMO_CPT,{'Heat':1,'Alarm':1},'Fault')
 check('无权重时logZ等于证据概率',close(baseline['log_normalizer'],baseline['log_evidence_probability']),str(baseline['log_normalizer']))
 check('无权重时后验不变',close(baseline['posterior'][1]['probability'],0.6608061335474756))
 soft=information_gain(DEMO_NODES,DEMO_CPT,{'Alarm':1},'Fault',weights={'Heat':[1,3]})
 scaled=information_gain(DEMO_NODES,DEMO_CPT,{'Alarm':1},'Fault',weights={'Heat':[2,6]})
 tiny=information_gain(DEMO_NODES,DEMO_CPT,{'Alarm':1},'Fault',weights={'Heat':[1e-300,3e-300]})
 for other,label in [(scaled,'同比缩放'),(tiny,'极小正权重')]:
  check(label+'后验不变',close(soft['baseline']['posterior'][1]['probability'],other['baseline']['posterior'][1]['probability']))
  check(label+'IG不变',len(soft['candidates'])==len(other['candidates']) and all(close(a['information_gain'],b['information_gain']) for a,b in zip(soft['candidates'],other['candidates'])))
 check('软权重不改变证据概率',close(soft['baseline']['log_evidence_probability'],-1.4850371776864433))
 check('加权logZ与证据概率分开',not close(soft['baseline']['log_normalizer'],soft['baseline']['log_evidence_probability']))
 check('带权节点不列为候选',all(c['node_id']!='Heat' for c in soft['candidates']))
 check('软权重进入快照',soft['baseline']['weights']=={'Heat':[1.0,3.0]})
 for weights,evidence,label in [({'Heat':[0,0]},{},'全零'),({'Heat':[-1,2]},{},'负权重'),({'Heat':[0,3]},{'Heat':0},'与确定证据冲突'),({'Fault':[1,2]},{},'目标带权')]:
  try:infer(DEMO_NODES,DEMO_CPT,evidence,'Fault',weights);failures.append(label+'未拒绝')
  except ValueError:pass
 conflict=infer(DEMO_NODES,DEMO_CPT,{'Fault':1,'Lock':1},'Fault',{'Lock':[1,0]},allow_conflict=True)
 check('软权重可令加权logZ为零但证据概率为正',conflict['log_normalizer']==-math.inf and conflict['log_evidence_probability']>-math.inf)
 try:infer(DEMO_NODES,DEMO_CPT,{'Fault':1,'Lock':1},'Fault',{'Lock':[1,0]});failures.append('零加权质量与确定证据冲突未拒绝')
 except ValueError:pass
 check('手算IG保持',close(information_gain(HAND_NODES,HAND_CPT,{},'F')['candidates'][0]['information_gain'],0.27545818553562484))
 print('FAIL' if failures else 'OK',failures)
 return 1 if failures else 0
if __name__=='__main__':sys.exit(main())
