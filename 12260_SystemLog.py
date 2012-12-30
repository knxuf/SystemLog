# -*- coding: iso8859-1 -*-
## -----------------------------------------------------
## Logik-Generator  V1.5
## -----------------------------------------------------
## Copyright © 2012, knx-user-forum e.V, All rights reserved.
##
## This program is free software; you can redistribute it and/or modify it under the terms
## of the GNU General Public License as published by the Free Software Foundation; either
## version 3 of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
## without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
## See the GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along with this program;
## if not, see <http://www.gnu.de/documents/gpl-3.0.de.html>.

### USAGE:  python.exe LogikGenerator.py [--debug --en1=34 --en2="TEST"]



import sys
import codecs
import os
import base64 
import marshal
import re
try:
    from hashlib import md5
except ImportError:
    import md5 as md5old
    md5 = lambda x='': md5old.md5(x)
import inspect
import time
import socket
import tempfile
import zlib
import zipfile

##############
### Config ###
##############

## Name der Logik
LOGIKNAME="SystemLog"
## Logik ID
LOGIKID="12260"

## Ordner im GLE
LOGIKCAT="www.knx-user-forum.de"


## Beschreibung
LOGIKDESC="""
Zentrales Logsystem
"""
VERSION="V2.011"


## Bedingung wann die kompilierte Zeile ausgeführt werden soll
BEDINGUNG="EN[1] or EN[2] or EN[3] or EI"
## Formel die in den Zeitspeicher geschrieben werden soll
ZEITFORMEL=""
## Nummer des zu verwenden Zeitspeichers
ZEITSPEICHER="0"

## AUF True setzen um Binären Code zu erstellen
doByteCode=False
#doByteCode=True

## Base64Code über SN[x] cachen
doCache=False

## Doku erstellen Ja/Nein
doDoku=True

debug=False
livedebug=False

