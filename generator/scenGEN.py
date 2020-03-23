# -*- coding: utf-8 -*-
"""
:::::::::::::::::::::::::::::::::::::  MITRE CRP PROJECT  :::::::::::::::::::::::::::::::::::::::

                                            NOTICE

This software (or technical data) was produced for the U. S. Government under contract 355358
with Brookhaven National Laboratory, and is subject to the Rights in Data-General Clause 52.227-14 (MAY 2014) or (DEC 2007).

The following copyright notice may be affixed after receipt of written approval from the Contracting Officer.
Please contact the Contracts Management Office for assistance with obtaining approval or identifying the correct clause.
If the contract has Clause 52.227-14, Alt. IV, written approval is not required and the below copyright notice may be affixed.

(c) 2020 The MITRE Corporation. All Rights Reserved.


scenGEN.py - Utility application for generating scenarios

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
"""

import sys
import random
from collections import defaultdict
from loaddata import LOAD_DATA, LOAD_TTP_SUPPLEMENT, LOAD_ATK4ICS, LOAD_ACTOR_PROFILES  # LOAD_TTP_EXTENSION
from loaddata import m_file_INFRASTRUCTURE, m_file_SCENARIOS, m_file_EXTENSIONS, m_file_ODNI

from stats import TAGS_INDEX, x_TYPES, x_TACTICS, x_PLATFORMS, x_ACTTAGS, x_TTPTAGS, x_MITTAGS, x_MALTAGS, x_TOLTAGS 

from TACSequence import initPatternMenu, GenTacticPattern, GetPatternbyName, GenTTPSequence
from ffactory import FILTER_FACTORY, INIT_FILTERS

import zoneCrawlr
from dbLoad import refreshSCENARIOs
from mitGEN import GENERATE_MITIGATIONS, SCENARIO_REPORT, ACTOR_REPORT
from ODNI import loadODNI, mapTTPs, augmentTTPs
import json

trace = False

def shortlist(listx, num):
    nxt = 0
    for entry in listx:
        entry.PP()
        nxt = nxt + 1
        if (nxt >= num):
            break

def isCOA (entry):
    if not(entry.find ('course-of-action') < 0):
        return True
    return False

def isTTP(entry):
    if not(entry.find ('attack-pattern') < 0):
        return True
    return False

def isMAL(entry):
    if not(entry.find ('malware') < 0):
        return True
    return False

def isACT(entry):
    if not(entry.find('intrusion-set') < 0):
        return True
    return False

def isTOOL(entry):
    if not(entry.find('tool--') < 0):
        return True
    return False

def findTTP(dataset, pattern):
    for t in dataset['ATT&CK']:
        if (t.getID() == pattern):
            return t
        
def findCOA(dataset, pattern):
    for c in dataset['ATKMITIGATION']:
        if (c.getID() == pattern):
            return c
        
def findACT(dataset, pattern):
    for a in dataset['ATKGROUPS']:
        if (a.getID() == pattern):
            return a
        
def findMAL(dataset, pattern):
    for m in dataset['ATKMALWARE']:
        if (m.getID() == pattern):
            return m

def findTOOL(dataset, pattern):
    for m in dataset['ATKTOOL']:
        if (m.getID() == pattern):
            return m

def find (dataset, patternID):
    if isCOA(patternID):
        return findCOA(dataset, patternID)
    elif isTTP(patternID):
        return findTTP(dataset, patternID)
    elif isACT(patternID):
        return findACT(dataset, patternID)
    elif isMAL(patternID):
        return findMAL(dataset, patternID)
    elif isTOOL(patternID):
        return findTOOL(dataset, patternID)
        
def checkForMods (ATTLIST, tstTime ):
    ret = []    
    for x in ATTLIST:
       if x.modifiedSince (tstTime):
           ret.append (x)
    return ret


def findActor(dataset, aid ):
    for j in dataset['ATKGROUPS']:
        if j.getGroupID() == aid:
            return j
        

def getTargetRecord(dataset, tid):
    for j in dataset['TARGET']:
        if j.getTID() == tid:
            return j

