from odbAccess import openOdb
import json
paths = {'full_odb': 'D:\\kimi\\cae-mcp\\runs\\abaqus_5d1d0ab8c1f34371\\analysis.odb', 'reduced_odb': 'D:\\kimi\\cae-mcp\\runs\\abaqus_eff56b44421446e6\\analysis.odb'}
result = {}
for label,path in paths.items():
    odb=openOdb(path,readOnly=True)
    rows=[]
    for frame in odb.steps['Pull'].frames:
        u=[v for v in frame.fieldOutputs['U'].values if 109<=v.nodeLabel<=117]
        rf=[v for v in frame.fieldOutputs['RF'].values if 109<=v.nodeLabel<=117]
        root=[v for v in frame.fieldOutputs['RF'].values if 1<=v.nodeLabel<=9]
        if len(u)!=9 or len(rf)!=9 or len(root)!=9:
            raise ValueError('Reference endpoint node coverage differs')
        peeq=frame.fieldOutputs['PEEQ'] if 'PEEQ' in frame.fieldOutputs else None
        rows.append(dict(time=frame.frameValue,U1=sum(v.data[0] for v in u)/len(u),
            tip_RF1=sum(v.data[0] for v in rf),root_RF1=sum(v.data[0] for v in root),
            max_PEEQ=max([v.data for v in peeq.values] or [0]) if peeq else 0))
    result[label]=rows
    odb.close()
with open('D:\\kimi\\benchmark_public\\v03_native_20261105\\claude-code-S04-a1\\curves.json','w') as f: json.dump(result,f,indent=2)