showList=False
#############################
########## Logik ############
#############################
LOGIK = '''# -*- coding: iso8859-1 -*-
## -----------------------------------------------------
## '''+ LOGIKNAME +'''   ### '''+VERSION+'''
##
## erstellt am: '''+time.strftime("%Y-%m-%d %H:%M")+'''
## -----------------------------------------------------
## Copyright © '''+ time.strftime("%Y") + ''', knx-user-forum e.V, All rights reserved.
##
## Dieses Werk ist unter einem Creative Commons Namensnennung-Weitergabe unter gleichen Bedingungen 3.0 Deutschland Lizenzvertrag lizenziert.
## Um die Lizenz anzusehen, gehen Sie bitte zu http://creativecommons.org/licenses/by-sa/3.0/de/ 
## oder schicken Sie einen Brief an Creative Commons, 171 Second Street, Suite 300, San Francisco, California 94105, USA.

## -- ''' +re.sub("\n","\n## -- ",LOGIKDESC)+ ''' 

#5000|"Text"|Remanent(1/0)|Anz.Eingänge|.n.|Anzahl Ausgänge|.n.|.n.
#5001|Anzahl Eingänge|Ausgänge|Offset|Speicher|Berechnung bei Start
#5002|Index Eingang|Default Wert|0=numerisch 1=alphanummerisch
#5003|Speicher|Initwert|Remanent
#5004|ausgang|Initwert|runden binär (0/1)|typ (1-send/2-sbc)|0=numerisch 1=alphanummerisch
#5012|abbruch bei bed. (0/1)|bedingung|formel|zeit|pin-ausgang|pin-offset|pin-speicher|pin-neg.ausgang

5000|"'''+LOGIKCAT+'''\\'''+LOGIKNAME+'''_'''+VERSION+'''"|0|9|"E1 Zentrales Log iKO"|"E2 Store Filter"|"E3 View Filter"|"E4 Ack Filter"|"E5 XML Formatstring-1"|"E6 XML Formatstring-2"|"E7 XML Formatstring-3"|"E8 Action"|"E9 erweiterte Konfig"|4|"A1 XML-Logliste-1"|"A2 XML-Logliste-2"|"A3 XML-Logliste-3"|"A4 Buffer"

5001|9|4|2|2|1

# EN[x]
5002|1|""|1 #* Zentrales Log iKO 
5002|2|"*.*"|1 #* Store Filter 
5002|3|"*.>notice"|1 #* View Filter
5002|4|"-1,0,1"|1 #* Ack Filter
5002|5|"%(ndate).8s %(ntime).8s %(facility).15s: %(severity).6s - %(message).50s"|1 #* Ausgabeformat1 
5002|6|"<id>%(id)s</id>%(ndate).5s %(ntime).8s %(facility).15s: %(severity).6s - %(message).50s"|1 #* Ausgabeformat2 
5002|7|""|1 #* Ausgabeformat3
5002|8|""|1 #* Action
5002|9|""|1 #* Konfig

# Speicher
5003|1||0 #* Klassenspeicher @@classSystemLog
5003|2|0|0 #* MustSave



# Ausgänge
5004|1|""|0|1|1 #* XML Logliste1 
5004|2|""|0|1|1 #* XML Logliste2 
5004|3|""|0|1|1 #* XML Logliste3 
5004|4|""|0|1|1 #* Remanent Buffer

#################################################

'''
#####################
#### Python Code ####
#####################
code=[]
code.append([3,"EI","""
## KNXUF_SystemLOG
if EI==1:
    global time,re,zlib,cPickle
    import zlib
    import cPickle
    import time
    import re
    
    global KNXUF_WebAttach
    class KNXUF_WebAttach:
        def __init__(self,pItem,datasource,name,typ='text/xml'):
            self.MC           = pItem.MC
            self.__datasource = datasource
            self.UrlPfad      = name.upper()
            self.DatName      = "OPT/%s" % (self.UrlPfad)
            self.DatLen       = 0
            self.Typ          = typ
            self.isQuad       = 0
            
            self.MC.GUI.ExtDatUrl[self.UrlPfad] = self
            ###DEBUG###print "Exporter installiert unter %s"  % ( self.UrlPfad )
        
        def update(self):
            self.DatLen = self.__datasource()
        
        def getDaten(self):
            return
        def getQuadDaten(self):
            return 
        
        def getDatenStream(self,stream):
            self.DatLen = self.__datasource( stream )

        def getQuadDatenStream(self,stream):
            self.getDatenStream( stream )


    global KNXUF_remanentBuffer
    class KNXUF_remanentBuffer:
        ######################################################################################
        ## Erstellt einen remanenten Buffer
        ## paramenter: pItem , Nummer des Ausgangs
        ## buffer=remanentBuffer(pItem, outlet=3 ,compressionlevel=1)
        ######################################################################################
        def __init__(self,pItem,outlet,compressionlevel=6):
            self.logik = pItem
            self.compressionlevel = compressionlevel
            
            self.realsize = 0.0
            self.zipsize = 0.0
            
            self.__buffer = []
            
            ## Alle iKO's 
            for iko in pItem.Ausgang[outlet-1][1]:
                ## Wenn Typ 14Byte und Remanent ist
                if iko.Format == 22 and iko.SpeicherID != 0:
                    self.__buffer.append(iko)

        #################################################
        ## gibt Infos über den Buffer wieder
        ##
        #################################################
        def info(self):
            numbuf     = len(self.__buffer)
            buffersize = numbuf *10000
            return {
                'numbuffer': numbuf, 
                'realsize': self.realsize/1000,
                'zipsize': self.zipsize/1000,
                'maxKB': buffersize/1000,
                'percent': int(self.zipsize/buffersize*100)
            }
                
        
        #################################################
        ## gibt die Daten wieder zurück
        ## Bei Fehler None
        #################################################
        def read(self):
            ###DEBUG###print "Remanentdaten einlesen"
            if not self.__buffer:
                return None
            try:
                raw = "".join([iko.getWert() for iko in self.__buffer])
            except:
                return None
                
            ## zlib Objekt anlegen
            decompobj = zlib.decompressobj()
            
            ##  Grösse des ZIP
            self.zipsize = float(len(raw))
            try:
                ## decompression 
                ret = decompobj.decompress(raw)
                
                ## benutzten Speicher ermitteln
                self.realsize = self.zipsize - len(decompobj.unused_data)
                ###DEBUG###print "ZIP Grösse: %d (%d)" % (self.zipsize,self.realsize)

                ## ZLIB Objekt löschen
                decompobj.flush()
            except:
                ###DEBUG###print "Fehler beim entpacken"
                return None
                
            try:
                ## Return Objekt
                return cPickle.loads(ret)
            except:
                return None
        
        
        #################################################
        ## speichert die übergebenen Daten ab
        ## gibt die prozentuale Nutzung zurück
        ## -1 bei Fehler 100 bei voll
        #################################################
        def write(self,val):
            ###DEBUG###print "Remanentdaten schreiben"
            try:
                data = cPickle.dumps(val)
            except:
                return -1

            ## Grösse ermitteln
            self.realsize = float(len(data))
            try:
                ## Daten gleich komprimieren
                data         = zlib.compress( data, self.compressionlevel )
                self.zipsize = float(len(data))
            except:
                return -1
            
            try:
                for iko in self.__buffer:
                    
                    iko.setWert(0,data[:10000])
                    data = data[10000:]
                
                if data:
                    ## return 100% Full
                    return 100
            except:
                return -1
            
            return int(self.zipsize/(len(self.__buffer)*10000)*100)
            

    ####################################################
    ### SystemLog
    ####################################################
    class KNXUF_SystemLog:
        def __init__(self,pItem,localvars):
            try:
                import random
            except ImportError:
                import whrandom as random
            try:
                from hashlib import md5
            except ImportError:
                import md5 as oldmd5
                md5 = lambda x='',oldmd5=oldmd5: oldmd5.md5(x)

            self.logik = pItem
            self.MC = pItem.MC

            EN = localvars['EN']

            self.localvars = localvars
            
            self.config = {
                'dateformat': 0,
                'listlength': -1,
                'export'    : 1,
                'name'      : 'SystemLog ID:%d' % (pItem.ID), 
                'lang'      : 'de',
            }
            
            self.setConfig(EN[9])
            
            
            self.i18n       = {}
            self.i18n['de'] = {'todaystring':'heute',  'yesterdaystring':'gestern',  'debug_Loglen':'Eintr&auml;ge',   'debug_buffersize':'Buffergr&ouml;sse', 'debug_buffersizeText':'%d Buffer %.2f/%d KB belegt'}
            self.i18n['en'] = {'todaystring':'today',  'yesterdaystring':'yesterday','debug_Loglen':'Entries',         'debug_buffersize':'Storage size',      'debug_buffersizeText':'%d remanent-storages %.2f/%d KB used'}
            self.i18n['nl'] = {'todaystring':'vandaag','yesterdaystring':'gistere n','debug_Loglen':'Lijst met invoer','debug_buffersize':'Buffergrootte',     'debug_buffersizeText':'%d remanentgeheugen %.2f/%d KB gebruikt' }
            
            ## Sprache setzen - default 'de'
            self.lang       = self.i18n.get(self.config['lang'].lower(),self.i18n.get('de'))

            self.__Version__ = '""" +VERSION+ """'
            
            self.severityEnum = {
                'emerg':   0, 
                'alert':   1, 
                'crit':    2, 
                'error':   3,
                'warn'   : 4,
                'warning': 4, 
                'notice':  5, 
                'info':    6, 
                'debug':   7 
            }
            ## reverse
            self.EnumSeverity = dict( [ (v,k) for k,v in self.severityEnum.iteritems()] )
            
            self.__LogikID__ = md5(str(random.random())).hexdigest()
            
            self.SystemLogName = self.config['name']
            
            self.__remanentBuffer = KNXUF_remanentBuffer(pItem,4,compressionlevel=4)
            
            data = self.__remanentBuffer.read()
            if type(data) == dict:
                self.__logList = data.get('loglist',[])
                self.__ACCESSID__ = data.get('accessID', self.__LogikID__ )
            else:
                self.__logList = []
                self.__ACCESSID__ = self.__LogikID__


            self.webURL = "SYSTEMLOG/%s/list.htm" % ( self.__ACCESSID__ )
            if self.config['export']:
                KNXUF_WebAttach(pItem,self.webUpdate,self.webURL,typ='text/html')
            
            self.__OutputConnect = [ -1, -1, -1 ]
            self.connectContent  = [ [],[],[] ]
            self.__WebContent    = []

            self.daysFromEpoch = lambda x: ( int( time.mktime( x[:3] + (0,0,0,0,0,0) ) - time.timezone ) ) / 86400

            self.xmlFormatString = [EN[5],EN[6],EN[7]]
            
            self.webFormatString = "<tr><td class='l'>%(ndate)5s</td><td class='l'>%(ntime)5s</td><td class='l'>%(adate)s</td><td class='l'>%(atime)s</td><td>%(severity)s</td><td>%(facility).20s</td><td>%(message).80s</td></tr>"

            self.setDateFormat( self.config['dateformat'] )
            
            self.__logRegex     = re.compile( r"<log>(.*?)</log>" )
            self.__contentRegex = re.compile( r"<(.*?)>(.*?)</\\1>" )
            #re.findall("<(\w+)\s*(.*?)>(.*?)</\\1",xml)
            self.__commandRegex = re.compile( r"(ack|nack|del|clearall):([\da-fA-F]+)" )
            
            self.__filter = {}
            
            self.__ACKfilter = [-1,0,1]
            
            
            self.__writeStat()
        
        ##
        ## HTML an der eigentlich setwert Funktion vorbei in die Debugseite schreiben
        ## * übergeben werden wert der in die Debug soll
        ##
        def debug_write(self,pWert):
            if self.config['export']:
                _name = "<a href='/OPT/%s' target='_blank'>%s</a>" % ( self.webURL, self.SystemLogName )
            else:
                _name = self.SystemLogName 

            _grp = filter(lambda x: x[0]=="SYSTEMLOG",self.MC.Debug.Daten)
            if not _grp:
                self.MC.Debug.addGruppe(
                    ["SYSTEMLOG" , "Systemlog"],
                      [ 
                        ["0VERSIONINFO",      "Version", 1,'"""+ VERSION + time.strftime(" - (%Y%m%d%H%M)")+ r"""'],
                        [ self.__LogikID__ ,    _name,    1, pWert ] ,
                      ]   
                )

            else:
                _grp_entry = _grp[0][2]
                _tok = filter(lambda x,y=self.__LogikID__: x[0]==y, _grp_entry)
                if _tok:
                    _tok[0][3] = pWert


        def findOutput(self):
            ## Ausgänge 1-3 
            for a in xrange(0,2):
                if len(self.logik.Ausgang[a][1]) > 0:
                    ## kein Direct Connect wenn iKO benutzt wird
                    self.__OutputConnect[a] = 0
                    continue
                
                ## Alle Logiken an Ausgang x
                for logik in self.logik.Ausgang[a][3]:
                    ## Alle Speicher der Logik
                    for speicher in logik[0].SpeicherWert:
                        ## wenn Type von SN[x] == instance
                        if type(speicher) == type(self):
                              if hasattr(speicher,'DirectConnect'):
                                  ###DEBUG###print "Found DirectConnect (%d) in Logik %d" % (logik[0].LogikItem.ID,logik[0].ID)
                                  self.__OutputConnect[a] = 1
                                  speicher.DirectConnect = [self.connectContent,a]


        def webUpdate(self,stream=False):
            content = "<html><head><style type='text/css'>td { text-align: right; } td.l { text-align: left; }</style></head><body><table border=1 cellspacing=5>%s</table></body></html>"      % (  "".join(self.__WebContent) )
            if stream:
                stream.write(content)
            return len(content)

        def log(self,logmsg):
            ###DEBUG###print "LOGMSG: %r" % (logmsg)
            save = 0
            for msg in self.__logRegex.findall(logmsg):
                msgdict = {
                    'time'    : int(time.time()),
                    'acktime' : 0,
                    'astate'  : -1,
                    'id'      : '',
                    'severity': 7,
                    'facility': 'System',
                    'message' : ''
                }
                
                for tag,val in self.__contentRegex.findall( msg ):
                    ###DEBUG###print "ADD Value: %s: %s" % (tag,val)
                    try:
                        msgdict[ tag.lower() ] = val
                    except:
                        pass
                
                ## save Nummer nicht Name der severity
                msgdict['sevnum'] = msgdict['severity'] = self.severityEnum.get(msgdict['severity'],7)
                if len( msgdict['id'] ) != 0:
                    if self.checkFilter('store',msgdict):
                        ###DEBUG###print "ADD %r to List" % (msgdict)
                        del msgdict['sevnum']
                        self.__logList.insert(0,msgdict)
                        save += 1
            
            if save > 0:
                self.save()
                self.updateContent( self.getParseDict( msgdict ) )
            
            return True


        def setxmlOutputString(self,xml1,xml2,xml3):
            self.xmlFormatString = [ xml1 , xml2 , xml3 ]

        def getParseDict(self,entry):
            
            parsedict={'id':'','severity':'info','facility':'System','message':'','time':0,'ndate':'','nyear':'','ntime':'','sevnum':5,'acktime':0,'adate':'','ayear':'','atime':'','astate':-1}
            ## Update with defaults
            parsedict.update(entry)

            ## Zeit
            parsedict['ntime'] = "%02d:%02d:%02d" % time.localtime( entry['time'] )[3:6]
            ## Datum
            parsedict['ndate'] = parsedict['date'] = self.mkDate( time.localtime( entry['time'] ) )
            ## Jahr
            parsedict['nyear'] = time.strftime( "%Y",time.localtime( entry['time']) )
            
            ## Nummer der severity 
            parsedict['sevnum'] = parsedict['severity']
            parsedict['severity'] = self.EnumSeverity.get( parsedict['severity'] ,'debug')
            
            if parsedict['acktime'] > 0:
                ## ack time
                parsedict['atime']  = "%02d:%02d:%02d" % (time.localtime( parsedict['acktime'] )[3:6])
                ## ack date
                parsedict['adate']  = self.mkDate( time.localtime( parsedict['acktime'] ) )
                ## ack status
            parsedict['astate'] = parsedict.get('astate',-1)
            return parsedict

        def updateContent(self,parsedict):
            if not self.checkFilter('view',parsedict):
                return
            if parsedict['astate'] not in self.__ACKfilter:
                ###DEBUG###print "CHECK ACKSTATE: %r " % (parsedict['astate'])
                return
            for o in xrange(3):
                if self.__OutputConnect[o] > -1:
                    ## anwenden wenn verbunden
                    try:
                        self.connectContent[o].insert(0,self.xmlFormatString[o] % parsedict)
                    except KeyError,xkeyerr:
                        ###DEBUG###print "KeyError: %s in %r" % (xkeyerr,parsedict)
                        pass
                    except TypeError:
                        ###DEBUG###print "TYPE Error: %r " %(parsedict)
                        pass
            
            try:
                self.__WebContent.insert(0,self.webFormatString % parsedict)
            except (KeyError,TypeError):
                pass

        def sendContent(self,localvar):
            AN = localvar['AN']
            AC = localvar['AC']
            
            for o in xrange(3):
                if self.__OutputConnect[o] == -1:
                    continue
                elif self.__OutputConnect[o] == 0:
                    AN[o+1] = "<xml>%s</xml>" % ("".join([ "<%d>%s</%d>" % (i,self.connectContent[o][i],i) for i in range(len(self.connectContent[o]))]))
                elif self.__OutputConnect[o] == 1:
                    AN[o+1] = "###DIRECT-CONNECT###"
                print "AN[%s] == %r" % (o+1,AN[o+1])
                AC[o+1] = 1
            
            ## SN[2] wieder auf Falsch
            return False
        

        def generateLists(self):
            ###DEBUG###print "SystemLogList-length: "+str(len(self.__logList))
            for a in xrange(3):
                self.connectContent[ a ] = []
            self.__WebContent = []
            for entry in reversed(self.__logList):
                parsedict = self.getParseDict(entry)
                self.updateContent(parsedict)
            return True

        ##
        ## Configuration von String lesen
        ##
        def setConfig(self,newconfig):
            if not newconfig:
                return
            for option in newconfig.split('*'):
                try:
                    key , val = option.split("=",1)
                    ## Wert in Integer wandeln
                    val = type(self.config[key])(val)
                    ## Wenn gültig dann setzen sonst KeyError 
                    self.config[key] = val
                except KeyError:
                    pass
                    ###DEBUG###print "Konfig fehlgeschlagen: "+option
                except ValueError:
                    pass
                    ###DEBUG###print "Konfig wrong Value: "+option
            ###DEBUG###print "Konfig: %r" % (self.config)


        def save(self):
            ## Liste kürzen
            if self.config['listlength'] > 0:
                while len(self.__logList) > self.config['listlength']:
                    self.__logList.pop()
            
            size = 100
            while size > 95:
                size = self.__remanentBuffer.write( {
                    'Version' : self.__Version__,
                    'loglist' : self.__logList,
                    'accessID': self.__ACCESSID__ 
                })
                if size >95:
                    self.config['listlength'] = len(self.__logList)-2
                    self.__logList.pop()
                    self.__logList.pop()
                    ###DEBUG###print "Liste um 2 reduziert auf %d" % (self.config['listlength'])
            
            if size < 80 and (self.config['listlength'] == len(self.__logList)):
                self.config['listlength'] += 1
                ###DEBUG###print "Liste um 1 vergrößert auf %d" % (self.config['listlength'])
            self.__writeStat()


        def __writeStat(self):
            dbgMsg = [ "<span style='color:red;'>Failed</span>" ]
            DirectCInfo = "".join( [ (self.__OutputConnect[o]==1 and "DC:%d" % (o+1) or "") for o in xrange(3) ] )
            if self.__remanentBuffer:
                ## 'numbuffer','realsize','zipsize','maxKB','percent'
                stats = self.__remanentBuffer.info()
                dbgMsg = []
                dbgMsg.append("%s: " % ( self.lang['debug_buffersize'] ) )
                dbgMsg.append(self.lang['debug_buffersizeText'] % (stats['numbuffer'],stats['zipsize'],stats['maxKB']))
                dbgMsg.append("<br>%s: %d/%d " % (self.lang['debug_Loglen'], len(self.__logList), self.config['listlength']))
                if DirectCInfo:
                    dbgMsg.append("<span type='size:xx-small;'><br>%s</span>" % (DirectCInfo))
            
            self.debug_write("".join(dbgMsg))



        def setDateFormat(self,dformat):
            ## Differenz zu epoch==1.1.1970 00:00:00 UTC DST=0, daher auch hier dst=0 und timezone(-3600) abgezogen
            self.todayDay = self.daysFromEpoch(time.localtime())
            
            if dformat == 1:
                self.mkDate = lambda x,y=self.todayDay, yesterday=self.lang['yesterdaystring'],dfe=self.daysFromEpoch: (y-dfe(x)==0 and ' ') or (y-dfe(x)==1 and yesterday) or time.strftime("%d.%m",x)
            elif dformat == 2:
                self.mkDate = lambda x,y=self.todayDay, today=self.lang['todaystring'] , yesterday=self.lang['yesterdaystring'],dfe=self.daysFromEpoch: (y-dfe(x)==0 and today) or (y-dfe(x)==1 and yesterday) or time.strftime("%d.%m",x)
            else:
                ## Immer Datum Tag.Monat
                self.mkDate = lambda x: time.strftime("%d.%m",x)
            ###DEBUG###print "Datumsformat auf %d gesetzt" % ( dformat )
            

        def makeFilter(self,ftype,filterstring):
            ## Filter löschen
            self.__filter[ftype] = []
            
            getrange = lambda z: map(lambda x,enu=self.severityEnum: enu.get(x,-1),z)
            
            for rule in filterstring.split("#"):
                ruleset = rule.split(".")[:3]
                if len(ruleset) < 1:
                    continue
                if not ruleset[0]:
                    continue
                addrule = {
                    'facility' : { }, 
                    'severity' : { 0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0 }, 
                    'message'  : [ [],[] ]
                }
                self.__filter[ftype].append(addrule)
                
                
                ## Facility
                if ruleset[0].startswith("-"):
                    addrule['facility'] = { ruleset[0][1:] : -1 }
                    ## negativ nächste Regel
                    continue
                else:
                    addrule['facility'] = { ruleset[0]     : 1 } 
                
                ## Abruch wenn nicht mehr
                if len(ruleset) < 2:
                    addrule['severity'] = { }
                    continue

                retval = 1
                if len(ruleset) < 3:
                    retval = 2
                ## Serverity
                for severity in ruleset[1].split(","):
                    if severity == "*":
                        for x in xrange(0,8):
                            addrule['severity'][x] = retval
                    elif severity.startswith(">"):
                        for x in xrange( 0, self.severityEnum.get(severity[1:],-1) +1 ):
                            addrule['severity'][x] = retval
                    elif severity.startswith("<"):
                        for x in xrange( self.severityEnum.get(severity[1:],8) +1 ,8 ):
                            addrule['severity'][x] = retval
                    elif severity.find("-") > 1:
                        srange = map(lambda x,enu=self.severityEnum: enu.get(x,-1), severity.split("-")[:2])
                        srange.sort()
                        for x in xrange( srange[0],srange[1] ): 
                            addrule['severity'][x] = retval
                    elif severity.startswith("-"):
                        srange =  self.severityEnum.get(severity[1:],-1)
                        if srange:
                            addrule['severity'][srange] = -1
                    else:
                        srange =  self.severityEnum.get(severity,-1)
                        if srange:
                            addrule['severity'][srange] = retval
                          
                if len(ruleset) < 3:
                      continue
                            
                for msgfilter in ruleset[2].split(","):
                    if msgfilter.startswith("-"):
                        addrule['message'][1].append(msgfilter[1:])
                    else:
                        addrule['message'][0].append(msgfilter)
        
        
        def makeACKFilter(self,cfg):
            if cfg == "":
                cfg = [ -1 , 0 , 1 ]
            else:
                cfg = [int(i) for i in cfg.split(",")]
                
            ###DEBUG###print "ACKFILTER: %r" % (cfg)
            self.__ACKfilter = cfg
            
        def checkFilter(self,ftype,msg):
            for rules in self.__filter.get(ftype,[]):
                ## {'facility': {'rollladen': 1 } , 'severity' : { 0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0 }, 'message': [ [+], [-] ] } 

                ## check facility
                ###DEBUG###print "Check Facility: %r " % (msg['facility'])
                action = rules['facility'].get( msg['facility'],  rules['facility'].get( "*" ,0) )
                if action == -1:
                    ###DEBUG###print "%r not in denied" % (msg['facility'])
                    return False
                elif action == 0:
                    ###DEBUG###print "%r not in rule" % (msg['facility'])
                    continue
                
                ## check severity
                action = rules['severity'].get( msg['sevnum'] ,2)
                ###DEBUG###print "check severity: %r (%r) " % (msg['severity'],msg['sevnum'] )
                if action == -1:
                    ###DEBUG###print "Severity: %r denied" % (msg['severity'])
                    return False
                elif action == 0:
                    ###DEBUG###print "Goto Next Rule"
                    continue
                elif action == 2:
                    ###DEBUG###print "Full Access"
                    return True
                
                ## check msgfilter
            ###DEBUG###print "Default Deny"
            return False


        def cmd(self,action):
            ###DEBUG###print "CMD: %r" % (action)
            for cmd in self.__commandRegex.findall(action):
                if cmd[0] == "clearall":
                    ###DEBUG###print "DELETE ALL"
                    self.__logList = []
                else:
                    ## Alle Einträge mit der ID suchen    
                    for entry in filter( lambda x,y=cmd[1]: x['id']==y ,self.__logList):
                        try:
                            index = self.__logList.index(entry)
                            
                            ###DEBUG###print "Do Command: %r Index: % d" % (cmd[0],index)
                            if cmd[0] == "ack":
                                self.__logList[index]['acktime'] = int( time.time() )
                                self.__logList[index]['astate'] = 1
                            
                            elif cmd[0] == "nack":
                                self.__logList[index]['astate'] = 0
                            
                            elif cmd[0] == "del":
                                del self.__logList[index]
                            
                            else:
                                return False
                        except IndexError:
                            pass
                        except KeyError:
                            pass
                
            self.save()        
            self.generateLists()
            return True
        

"""])
postlogik=[0,"","""
5012|0|"EI"|"KNXUF_SystemLog(pItem,locals())"|"0.1"|0|1|1|0

5012|0|"OC[1]"|"SN[1].findOutput()"|""|0|0|0|0

5012|0|"OC[1] or EC[2]"|"SN[1].makeFilter('store',EN[2])"|""|0|0|0|0
5012|0|"OC[1] or EC[3]"|"SN[1].makeFilter('view',EN[3])"|".1"|0|2|0|0
5012|0|"OC[1] or EC[4]"|"SN[1].makeACKFilter(EN[4])"|".1"|0|2|0|0

## Listen generieren und um 00:00 neu generieren
5012|0|"OC[2]"|"SN[1].generateLists()"|"86400 - (lambda x=__import__('time').localtime()[3:6]: float(x[0]*3600)+(x[1]*60)+x[2])()"|0|2|2|0

5012|0|"EC[1] and len(EN[1]) > 0"|"SN[1].log(EN[1])"|""|0|0|2|0

5012|0|"EC[5] or EC[6] or EC[7]"|"SN[1].setxmlOutputString(EN[5],EN[6],EN[7])"|"1"|0|2|0|0


5012|0|"EC[8]"|"SN[1].cmd(EN[8])"|""|0|0|2|0

5012|0|"SN[2]"|"SN[1].sendContent(locals())"|""|0|0|2|0

"""]