def Timecheck (dataset, tsttime):
   print ('Checking for updates since', tsttime )

   c1 = checkForMods (dataset['ATT&CK'], tsttime )
   if not (c1):
       print ('No changes to TTPs')
   else:
       print ('Changes to TTPs:', len(c1))

   c2 = checkForMods (dataset['ATKGROUPS'], tsttime )
   if not (c2):
       print ('No changes to Intrustion sets')
   else:
       print ('Changes to Intrustion sets:', len(c2))

   c3 = checkForMods (dataset['ATKMALWARE'], tsttime )
   if not (c3):
       print ('No changes to Malware')
   else:
       print ('Changes to Malware:', len(c3))

   c4 = checkForMods (dataset['ATKTOOL'], tsttime )
   if not (c4):
       print ('No changes to Tools')
   else:
       print ('Changes to Tools:', len(c4))    
       
   c5 = checkForMods (dataset['ATKMITIGATION'], tsttime )
   if not (c5):
       print ('No changes to Mitigations')
   else:
       print ('Changes to Mitigations:', len(c5))   


def traverse(dataset, zonemap, startIP, targetIP, surface, platform, trace):    

    cArray = [ 'traverse', startIP, targetIP, surface, platform ]
    iplist = zoneCrawlr.do_traverse (dataset, zonemap, cArray, trace )
    
    if not(iplist):
        if trace:
           print ('WARNING! Traverse returned no IP list')
        return
    
    if trace:
       for x in iplist:
           zoneCrawlr.findTargetComponentIP(dataset, x).PP(False )
       
    return iplist


def getZoneTargets (dataset, zone, bBest, trace):        
    cArray = []
    if bBest:
       cArray = ['targets', zone, 'best' ]
    else:
      cArray = ['targets', zone, 'all' ]    
      
    tgtlist = zoneCrawlr.do_zonetargets(dataset, cArray, trace)
    if not(tgtlist):
        if trace:
            print ('No IPs in zone', zone)
        return
    
    ret = []
    for j in tgtlist:
        ret.append(j[0])
        
    return ret


def getSystemTargets (dataset, sysname, trace ):    
        
    cArray = ['disruptSYS', 'flat=True', sysname]
    
    if trace:
        print ('getSystemTargets input array', cArray)
    
    result = zoneCrawlr.do_disruptSYS (dataset, cArray, trace)    
    if not(result):
        if trace:
            print ('No target list returned for system', sysname)
            return
            
#   use the impact score to filter result list
    maxscore = 0
    for r in result:
        test = int(r[1])
        if test > maxscore:
            maxscore = test
 
    ret = []
    for r in result:
        test = int(r[1])
        if test == maxscore:
           ret.append(r[0])

    return ret

def getFunctionTargets (dataset, fname, trace):
     
    cArray = ['disruptFX', 'flat=true', 'list=top', fname ]
     
    result = zoneCrawlr.do_disruptFX (dataset, cArray, trace)
    if not(result):
       if trace:
           print ('No target list returned for function', fname )
           return

#   use the impact score to filter result list    
    maxscore = 0
    for r in result:
        test = int(r[1])
        if test > maxscore:
            maxscore = test
 
    ret = []
    for r in result:
        test = int(r[1])
        if test == maxscore:
           ret.append(r[0])
           
    return ret
        
def getCapabilityTargets (dataset, capname, trace):
     
    cArray = ['disruptCAP', 'flat=true', 'list=top', capname ]
    
    result = zoneCrawlr.do_disruptCAP (dataset, cArray, trace)
    if not(result):
       if trace:
           print ('No target list returned for capability', capname )
           return

#   use the impact score to filter result list    
    maxscore = 0
    for r in result:
        test = int(r[1])
        if test > maxscore:
            maxscore = test
 
    ret = []
    for r in result:
        test = int(r[1])
        if test == maxscore:
           ret.append(r[0])

    return ret

