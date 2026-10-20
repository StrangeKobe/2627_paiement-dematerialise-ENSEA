#!/usr/bin/env python3
"""Relancer ERC, DRC, parite et comparaison de connexions ; Python 3 + KiCad 9 CLI."""
from pathlib import Path
import subprocess,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
PROJECTS={'caisse':('Caisse_Fixe','PCB_Caisse_Enregistreuse'),'terminal':('Terminal_Mobile','PCB_Caisse_Dématérialisée')}
OUT=ROOT/'Validation_reexecution'
def connections(path):
 tree=ET.parse(path)
 return tree,{(p.get('ref'),p.get('pin')):n.get('name') for n in tree.findall('nets/net') for p in n.findall('node')}
def run(*args):subprocess.run(['kicad-cli',*map(str,args)],check=True)
def main():
 OUT.mkdir(exist_ok=True)
 for kind,(folder,stem) in PROJECTS.items():
  sch=ROOT/'Hardware'/folder/(stem+'.kicad_sch');pcb=sch.with_suffix('.kicad_pcb')
  run('sch','erc','--format','json','-o',OUT/f'{kind}_ERC.json',sch)
  run('pcb','drc','--format','json','--all-track-errors','--schematic-parity','-o',OUT/f'{kind}_DRC.json',pcb)
  run('sch','export','netlist','--format','kicadxml','-o',OUT/f'{kind}_netlist.xml',sch)
  for suffix in ['DRC','ERC']:
   data=json.loads((OUT/f'{kind}_{suffix}.json').read_text())
   violations=([v for s in data.get('sheets',[]) for v in s.get('violations',[])] if suffix=='ERC' else data['violations']+data['unconnected_items']+data['schematic_parity'])
   if violations:raise RuntimeError(f'{kind}: {len(violations)} anomalies {suffix}; lire {OUT}')
  tree,nets=connections(OUT/f'{kind}_netlist.xml');_,old=connections(ROOT/'Validation/Reference_V1'/f'{kind}_netlist.xml')
  for (ref,pin),name in old.items():
   if ref in (['Q1','Q3'] if kind=='caisse' else ['Q1']):pin={'1':'3','2':'1','3':'2'}[pin]
   if name in ['Net-(Q1-G)','Net-(Q3-G)']:name='/'+name[5:7]+'_GATE'
   if kind=='caisse':
    if name=='+12V':name='+12V_RAW' if (ref,pin) in [('J2','1'),('J3','1')] else '+12V_SW'
    if name=='/Power_supply/Interrupteur -':name='+12V_SW'
   assert nets.get((ref,pin))==name,(kind,ref,pin,name,nets.get((ref,pin)))
  for ref,gate in [('D8','/Q1_GATE')]+([('D9','/Q3_GATE')] if kind=='caisse' else []):
   assert nets[(ref,'1')]==gate and nets[(ref,'2')]=='GND',(kind,ref)
  if kind=='caisse':assert {p for p,n in nets.items() if n=='+12V_RAW'}=={('J2','1'),('J3','1')}
  values={c.get('ref'):c.findtext('value') for c in tree.findall('components/comp')}
  expected={'R12':'90k9','R4':'10k','R15':'10k','C15':'4n7'} if kind=='caisse' else {'R3':'10k'}
  for ref,value in expected.items():assert values[ref]==value,(kind,ref,values[ref])
  print(kind,': OK - ERC, DRC, parite, valeurs et connexions V2')
 print('Controles numeriques termines. Les essais sur prototype restent distincts.')
if __name__=='__main__':main()