####################################################################################################################################################


###################################################
############## Interne Funktionen #################
###################################################

LGVersion="1.5"

livehost=""
liveport=0
doSend=False
noexec=False
nosource=False
doZip=False
for option in sys.argv:
    if option.find("--new")==0:
        try:
            LOGIKID=int(option.split("=")[1].split(":")[0])
            LOGIKNAME=option.split("=")[1].split(":")[1]
            try: 
                LOGIKCAT=option.split("=")[1].split(":")[2]
            except:
                pass
        except:
            print "--new=id:name[:cat]"
            raise
            sys.exit(1)

        if LOGIKID >99999 or LOGIKID == 0:
            print "invalid Logik-ID"
            sys.exit(1)

        if LOGIKID <10000:
            LOGIKID+=10000
        LOGIKID="%05d" % LOGIKID
        f=open(inspect.currentframe().f_code.co_filename,'r')
        data=""
        while True: 
            line = f.readline()
            if line.find("LOGIKID=") == 0:
                line = "LOGIKID=\""+LOGIKID+"\"\n"
            if line.find("LOGIKNAME=") == 0:
                line = "LOGIKNAME=\""+LOGIKNAME+"\"\n"
            if line.find("LOGIKCAT=") == 0:
                line = "LOGIKCAT=\""+LOGIKCAT+"\"\n"
            data += line
            if not line: 
                break 
        f.close()
        open(str(LOGIKID)+"_"+LOGIKNAME+".py",'w').write(data)
        sys.exit(0)

    if option=="--list":
        showList=True
      
    if option=="--debug":
        debug=True

    if option=="--noexec":
        noexec=True

    if option=="--nosource":
        nosource=True    

    if option=="--zip":
        doZip=True

    if option=="--nocache":
        doCache=False
      
    if option.find("--live")==0:
        livedebug=True
        debug=True
        doByteCode=False
        doCache=True
        try:
            livehost=option.split("=")[1].split(":")[0]
            liveport=int(option.split("=")[1].split(":")[1])
        except:
            print "--live=host:port"

    if option.find("--send")==0:
        doSend=True
        try:
            livehost=option.split("=")[1].split(":")[0]
            liveport=int(option.split("=")[1].split(":")[1])
        except:
            print "--send=host:port"
          