def filterIPsbyVulnerability(dataset, iplist, vulnkey):

    ret = []   
    for ip in iplist:
       cmp = zoneCrawlr.findTargetComponentIP(dataset, ip)
       vlist = cmp.getVulnerabilityList()
       if not(vlist):
           continue
 
       for v in vlist:
         for e in v.getEffects():
           if e.startswith(vulnkey):
               ret.append([ip, v.getCVE()] )
               break
           else:
              continue
       
    return ret  
        
def genSequence(dataset, zonemap, startIP, destIP, surface, platform, trace):
    
     if trace:
         print ('genSequence: Entry Point:', startIP, 'Destination:', destIP)
                     
     plist = traverse(dataset, zonemap, startIP, destIP, surface, platform,  trace)
       
     if not(plist):
        if trace:
            print ('No path found from', startIP, 'to', destIP+'.')

     return plist

def storeScenarioStats(stats, scnName, attackPath, actor, target, effect, score, ttpseq):
    dataX = defaultdict(list)
    dataX['name'] = scnName
    dataX['path'] = attackPath
    dataX['actor'] = actor
    dataX['target'] = target
    dataX['effect'] = effect
    dataX['score'] = score
    dataX['ttps'] = ttpseq
    stats[scnName].append (dataX)   
    


def getTTPObj(dataset, techID):
    for t in dataset['ATT&CK']:
        if (t.getTECHID() == techID):
            return t        
    for k in dataset['TTP_SUP']:
        if (k.getTECHID() == techID):
            return k        
    print ('WARNING! could not find TTP object for ID:', techID)


def genScenario(stats, dataset, ffactory, scenario, zonemap, entrypoint, target, surface, platform, trace):
    startIP = entrypoint.getIPAddr()
    startZone = entrypoint.getZone()
    destIP = target.getIPAddress()
    destZone = target.getZone()
    effectflag = scenario.getIntendedEffect()
    
    bfull = not(trace)
    
    ret = defaultdict(list)
    ret['ID'] = scenario.getID()+'EP'+startIP
    if bfull:
       ret['NAME'] = scenario.getShortName()
       ret['DESCRIPTION'] = scenario.getDesc()
       ret['ACTOR'] = scenario.getActorID() #.getActor()[0].getName()
       ret['ENTRY_IP'] = startIP
       ret['TARGET_IP'] = destIP
       ret['EFFECT'] = effectflag   

    iplist = genSequence(dataset, zonemap, startIP, destIP, surface, platform, trace )
    if len(iplist) < 2:
        if trace:
           print ('No attack path from', startIP+'('+startZone+')', 'to', destIP+'('+destZone+')', 'found.')
        return
                    
    if trace:
       print('Attack path from', startIP+'('+startZone+')', 'to', destIP+'('+destZone+')', ':', iplist)
 
#   eliminate duplicate IPs in the attack path
    iplist  = list(dict.fromkeys(iplist))   
         
    vtrace = []   
    patseq = GenTacticPattern(iplist, GetPatternbyName (ret['EFFECT']), True )
    ttpmap = GenTTPSequence (dataset, ffactory, patseq, scenario.getActorID(), True, False ) #()[0].getGroupID(), True, False)
       
    for step in patseq:
        cmp = zoneCrawlr.findTargetComponentIP(dataset, step[0])
        sysx = cmp.getSystem()
        strace = [step[0], str(sysx.getLevel())+sysx.getZone(), cmp.getPlatform(), cmp.getVendor(), cmp.getDesc(), cmp.getType(), cmp.getImpactScore(), 
                  cmp.getSysName(), zoneCrawlr.get2ndOrderEffects(dataset, cmp.getSysName()), 
        zoneCrawlr.get3rdOrderEffects(dataset, cmp.getSysName()) ]
        vtrace.append (strace)     
     
    indx = 0
    xtrace = []
    for step in vtrace:
        cmp = zoneCrawlr.findTargetComponentIP(dataset, step[0])
        vlist = cmp.getVulnerabilityList()
        
        ttplist = []
        entry = ttpmap[indx]
        for j in entry[1:]:
            if j:
                ttplist.append (getTTPObj(dataset, random.choice(j) ))
            else:
                print('WARNING: TTP filter returned no entries:', entry )
                    
        xtrace.append([step, ttplist, vlist])
        indx = indx + 1
             
    ttplist = []
    for k in xtrace:
        ret['TRACE'].append(STEPtoJSON(k[0], k[1], k[2], bfull ) ) 
        tseq = []
        for t in k[1]:
          tseq.append(t.getTECHID())
        ttplist.append(tseq)
       
    storeScenarioStats(stats, scenario.getID()+'EP'+startIP, iplist, scenario.getActorID(), #()[0].getName(), 
                       destIP, effectflag, cmp.getImpactScore(), ttplist)

    return ret


