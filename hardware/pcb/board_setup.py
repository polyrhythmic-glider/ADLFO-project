"""Native pcbnew preparation. Run with KiCad's Python, after build.py.

The main board has a dedicated internal ground plane; the front board has two
copper layers. Routing and native DRC remain separate, explicit build stages.
"""
from pathlib import Path
import json
import hashlib
import subprocess
import sys
import xml.etree.ElementTree as ET
import pcbnew as pcb

OUT=Path(__file__).parent/'output'
WORK=Path(__file__).parent/'build'


def route_rules(path):
    raw=path.read_text(encoding='utf-8');start=raw.index('(class kicad_default ')
    circuit=raw.index('(circuit',start);depth=0;end=start
    for end in range(start,len(raw)):
        if raw[end]=='(':depth+=1
        elif raw[end]==')':
            depth-=1
            if depth==0:break
    nets=raw[start+len('(class kicad_default '):circuit].split()
    power=[n for n in nets if n.startswith(('+','-')) and n not in ('+3V3','+5A')]
    if power:
        default='(class kicad_default '+' '.join(n for n in nets if n not in power)+'\n'+raw[circuit:end+1]
        body=raw[circuit:end+1].replace('(width 200)','(width 300)').replace('(clearance 150)','(clearance 160)')
        raw=raw[:start]+default+'\n    (class Power '+' '.join(power)+'\n'+body+raw[end+1:]
    # Ten micrometres guard against autorouter export rounding at the native 0.15 mm limit.
    raw=raw.replace('(clearance 150)','(clearance 160)')
    # Preserve a continuous reference plane; signal routing uses the other three layers.
    raw=raw.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)')
    path.write_text(raw,encoding='utf-8')


def prepare():
    WORK.mkdir(exist_ok=True)
    design=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
    parts={p['ref']:p for p in design['parts']}
    connector_positions={}
    for name in ('main','panel'):
        netfile=OUT/f'Adolfo-{name}.net'
        subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','sch','export','netlist',
                        '--format','kicadxml','--output',str(netfile),str(OUT/f'Adolfo-{name}.kicad_sch')],check=True)
        netlist=ET.parse(netfile)
        pin_nets={(node.attrib['ref'],node.attrib['pin']):net.attrib['name']
                  for net in netlist.findall('./nets/net') for node in net.findall('node')}
        path=OUT/f'Adolfo-{name}.kicad_pcb';b=pcb.LoadBoard(str(path))
        b.SetCopperLayerCount(4 if name=='main' else 2)
        settings=b.GetDesignSettings()
        settings.m_MinClearance=pcb.FromMM(.15)
        settings.m_TrackMinWidth=pcb.FromMM(.15)
        settings.m_ViasMinSize=pcb.FromMM(.6)
        settings.m_MinThroughDrill=pcb.FromMM(.3)
        settings.m_HoleToHoleMin=pcb.FromMM(.25)
        settings.m_CopperEdgeClearance=pcb.FromMM(.3)
        default=settings.m_NetSettings.GetNetClassByName('Default')
        default.SetClearance(pcb.FromMM(.15));default.SetTrackWidth(pcb.FromMM(.2))
        default.SetViaDiameter(pcb.FromMM(.6));default.SetViaDrill(pcb.FromMM(.3))
        for fp in b.GetFootprints():
            part=parts.get(fp.GetReference())
            if part is None:
                fp.SetAttributes(fp.GetAttributes() | pcb.FP_BOARD_ONLY)
                continue
            fp.SetFields({'MPN':part['mpn'],'Manufacturer':part['manufacturer'],
                          'Datasheet':part['datasheet'],'BOM Comments':part['note']})
            for field in ('MPN','Manufacturer','Datasheet','BOM Comments'):
                fp.GetField(field).SetVisible(False)
            if part and part['side']=='B':
                assert fp.GetLayer()==pcb.F_Cu,'Prepare only fresh, unflipped build output'
                fp.Flip(fp.GetPosition(),False)
            for pad in fp.Pads():
                if not pad.GetNumber():continue
                key=(fp.GetReference(),pad.GetNumber());netname=pin_nets.get(key)
                expected=part['pins'][pad.GetNumber()]
                assert netname==expected or (expected is None and (netname is None or netname.startswith('unconnected-'))),(key,expected,netname)
                if netname:
                    net=b.FindNet(netname)
                    if net is None or net.GetNetCode()<0:
                        net=pcb.NETINFO_ITEM(b,netname);b.Add(net)
                    pad.SetNet(net)
            if part['id'] in ('JM','JP'):
                connector_positions[part['id']]={p.GetNumber():(p.GetPosition().x,p.GetPosition().y) for p in fp.Pads()}
        if name=='main':
            zone=pcb.ZONE(b);zone.SetLayer(pcb.In1_Cu);zone.SetNetCode(b.FindNet('GND').GetNetCode())
            zone.SetLocalClearance(pcb.FromMM(.25));zone.SetThermalReliefGap(pcb.FromMM(.25))
            zone.SetThermalReliefSpokeWidth(pcb.FromMM(.3))
            p=design['pcb'];border=zone.Outline();border.NewOutline()
            for x,y in [(p['x']+.3,p['y']+.3),(p['x']+p['width']-.3,p['y']+.3),
                        (p['x']+p['width']-.3,p['y']+p['height']-.3),(p['x']+.3,p['y']+p['height']-.3)]:border.Append(pcb.FromMM(x),pcb.FromMM(y))
            b.Add(zone)
            from ground_plane import connect_ground
            assert not connect_ground(b),'Ground pads must have physical connections before exporting the plane'
            pcb.ZONE_FILLER(b).Fill(b.Zones())
        pcb.SaveBoard(str(path),b)
        assert pcb.ExportSpecctraDSN(b,str(WORK/f'Adolfo-{name}.dsn'))
        route_rules(WORK/f'Adolfo-{name}.dsn')
    assert connector_positions['JM']==connector_positions['JP'],'The mating connectors must align by physical pin number'
    print('Prepared native boards; JM/JP all 40 pad coordinates agree.')