print "HOST: "+livehost+" Port:" +str(liveport)
### DEBUG ####
EI=True
EA=[]
EC=[]
EN=[]
SA=[]
SC=[]
SN=[]
AA=[]
AC=[]
AN=[]
OC=[]
ON=[]
if debug or doSend:
    EA.append(0)
    EC.append(False)
    EN.append(0)
    AA.append(0)
    AC.append(False)
    AN.append(0)
    SA.append(0)
    SC.append(False)
    SN.append(0)
    ON.append(0)
    OC.append(False)

    ## Initialisieren ##
    for logikLine in LOGIK.split("\n"):
        if logikLine.find("5001") == 0:
            for i in (range(0,int(logikLine.split("|")[3]))):
              ON.append(0)
              OC.append(False)
        if logikLine.find("5002") == 0:
            EN.append(logikLine.split("|")[2].replace('\x22',''))
            EA.append(logikLine.split("|")[2])
            EC.append(False)
        if logikLine.find("5003") == 0:
            if logikLine.split("|")[3][0] == "1":
                SN.append(re.sub('"','',logikLine.split("|")[2]))
            else:
                try:
                    SN.append(int(logikLine.split("|")[2]))
                except:
                    pass
                    SN.append(logikLine.split("|")[2])
            SA.append(logikLine.split("|")[2])
            SC.append(False)
        if logikLine.find("5004") == 0:
            AN.append(logikLine.split("|")[2])
            AA.append(logikLine.split("|")[2])
            AC.append(False)