def CVEtoJSON(ventry, bfull):
    ret = defaultdict(list)    
    ret['CVE_ID'] = ventry.getCVE()    
    if bfull:      
      ret['Description'] = str(ventry.getDescription().encode('utf8'))
      ret['URL'] = ventry.getReferences()
    return ret

def TTPtoJSON(ttp, bfull):
    ret = defaultdict(list)
    ret['TTP_ID'] = ttp.getTECHID()
    if bfull:
        ret['Name'] = ttp.getName()
        ret['Tactic'] = ttp.getTactic()
        ret['Description'] = str(ttp.getDesc().encode('utf8'))
        ret['Platform'] = ttp.getPlatform()
        ret['Detection'] = str(ttp.getDET().encode('utf8'))
        ret['URL'] = ttp.getURL()
    return ret
               
def STEPtoJSON(step, ttpseq, cvelist, bfull):
    ret = defaultdict(list)
    ret['IP'] = step[0]
    ret['Zone'] = step[1]
    if bfull:
        ret['Platform'] = step[2]
        ret['Vendor'] = step[3]
        ret['Description'] = step[4]
        ret['Type'] = step[5]
        ret['Score'] = step[6]
        ret['Effect_1'] = step[7]
        ret['Effect_2'] = step[8]
        ret['Effect_3'] = step[9]
    
    for t in ttpseq:
        ret['TTPs'].append (TTPtoJSON(t, bfull ))
        
    if cvelist:
        for v in cvelist:
            ret['CVEs'].append(CVEtoJSON(v, bfull) )

    return ret


# Generate scenario detail for each SCENARIO object.  Update mySQL table.  
def GENERATE_SCENARIOS (dataset, ffactory, bUpdateSQL, zonemap, dbname='cicat20', trace=False):


    stats = defaultdict(list)
             
    for s in dataset['SCENARIO']:
        
        sval = 0
        for a in dataset['ATKGROUPS']:
            if a.getGroupID() == s.getActorID():
                sval = a.getSophisticationLevel()                
       
        print ('\nEvaluating:', s.getShortName(), 'using pattern:', s.getIntendedEffect(), 'by threat actor:', s.getActorID(), ' Soph:', sval ) 
       
        tid = s.getTargetID()
        trec = getTargetRecord(dataset, tid)
        if not (trec):
            print ('WARNING - cannot find target record', tid)
            s.setDetail('Invalid target record:'+ tid)
            continue
            
        targetIPs = []
        if trec.getType().lower() == 'system':   
           targetIPs = getSystemTargets(dataset, trec.getName(), False)                                
        elif trec.getType().lower() == 'function':
          targetIPs = getFunctionTargets (dataset, trec.getName(), False)
        elif trec.getType().lower() == 'capability':
          targetIPs = getCapabilityTargets(dataset, trec.getName(), False)
        else:
          targetIPs.append (trec.getName())  # COMPONENT targets use IP address as name

        if not(targetIPs):
           print('Target:', trec.getType(), trec.getName(), 'not found in system model.')
           s.setDetail ('Target '+ trec.getType() + ' ' + trec.getName() + ' not found in system model.')
           continue
 
        destIP = random.choice(targetIPs)
        tgtcmp = zoneCrawlr.findTargetComponentIP(dataset, destIP)
        
        scndump = defaultdict(list)        
        for ep in dataset['ENTRYPOINT']: 
            scn = genScenario(stats,  dataset, ffactory, s, zonemap, ep, tgtcmp, 'any', 'any', trace )
            if scn:
               scndump[destIP].append (scn)
               print('  Scenario created for attack path from:', ep.getIPAddr() )
