import struct
from hartcommand import *
from pprint import pprint

Length = {'Total':8,'VerLen':1,'MesTypeLen':1,'MesIDLen':1,'StatusCodeLen':1,'SeqNumLen':2,'ByteCountLen':2}

Version = 1

MessageType = {'Request':0,'Response':1,'Pub_Noti':12,'Nak':15}

MessageID   = {'SessionInitiate':0,'SesstionClose':1,'KeepAlive':2,'TPPDU':3,'Discovery':128}

StatusCode = ''

SequenceNumber = ''

ByteCount = ''


def ReceiveFromSocket(data,client):
    #Calculate the data length from the socket received
    RecLength = len(data)    
    
    RecFmt = str(RecLength)+'B' 
    pprint(struct.unpack(RecFmt,data))
         
    Header = ProcessHeader(data[0:8])
    if Header['Status'] == True:        
        MesHeader =  Header['RecHeader']          
        if MesHeader['RecMesType'] == 0:                                 #Request
            
            if MesHeader['RecMesID'] == 0:     #Session Initiate  
                pprint('Session initiate')
                SessionReq = {'MasterType':'','InactivityCloseTime':''}
                ResData =''
                
                RC = 0
                if MesHeader['RecVersion'] != Version:
                    RC = 14
                if MesHeader['RecByteCount'] < 13:
                    RC = 6
                else:
                    SessionReq['MasterType']            = struct.unpack('B',data[8])[0]
                    SessionReq['InactivityCloseTime']   = struct.unpack('!I',data[9:13])[0]   #Milliseconeds     
                    if SessionReq['MasterType'] != 1:
                        RC = 2                    
                    if SessionReq['InactivityCloseTime'] <= 100000:
                        SessionReq['InactivityCloseTime'] = 100000
                        RC = 8
                    client.settimeout(SessionReq['InactivityCloseTime']/1000)
                    pprint('session timeout is: %d'%SessionReq['InactivityCloseTime'])
                    
                    #response to initiate 
                    if RC==0:
                        ResData += struct.pack('B',SessionReq['MasterType'])
                        ResData += struct.pack('!I',SessionReq['InactivityCloseTime'])
                client.send(ResponseToRequest(Version,0,RC,MesHeader['RecSecNum'],ResData))              
            
            elif MesHeader['RecMesID'] == 1:   #Session Close
                pprint('Session Close')
            
            elif MesHeader['RecMesID'] == 2:   #Keep Alive
                pprint('Keep Alive')
                client.send(ResponseToRequest(Version,2,0,MesHeader['RecSecNum'],'')) 
           
            elif MesHeader['RecMesID'] == 3:   #Token-Passing PDU
                pprint('Token-Passing PDU')
                TPLength = MesHeader['RecByteCount'] - 8
                try:
                    RC,resBinary = ProcessTPPDURequest(data[8:RecLength],client)
                except Exception as e:
                    RC = False
                if RC == True:
                    client.send(ResponseToRequest(Version,3,0,MesHeader['RecSecNum'],resBinary))              
                
            elif MesHeader['RecMesID'] == 128: #Discovery
                pprint('Discovery')
            
            else:                              #Error occur
                pprint('err message type : %s' % MesHeader['RecMesID'])
              
      
        elif MesHeader['RecMesType'] == 1:                               #Response
            pass
        elif MesHeader['RecMesType'] == 2:                               #Publish/Notification
            pass
        elif MesHeader['RecMesType'] == 15:                              #NAK
            pass
        else:                                                            #Error occur
            pprint('err message type : %s' % MesHeader['RecMesType'])
        
    
        
def ProcessHeader(data):
    RecHeader = {'RecVersion':'','RecMesType':'','RecMesID':'','RecStatusCode':'','RecSecNum':'','RecByteCount':''}
    Res = {'Status':'False','RecHeader':RecHeader}

    if len(data) != 8:
        return Res
    
    try:
        RecHeader['RecVersion']    = struct.unpack('B',data[0])[0]
        RecHeader['RecMesType']    = struct.unpack('B',data[1])[0]
        RecHeader['RecMesID']      = struct.unpack('B',data[2])[0]
        RecHeader['RecStatusCode'] = struct.unpack('B',data[3])[0]
        RecHeader['RecSecNum']     = struct.unpack('!H',data[4:6])[0]
        RecHeader['RecByteCount']  = struct.unpack('!H',data[6:8])[0] 
        Res['Status'] = True
    except Exception as E:
        pprint(E)
    
    return Res

def ResponseToRequest(ver,MesID,Status,SeqNum,data):
    return AssemblePacket(ver, MessageType['Response'], MesID, Status, SeqNum, data)
    
def AssemblePacket(ver,Mestype,MesID,Status,SeqNum,data):
    frame = ''
    length = 8
    newdata = []
    datalength = len(data)
    length += datalength
    
    try:    
        frame+=struct.pack('B',ver)
        frame+=struct.pack('B',Mestype)
        frame+=struct.pack('B',MesID)
        frame+=struct.pack('B',Status)
        frame+=struct.pack('!H',SeqNum)
        frame+=struct.pack('!H',length)
        frame+=data
    except Exception as e:
        pprint(e)
    
    return frame


def ProcessTPPDURequest(data,client):
    datalist = list(struct.unpack(str(len(data))+'B',data))
    recCheck = datalist.pop()
    if recCheck == CheckSum(datalist):
        Delimiter = datalist[0]
        if Delimiter == 0x02:                                   #Polling Request
            
            cmdres = CommandRequest_0()
            cmd0 = [0]
            res = cmd0 + cmdres
            resDelimiter = 0x06
            addr = [128]
            resList = [resDelimiter] + addr + res
            resList.append(CheckSum(resList))
            return True,ListToBinary(resList)
        elif Delimiter == 0x82:                                 #Long Address Request
            addr = struct.unpack('!5B',data[1:6])
            if addr == Device['Address']:
                recCmdID = datalist[6]
                recCmdLength = datalist[7]                
                try:
                    if HARTCommandRequestFunction.has_key(str(recCmdID)):
                        pprint('Command %s' % recCmdID)
                        if recCmdLength == 0:
                            resCommand = HARTCommandRequestFunction[str(recCmdID)]()                   
                        else:
                            resCommand = HARTCommandRequestFunction[str(recCmdID)](datalist[7:])
                    else:
                        pprint('No this command %s' % recCmdID)
                        resCommand = [64]   # Response Code, No payloads
                except Exception as e:
                    resCommand = [64]   # problem occur
                
                res = [recCmdID] + resCommand
                    
                resDelimiter = 0x86
                addr = [166,78,0,0,240]
                resList = [resDelimiter] + addr + res
                resList.append(CheckSum(resList))
                return True,ListToBinary(resList)        
            else:
                pprint('Delimiter is error')
                return 
        else:   #checksum is error
            pprint('checksum is error')
            return
    else:
        pprint('wrong request was received %s' % Delimiter)
        return 
    
def ListToBinary(InputList):
    str = ''
    for i in range(len(InputList)):
        str += struct.pack('B',InputList[i])        
    return str

def CheckSum(InputList):
    Check = InputList[0]
    for i in range(1,len(InputList)):
        Check ^= InputList[i]
        
    return Check