def bool2Name(b):
  if int(b)==1:
    return "Ja"
  else:
    return "Nein"
def sbc2Name(b):
  if int(b)==1:
    return "Send"
  else:
    return "Send By Change"


def addInputDoku(num,init,desc):
  return '<tr><td class="log_e1">Eingang '+str(num)+'</td><td class="log_e2">'+str(init)+'</td><td class="log_e3">'+str(desc)+'</td></tr>\n'
def addOutputDoku(num,sbc,init,desc):
  return '<tr><td class="log_a1">Ausgang '+str(num)+' ('+sbc2Name(sbc)+')</td><td class="log_a2">'+str(init)+'</td><td class="log_a3">'+str(desc)+'</td></tr>\n'

LOGIKINHTM=""
LOGIKOUTHTM=""

i=0
LEXPDEFINELINE=LHSDEFINELINE=LINDEFINELINE=LSPDEFINELINE=LOUTDEFINELINE=0
for logikLine in LOGIK.split("\n"):
    if logikLine.find("5000") == 0:
        LEXPDEFINELINE=i
        LOGIKREMANT=bool2Name(logikLine.split("|")[2])
        LOGIKDEF=logikLine
    if logikLine.find("5001") == 0:
        LHSDEFINELINE=i
        ANZIN=int(logikLine.split("|")[1])
        ANZOUT=int(logikLine.split("|")[2])
        ANZSP=int(logikLine.split("|")[4])
        CALCSTARTBOOL=logikLine.split("|")[5]
        CALCSTART=bool2Name(CALCSTARTBOOL)
    if logikLine.find("5002") == 0:
        LINDEFINELINE=i
        desc=re.sub('"','',LOGIKDEF.split("|")[3+int(logikLine.split("|")[1])])
        if logikLine.find("#*") >0:
            desc=logikLine.split("#*")[1]
        LOGIKINHTM+=addInputDoku(logikLine.split("|")[1],logikLine.split("|")[2],desc)
    if logikLine.find("5003") == 0 or logikLine.find("# Speicher") == 0:
        LSPDEFINELINE=i
    if logikLine.find("5004") == 0:
        LOUTDEFINELINE=i
        desc=re.sub('"','',LOGIKDEF.split("|")[(4+ANZIN+int(logikLine.split("|")[1]))])
        if logikLine.find("#*") >0:
            desc=logikLine.split("#*")[1]
        LOGIKOUTHTM+=addOutputDoku(logikLine.split("|")[1],logikLine.split("|")[4],logikLine.split("|")[2],desc)
    i=i+1