#            else:
#               print('Scenario:', s.getShortName(), 'Target:', tgtcmp.getIPAddress(), 'Entry point:', ep.getIPAddr(), 'no attack path.')
            
        s.setDetail(json.dumps(scndump))

    if bUpdateSQL:
        print('Updating mySQL scenario table..')
        refreshSCENARIOs(dataset, True, dbname)

    return stats

# Helper function for reading options from command line
def optionReader(params, flag):
    idx = params.index(flag)
    if len(params) > idx + 1 and '-' not in params[idx + 1]:
        return params[idx + 1]
    else:
        print(flag + ' flag must include an option!')
        exit()
   
# Main function that runs scenario generator
def generate(reportOpt, Ispread, Tspread, dbUpdate, dbname, trace=False):
    m_DATASET = LOAD_DATA(Ispread, Tspread, True, False)

    # Initialize topology
#    zoneCrawlr.INIT_TOPOLOGY(m_DATASET, True) 
#    zonemap = zoneCrawlr.buildZoneMap(zoneCrawlr.m_zoneCIs) 
    
    zonemap = zoneCrawlr.INIT_TOPOLOGY(m_DATASET, True ) 
        
    # Initialize ODNI staging
    loadODNI(m_file_ODNI)
    mapTTPs(m_DATASET['ATT&CK']) 
   
    LOAD_TTP_SUPPLEMENT(m_DATASET) #, 'ATTACK_EXTENSIONS.xlsx', 'ATT&CKSUP')
    LOAD_ATK4ICS (m_DATASET, '..\\data\ATK4ICS.xlsx' )
    LOAD_ACTOR_PROFILES (Tspread, m_DATASET, ['SCADACAT', 'ICSCUB_1', 'RedCanary', 'APT28', 'APT1', 'OilRig', 'Lazarus Group', 'Leviathan'] )

    denyTactics = []
    for t in m_DATASET['TTP_SUP']:
        if ['deny' in t.getTactic()]:
            denyTactics.append(t)          
    
    augmentTTPs('deny', denyTactics)
    
    ffactory = FILTER_FACTORY(False )
    INIT_FILTERS (ffactory, m_DATASET )
    initPatternMenu()
  
    myStats = GENERATE_SCENARIOS(m_DATASET, ffactory, dbUpdate, zonemap, dbname, trace)      
    SCENARIO_REPORT(m_DATASET, myStats, reportOpt)    # options ['Details', 'Mitigations', 'Forensics'] )   
  
#   GENERATE_MITIGATIONS (m_DATASET, myStats, 'test')
    print('End of run')

"""
scenGEN.py  - Attack Scenario Generation Tool

Input parameters:

Infrastucture spreadsheet filename: required
Threat spreadsheet filename: required

Reporting options:
   'Details' - reports TTP descriptions
   'Mitigations' - reports TTP mitigations
   'Forensics' - reports TTP detection techniques

"""

# main entry point
if ( __name__ == "__main__"):
        
#  default settings
    Ispread = m_file_INFRASTRUCTURE
    Tspread = m_file_SCENARIOS
    reportOpt = 'Details'
    dbUpdate = False
    dbname = 'cicat2'
    trace = False
 
    params = sys.argv
    if len(params) > 1:
        if 'help' in params[1].lower():
            print ('\nUSAGE: python', params[0], '[-r (Details|Mitigations|Forensics)] [-u|--update] [-i <Path to Infrastructure spreadsheet>] [-s <Path to Scenarios spreadsheet>] [-db <name of database on localhost to update>] [-trace <output debug messages to console>]')
            exit()

        if '-r' in params:
            reportOpt = optionReader(params, '-r')

        if '--update' in params or '-u' in params:
            dbUpdate = True
        
        if '-i' in params:
            Ispread = optionReader(params, '-i')

        if '-s' in params:
            Tspread = optionReader(params, '-s')

        if '-db' in params:
            dbname = optionReader(params, '-db')
        
        if '-trace' in params:
            trace = True
        
    generate(reportOpt, Ispread, Tspread, dbUpdate, dbname, trace)