def audit():
    result={}
    for name in ('main','panel'):
        b=pcb.LoadBoard(str(OUT/f'Adolfo-{name}.kicad_pcb'))
        parts={}
        for fp in b.GetFootprints():
            parts[fp.GetReference()]={'x':pcb.ToMM(fp.GetPosition().x),'y':pcb.ToMM(fp.GetPosition().y),
                'side':'B' if fp.GetLayer()==pcb.B_Cu else 'F','path':fp.GetPath().AsString(),
                'value':fp.GetValue(),
                'mpn':fp.GetFieldText('MPN') if fp.HasField('MPN') else '',
                'manufacturer':fp.GetFieldText('Manufacturer') if fp.HasField('Manufacturer') else '',
                'datasheet':fp.GetFieldText('Datasheet') if fp.HasField('Datasheet') else '',
                'pads':[{'number':p.GetNumber(),'net':p.GetNetname(),'x':pcb.ToMM(p.GetPosition().x),'y':pcb.ToMM(p.GetPosition().y),
                         'drill_x':pcb.ToMM(p.GetDrillSize().x),'drill_y':pcb.ToMM(p.GetDrillSize().y)} for p in fp.Pads()]}
        tracks=[t for t in b.GetTracks() if not isinstance(t,pcb.PCB_VIA)]
        smd=[p for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcb.PAD_ATTRIB_SMD]
        via_in_smd=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber()
                    for via in b.GetTracks() if isinstance(via,pcb.PCB_VIA)
                    for p in smd if p.GetEffectiveShape(p.GetLayer()).Collide(
                        pcb.SHAPE_CIRCLE(via.GetPosition(),via.GetDrillValue()//2),0)]
        result[name]={'sha256':hashlib.sha256((OUT/f'Adolfo-{name}.kicad_pcb').read_bytes()).hexdigest(),
            'parts':parts,'layers':b.GetCopperLayerCount(),'tracks':len(tracks),
            'vias':sum(isinstance(t,pcb.PCB_VIA) for t in b.GetTracks()),
            'track_length_mm':sum(pcb.ToMM(t.GetLength()) for t in tracks),
            'via_in_smd':via_in_smd,
            'plane_signal_tracks':[t.GetNetname() for t in tracks if t.GetLayer()==pcb.In1_Cu and t.GetNetname()!='GND'],
            'zones':[{'net':z.GetNetname(),'layer':b.GetLayerName(z.GetLayer()),'filled':z.HasFilledPolysForLayer(z.GetLayer())} for z in b.Zones()]}
    (OUT/'board-metrics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({name:{k:v for k,v in data.items() if k!='parts'} for name,data in result.items()})


if __name__=='__main__':
    if sys.argv[1:]==['audit']:audit()
    else:prepare()