if livedebug:
    EC.append(0)
    EN.append("")


sendVars=""

for option in sys.argv:
    if option.find("--sa") == 0:
        SA[int(option[4:option.find("=")])]=option.split("=")[1]
        sendVars+="SA["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1]+"\n"
    if option.find("--sn") == 0:
        SN[int(option[4:option.find("=")])]=option.split("=")[1]
        SC[int(option[4:option.find("=")])]=True
        sendVars+="SN["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1]+"\n"
        sendVars+="SC["+str(int(option[4:option.find("=")]))+"]=1\n"
    if option.find("--aa") == 0:
        AA[int(option[4:option.find("=")])]=option.split("=")[1]
        sendVars+="AA["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1]+"\n"
    if option.find("--an") == 0:
        AN[int(option[4:option.find("=")])]=option.split("=")[1]
        AC[int(option[4:option.find("=")])]=True
        sendVars+="AN["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1:]+"\n"
        sendVars+="AC["+str(int(option[4:option.find("=")]))+"]=1\n"
    if option.find("--ea") == 0:
        EA[int(option[4:option.find("=")])]=option.split("=")[1]
        sendVars+="EA["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1:]+"\n"
    if option.find("--en") == 0:
        EN[int(option[4:option.find("=")])]="".join(option.split("=",1)[1])
        EC[int(option[4:option.find("=")])]=True
        sendVars+="EN["+str(int(option[4:option.find("=")]))+"]="+"".join(option.split("=")[1:])+"\n"
        sendVars+="EC["+str(int(option[4:option.find("=")]))+"]=1\n"
    if option.find("--ec") == 0:
#        EC[int(option[4:option.find("=")])]=int(option.split("=")[1])
        sendVars+="EC["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1]+"\n"
        print sendVars
    if option.find("--sc") == 0:
#        EC[int(option[4:option.find("=")])]=int(option.split("=")[1])
        sendVars+="SC["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1]+"\n"
        print sendVars
    if option.find("--on") == 0:
        ON[int(option[4:option.find("=")])]=option.split("=")[1]
        sendVars+="ON["+str(int(option[4:option.find("=")]))+"]="+option.split("=")[1]+"\n"
    if option.find("--oc") == 0:
        OC[int(option[4:option.find("=")])]=True
        sendVars+="OC["+str(int(option[4:option.find("=")]))+"]=1\n"
    if option.find("--ei") == 0:
        EI=(int(option.split("=")[1])==1)
        sendVars+="EI=1\n"
    if option.find("--run") == 0:
        sendVars+="eval(SN["+str(ANZSP+1)+"])\n"


def symbolize(LOGIK,code):
      symbols = {}
      for i in re.findall(r"(?m)^500([234])[|]([0-9]{1,}).*[@][@](.*)\s", LOGIK):
          varName=((i[0]=='2') and 'E') or ((i[0]=='3') and 'S') or ((i[0]=='4') and 'A')
          isunique=True
          try:
              type(symbols[i[2]])
              sym=i[2]
              isunique=False
          except KeyError:
              pass
          ## überprüft auch die alternativen Varianten
          if re.match("[ACN]",i[2][-1:]):
              try:
                  type(symbols[i[2][:-1]])
                  sym=i[2][:-1]
                  isunique=False
              except KeyError:
                  pass
          if isunique:
              symbols[i[2]]=[varName,"["+i[1]+"]"]
          else:
              print "Variablen Kollision :" +repr(i[2])+" ist in " +repr(symbols[sym]) + " und  "+ varName +"["+i[1]+"] vergeben"
              sys.exit(1)

      ## Symbole wieder entfernen
      LOGIK=re.sub("[@][@]\w+", "",LOGIK)

      #im Code tauschen
      for i in symbols.keys():
          code=[code[0],re.sub("[\@][\@]"+i+"([ACN])",symbols[i][0]+"\\1"+symbols[i][1],code[1]),re.sub("[\@][\@]"+i+"([ACN])",symbols[i][0]+"\\1"+symbols[i][1],code[2])]
          code=[code[0],re.sub("[\@][\@]"+i+"",symbols[i][0]+"N"+symbols[i][1],code[1]),re.sub("[\@][\@]"+i+"",symbols[i][0]+"N"+symbols[i][1],code[2])]
      return LOGIK,code

NCODE=[]
commentcode=[]
for codepart in code:
    NLOGIK,codepart=symbolize(LOGIK,codepart)

    NCODE.append(codepart)

    if codepart[0]==0 or codepart[0]==3:
        commentcode.append("##########################\n###### Quelltext: ########\n##########################"+"\n##".join(codepart[2].split("\n"))+"\n")
    #else:
    #    commentcode.append("#"+codepart[2].split("\n")[1]+"\n################################\n## Quelltext nicht Öffentlich ##\n################################")


NLOGIK,postlogik = symbolize(LOGIK,postlogik)
LOGIK=NLOGIK

code=NCODE

## Doku
doku = """
<html>
<head><title></title></head>
<link rel="stylesheet" href="style.css" type="text/css">
<body><div class="titel">"""+LOGIKNAME+"""</div>
<div class="nav"><A HREF="index.html">Hilfe</A> / <A HREF="logic.html">Logik</A> / """+LOGIKNAME+""" / <A HREF="#anker1">Eing&auml;nge</A> / <A HREF="#anker2">Ausg&auml;nge</A></div><div class="field0">Funktion</div>
<div class="field1">"""+re.sub("\r\n|\n","<br>",LOGIKDESC.decode("iso-8859-1").encode("ascii","xmlcharrefreplace") )+"""</div>
<div class="field0">Eing&#228;nge</div>
<a name="anker1" /><table border="1" width="612" class="log_e" cellpadding="0" cellspacing="0">
<COL WIDTH=203><COL WIDTH=132><COL WIDTH=275>
<tr><td>Eingang</td><td>Init</td><td>Beschreibung</td></tr>
"""+LOGIKINHTM.decode("iso-8859-1").encode("ascii","xmlcharrefreplace") +"""
</table>
<div class="field0">Ausg&#228;nge</div>
<a name="anker2" /><table border="1" width="612" class="log_a" cellpadding="0" cellspacing="0">
<COL WIDTH=203><COL WIDTH=132><COL WIDTH=275>
<tr><td>Ausgang</td><td>Init</td><td>Beschreibung</td></tr>
"""+LOGIKOUTHTM.decode("iso-8859-1").encode("ascii","xmlcharrefreplace") +"""
</table>
<div class="field0">Sonstiges</div>
<div class="field1">Neuberechnung beim Start: """+CALCSTART+"""<br />Baustein ist remanent: """+LOGIKREMANT+"""<br />Interne Bezeichnung: """+LOGIKID+"""<br />Der Baustein wird im "Experten" in der Kategorie '"""+LOGIKCAT+"""' einsortiert.<br /></div>
</body></html>

"""

if doDoku:
  open("log"+LOGIKID+".html",'w').write(doku)


LIVECODE="""
if EN["""+str(ANZIN+1)+"""].find("<id"""+LOGIKID+""">")!=-1:
    print "LivePort " +str(len(EN["""+str(ANZIN+1)+"""]))+ " Bytes erhalten"
    try:
        __LiveDebugCode_="".join(__import__('re').findall("(?i)<id"""+LOGIKID+""">(.*)</id"""+LOGIKID+""">",EN["""+str(ANZIN+1)+"""]))
        print "LiveDebug-Daten ID:"""+LOGIKID+" Name:"+LOGIKNAME+""" "
    except:
        pass
        print "Fehler Datenlesen"
        __LiveDebugCode_=''
    if __LiveDebugCode_.find("<inject>") != -1:
        SN["""+str(ANZSP+2)+"""]+="".join(__import__('re').findall("(?i)<inject>([A-Za-z0-9\\x2B\\x3D\\x2F]+?)</inject>", __LiveDebugCode_))
        print "Daten erhalten Buffer: " + str(len(SN["""+str(ANZSP+2)+"""]))
    elif  __LiveDebugCode_.find("<compile />") != -1:
        print "Compile"
        try:
            __LiveBase64Code_=__import__('base64').decodestring(SN["""+str(ANZSP+2)+"""])
            print __LiveBase64Code_
        except:
            pass
            print "Base64 Error"
            raise
        try:
            SN["""+str(ANZSP+1)+"""]=compile(__LiveBase64Code_,'<LiveDebug_"""+LOGIKID+""">','exec')
            SC["""+str(ANZSP+1)+"""]=1
            print "Running"
        except:
            pass
            SN["""+str(ANZSP+1)+"""]="0"
            SC["""+str(ANZSP+1)+"""]=1
            print "Compile Error"

        SN["""+str(ANZSP+2)+"""]=''
    elif __LiveDebugCode_.find("<vars>") == 0:
        print "Run Script"
        try:
            __LiveBase64Code_=__import__('base64').decodestring("".join(__import__('re').findall("(?i)<vars>([A-Za-z0-9\\x2B\\x3D\\x2F]+?)</vars>", __LiveDebugCode_)))
        except:
            pass
            print "Script Base64 Error"
            __LiveBase64Code_='0'
        try:
            eval(compile(__LiveBase64Code_,'<LiveDebugVars"""+LOGIKID+""">','exec'))
        except:
            print "Script Error" 
            print __LiveBase64Code_
            print  __import__('traceback').print_exception(__import__('sys').exc_info()[0],__import__('sys').exc_info()[1],__import__('sys').exc_info()[2])
            raise
    else:
        print "unbekanntes TAG: " + repr(__LiveDebugCode_)
"""




#print LIVECODE

LOGIKFILE=LOGIKID+"_"+LOGIKNAME

## Debug Lines
NCODE=[]
if debug or livedebug:
    for codepart in code:
        codepart[2]=re.sub("###DEBUG###","",codepart[2])
        NCODE.append(codepart)
    code=NCODE

#print "\n".join(code)
def commentRemover(code):
    ## Komentar Remover 
    ## thanks to gaston
    codelist=code[2].split("\n")
    removelist=[]
    lencode=len(codelist)-1
    for i in range(1,lencode):
        codeline=codelist[lencode-i].lstrip(" \t")
        if len(codeline)>0:
            if codeline[0]=='#':
                removelist.insert(0,"REMOVED: ("+str(lencode-i)+") "+codelist.pop(lencode-i))
        else:
            codelist.pop(lencode-i)
    return ([code[0],code[1],"\n".join(codelist)],"\n".join(removelist))

Nremoved=""
NCode=[]
for codepart in code:
    codepart, removed=commentRemover(codepart)
    Nremoved=Nremoved+removed
    NCode.append(codepart)

code=NCode

#print Nremoved
#print "\n\n"


#print code

if livedebug:
    NCODE="\n##### VERSION #### %04d-%02d-%02d %02d:%02d:%02d ###\n" % time.localtime()[:6]
    code.append(NCODE)

CODELENGTH=len(repr(code))



breakStart=str((int(CALCSTARTBOOL)-1)*-1)
LOGIKARRAY=LOGIK.split("\n")
lformel=""
def compileMe(code,doByteCode,BEDINGUNG=''):
    if doByteCode:
        data=compile(code,"<"+LOGIKFILE+">","exec")
        data=marshal.dumps(data)
        version = sys.version[:3]
        formel = ""
        if doByteCode==2:
            formel += "5012|0|\""+BEDINGUNG+"\"|\"eval(__import__('marshal').loads(__import__('zlib').decompress(__import__('base64').decodestring('"+re.sub("\n","",base64.encodestring(zlib.compress(data,6)))+"'))))\"|\""+ZEITFORMEL+"\"|0|"+ZEITSPEICHER+"|0|0"
        else:
            formel += "5012|0|\""+BEDINGUNG+"\"|\"eval(__import__('marshal').loads(__import__('base64').decodestring('"+re.sub("\n","",base64.encodestring(data))+"')))\"|\""+ZEITFORMEL+"\"|0|"+ZEITSPEICHER+"|0|0"
        formel+="\n"

    else:
        if doCache:
            LOGIKDEFARRAY=LOGIKARRAY[LHSDEFINELINE].split("|")
            if livedebug:
                LOGIKDEFARRAY[4]=str(ANZSP+2)
            else:
                LOGIKDEFARRAY[4]=str(ANZSP+1)
            LOGIKARRAY[LHSDEFINELINE]="|".join(LOGIKDEFARRAY)
            LOGIKARRAY[LSPDEFINELINE]+="\n"+"5003|"+str(ANZSP+1)+"|\"0\"|0 # Base64 Code-Cache"
            if livedebug:
                LOGIKARRAY[LSPDEFINELINE]+="\n"+"5003|"+str(ANZSP+2)+"|\"\"|0 # LivePortBase64Buffer"
            if livedebug:
                formel = "5012|0|\"EI or EC["+str(ANZIN+1)+"]\"|\"eval(compile(__import__('base64').decodestring('"+re.sub("\n","",base64.encodestring(LIVECODE))+"'),'<"+LOGIKFILE+">','exec'))\"|\"\"|0|0|0|0\n"
                #formel += "5012|0|\"("+BEDINGUNG+") or SC["+str(ANZSP+1)+"]\"|\"eval(SN["+str(ANZSP+1)+"])\"|\""+ZEITFORMEL+"\"|0|"+ZEITSPEICHER+"|0|0"
                formel += "5012|0|\"\"|\"eval(SN["+str(ANZSP+1)+"])\"|\""+ZEITFORMEL+"\"|0|"+ZEITSPEICHER+"|0|0"
            else:
                formel = "5012|0|\"EI\"|\"compile(__import__('base64').decodestring('"+re.sub("\n","",base64.encodestring(code))+"'),'<"+LOGIKFILE+">','exec')\"|\"\"|0|0|"+str(ANZSP+1)+"|0\n"
                formel += "5012|0|\""+BEDINGUNG+"\"|\"eval(SN["+str(ANZSP+1)+"])\"|\""+ZEITFORMEL+"\"|0|"+ZEITSPEICHER+"|0|0"
        else:
            formel = "5012|0|\""+BEDINGUNG+"\"|\"eval(compile(__import__('base64').decodestring('"+re.sub("\n","",base64.encodestring(code))+"'),'<"+LOGIKFILE+">','exec'))\"|\""+ZEITFORMEL+"\"|0|"+ZEITSPEICHER+"|0|0"
    #formel+="\n## MD5 der Formelzeile: "+md5.new(formel).hexdigest()
    return formel

formel=""
for i in range(len(code)):
    codepart=code[i]
    if codepart[0]==1:
        tempBC=1
    if codepart[0]==2:
        tempBC=2
    else:
        tempBC=doByteCode
    if livedebug:
        doCache=True
        formel=compileMe(LIVECODE,False,BEDINGUNG="")
        break
    formel+=compileMe(codepart[2],tempBC,BEDINGUNG=codepart[1])
    #formel+=commentcode[i]+"\n\n"
        
### DEBUG ###

formel+="\n"+postlogik[2]

## Debuggerbaustein

if livedebug:
    LOGIKDEFARRAY=LOGIKARRAY[LEXPDEFINELINE].split("|")
    LOGIKDEFARRAY[3]=str(ANZIN+1)
    LOGIKDEFARRAY[3+ANZIN]+="|\"E"+str(ANZIN+1)+" DEBUG\""
    LOGIKARRAY[LEXPDEFINELINE]="|".join(LOGIKDEFARRAY)
    LOGIKDEFARRAY=LOGIKARRAY[LHSDEFINELINE].split("|")
    LOGIKDEFARRAY[1]=str(ANZIN+1)
    LOGIKARRAY[LHSDEFINELINE]="|".join(LOGIKDEFARRAY)
    LOGIKARRAY[LINDEFINELINE]+="\n"+"5002|"+str(ANZIN+1)+"|\"\"|1 # Debugger Live in"


LOGIK = "\n".join(LOGIKARRAY)

allcode=""
for i in code:
  allcode+=i[2]+"\n"

if showList:
    codeobj=allcode.split("\n")
    for i in range(0,len(codeobj)):
        print str(i)+": "+codeobj[i]

if debug and not livedebug:
    debugstart=time.clock()
    allcode += debugcode
    if not noexec:
        exec(allcode)
    else:
        compile(allcode,"<code>","exec")

    debugtime=time.clock()-debugstart
    print "Logikausfuehrzeit: %.4f ms" % (debugtime)
    if debugtime>1:
      print """
###############################################
### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ###
### !!!ACHTUNG: sehr lange Ausfürungszeit!! ###
### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ###
###############################################
"""

if debug or doSend:
    del EN[0]
    del SN[0]
    del AN[0]

if livedebug:
    #formel=lformel
    LOGIK="""############################\n####  DEBUG BAUSTEIN #######\n############################\n"""+LOGIK
    livesend=re.sub("\n","",base64.encodestring(allcode))
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.connect((livehost,liveport))
    Livepackets=0
    while livesend!="":
        Livepackets+=1
        sock.sendall("<xml><id"+LOGIKID+"><inject>"+livesend[:4000]+"</inject></id"+LOGIKID+"></xml>")
        livesend=livesend[4000:]
        time.sleep(0.1)
    time.sleep(1)
    sock.sendall("<xml><id"+LOGIKID+"><compile /></id"+LOGIKID+"></xml>")
    print str(Livepackets)+ " Packet per UDP verschickt"
    sock.close()

if doSend:
    ## Das auslösen über den Debug verhindern
    sendVars="EC["+str(ANZIN+1)+"]=0\n"+sendVars
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.connect((livehost,liveport))
    sock.sendall("<xml><id"+LOGIKID+"><vars>"+re.sub("\n","",base64.encodestring(sendVars)+"</vars></id"+LOGIKID+"></xml>\n"))
    sock.close()


if VERSION !="":
    VERSION="_"+VERSION
if debug:
    VERSION+="_DEBUG"


open(LOGIKFILE+VERSION+".hsl",'w').write(LOGIK+"\n"+formel+"\n")
def md5sum(fn):
    m = md5()
    f=open(fn,'rb')
    while True: 
        data = f.read(1024) 
        if not data: 
            break 
        m.update(data) 
    f.close()
    return m.hexdigest() + " *" + fn + "\n"
    
#chksums = md5sum(LOGIKFILE+VERSION+".hsl")
#if not nosource:
#    chksums += md5sum(inspect.currentframe().f_code.co_filename)
#if doDoku:
#    chksums += md5sum("log"+LOGIKID+".html")
#
#open(LOGIKFILE+".md5",'w').write(chksums)

if doZip:
    #os.remove(LOGIKFILE+VERSION+".zip")
    z=zipfile.ZipFile(LOGIKFILE+VERSION+".zip" ,"w",zipfile.ZIP_DEFLATED)
    if not nosource:
        z.write(inspect.currentframe().f_code.co_filename)
    if doDoku:
        z.write("log"+LOGIKID+".html")
    z.write(LOGIKFILE+VERSION+".hsl")
#    z.write(LOGIKFILE+".md5")
    z.close()

print "Baustein \"" + LOGIKFILE + "\" erstellt"
print "Groesse:" +str(CODELENGTH)

if livedebug:
    print "########################################"
    print "####       DEBUGBAUSTEIN            ####"
    print "########################################"

print """
Neuberechnung beim Start: """+CALCSTART+"""
Baustein ist remanent: """+LOGIKREMANT+"""
Interne Bezeichnung: """+LOGIKID+"""
Kategorie: '"""+LOGIKCAT+"""'
Anzahl Eingänge: """+str(ANZIN)+"""   """+repr(EN)+"""
Anzahl Ausgänge: """+str(ANZOUT)+"""  """+repr(AN)+"""
Interne Speicher: """+str(ANZSP)+"""  """+repr(SN)+"""
"""

#print chksums
