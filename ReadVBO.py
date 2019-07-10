import numpy as np
import VectorMath

class VBOReader:
    
    headerTag='[header]'
    channelUnitTag='[channel units]'
    commentsTag='[comments]'
    aviTag= '[AVI]'
    laptimingTag= '[laptiming]'
    columnNamesTag= '[column names]'
    dataTag='[data]'

    headers=[]
    channelUnits=[]
    comments= []
    avi= []
    laptiming=[]
    columnNames=[]
    data=[]
    Laps=[]
    
    def __init__(self, fileLocation,runsheet=None,fueladded=0.0,tyres="",comments="",tyrepressures={}):
        super().__init__()
        self.fileName = fileLocation.split("\\")[-1]
        if(".vbo" in self.fileName):
            self.file = open(fileLocation,"r")
            self.lines = [line.rstrip('\n') for line in self.file]
            
        self.runsheet = runsheet
        if self.runsheet == None:
            self.runsheet = runSheet()
        self.fuelAdded = fueladded
        self.tyres = tyres
        self.usercomments = comments
        self.tyrepressures = tyrepressures
    def setup(self):
        self.getDateFromFile()

        self.headers = self.getTagFromFile(self.headerTag)
        self.channelUnits = self.getTagFromFile(self.channelUnitTag)
        self.comments = self.getTagFromFile(self.commentsTag)
        self.avi = self.getTagFromFile(self.aviTag)
        self.laptiming = self.getTagFromFile(self.laptimingTag)
        self.columnNames = self.getTagFromFile(self.columnNamesTag)
        self.data = self.getTagFromFile(self.dataTag)

        self.data = [x.split(" ") for x in self.data]
                
        self.laptiming = [VBOReader.splitLaptimes(x)  for x in self.laptiming]
        
        self.minFuel        = self.getMinFromColumn("PURE_FuelConsumed")
        self.maxFuel        = self.getMaxFromColumn("PURE_FuelConsumed")
        self.fuelConsumed   = self.maxFuel - self.minFuel
        self.minOdo         = self.getMinFromColumn("lPART1Totalizer")
        self.maxOdo         = self.getMaxFromColumn("lPART1Totalizer")
        self.totalOdo       =  self.maxOdo - self.minOdo
        self.LperKM         = 0.0
        if(not self.totalOdo == 0 ):
            self.LperKM = self.fuelConsumed/self.totalOdo
        self.maxTCoolant =  self.getMaxFromColumn("TCoolant")
        self.maxTAirCharge = self.getMaxFromColumn("TAirCharge")
        self.maxToil = self.getMaxFromColumn("TOil")
        self.maxTClutch = self.getMaxFromColumn("TClutchOil")
        self.Vmax = self.getMaxFromColumn("velocity kmh")
        self.maxTAmbient = self.getMaxFromColumn("TAmbientRaw")

        self.MeanTCoolant =  self.getMeanFromColumn("TCoolant")
        self.MeanTAirCharge = self.getMeanFromColumn("TAirCharge")
        self.MeanToil = self.getMeanFromColumn("TOil")
        self.MeanTClutch = self.getMeanFromColumn("TClutchOil")
        self.VMean = self.getMeanFromColumn("velocity kmh")
        self.MeanTAmbient = self.getMeanFromColumn("TAmbientRaw")
        self.MeanPAmbient = self.getMeanFromColumn("pAmbient")  

        self.createLapsFromData()
        newRun = run()
        newRun.setValues(self.Laps,float(self.minFuel       )
                                    ,float(self.maxFuel       )
                                    ,float(self.fuelConsumed  )
                                    ,float(self.minOdo        )
                                    ,float(self.maxOdo        )
                                    ,float(self.totalOdo      )
                                    ,float(self.LperKM        )
                                    ,float(self.maxTCoolant   )
                                    ,float(self.maxTAirCharge )
                                    ,float(self.maxToil       )
                                    ,float(self.maxTClutch    )
                                    ,float(self.Vmax          )
                                    ,float(self.maxTAmbient   )
                                    ,float(self.MeanTCoolant  )
                                    ,float(self.MeanTAirCharge)
                                    ,float(self.MeanToil      )
                                    ,float(self.MeanTClutch   )
                                    ,float(self.VMean         )
                                    ,float(self.MeanTAmbient  )
                                    ,float(self.MeanPAmbient  )
                                    ,float(self.fuelAdded)
                                    ,self.tyres
                                    ,self.usercomments
                                    ,len(self.data)
                                    ,self.tyrepressures)
        self.runsheet.appendRun(newRun)

    def getDateFromFile(self):
        splitStringArray = self.lines[0].rsplit('@ ')
        self.creationTime = splitStringArray[1]
        dateString = str(splitStringArray[0])
        self.creationDate = dateString.rsplit('on ')[1]
        self.creationDate = str(self.creationDate).strip()

    @staticmethod
    def splitLaptimes(laptime):
        tabSplit = laptime[0:13].strip()
        times = laptime[13:len(laptime)].split()
        coords = np.array(times[0:4]).astype(float)
        #spaceSplit= tabSplit[].split()
        return tabSplit,coords

    def createLapsFromData(self):
        self.lapcount = 0
        latitudeIndex = self.headers.index("latitude")
        longtitudeIndex = self.headers.index("longitude")
        timeIndex = self.headers.index("time")

        var1 = np.array(self.laptiming)
        finishStartindex= var1[np.where(var1[:,0] == "Start finish")]
        startfinish= finishStartindex[0:,1]
        #startfinish = self.laptiming[startfinishIndex][1]

        lapY1 = startfinish[0][0]
        lapX1 = startfinish[0][1]
        lapY2 = startfinish[0][2]
        lapX2 = startfinish[0][3]

        S1 = np.array([lapX1,lapY1])
        S2 = np.array([lapX2,lapY2])
        P1= [float(self.data[0][longtitudeIndex]),float(self.data[0][latitudeIndex])]
        P1Time= float(self.data[0][timeIndex])
        P2Time = 0.0
        TotalCount= 0
        lapCount = 0
        SumDeltaTime= 0.0
        count2=100
        
        coords = np.array(self.data)[:,[timeIndex,longtitudeIndex,latitudeIndex]].astype(float)
        for x in coords:
            TotalCount=TotalCount+1
            lapCount= lapCount+1
            count2= count2 +1
            P2Time = x[0]
            pTimeDelta =(P2Time - P1Time)
            SumDeltaTime = SumDeltaTime + (P2Time - P1Time)
            P1Time = P2Time
            y1 = x[1]
            x1 = x[2]
            P2 = np.array([x1,y1])
            #if( (P1[0] != P2[0] or  P1[1] != P2[1] ) and count2 >50):
            vMath = VectorMath.vMath(S1,S2,P1,P2)
            
            if(vMath.doIntersect() and count2 >= 100):
                count2 = 0
                time = (lapCount-1)*0.1 + (0.1 * vMath.PreIntersectionWeight )
                lapCount=0
                #vMath.printMe()
                #if(pTimeDelta > 0.2):
                self.lapcount = self.lapcount+1
                self.Laps.append([self.lapcount ,str(time)+"s",time] )
                SumDeltaTime=0.0
                
                
            P1 = np.array([x1,y1])

    def getTagFromFile(self, tag):
        
        locallist= self.lines.copy()
        try:
            tagIndex = self.lines.index(tag)
        
            try:
                tagStopIndex = locallist.index('',tagIndex)
            except:
                tagStopIndex = locallist.__len__()
            
            return locallist[tagIndex+1:tagStopIndex].copy()
        except:
            return []
       
    def getMeanFromColumn(self,_tag):
        
        arr = np.array(self.data)

        tagIndex = self.headers.index(_tag)

        copy = np.copy(arr[:,tagIndex])
        asFloatCopy = copy.astype(float)

        return np.mean(asFloatCopy)

    def getMinFromColumn(self,_tag):
        
        arr = np.array(self.data)

        tagIndex = self.headers.index(_tag)

        copy = np.copy(arr[:,tagIndex])
        asFloatCopy = copy.astype(float)

        return np.min(asFloatCopy)

    def getMaxFromColumn(self,_tag):
        
        arr = np.array(self.data)

        tagIndex = self.headers.index(_tag)

        copy = np.copy(arr[:,tagIndex])
        asFloatCopy = copy.astype(float)

        return np.max(asFloatCopy)
    def getSumFromColumn(self,_tag):
        
        arr = np.array(self.data)

        tagIndex = self.headers.index(_tag)

        copy = np.copy(arr[:,tagIndex])
        asFloatCopy = copy.astype(float)

        return np.sum(asFloatCopy)

    def __str__(self):
        print(super().__str__())
        
        print(self.creationDate)
        print(self.creationTime)
        #print(self.file.name())
        print( self.headerTag)
        print(self.headers.__str__())
        print( self.channelUnitTag)
        print(self.channelUnits.__str__())
        print( self.commentsTag)
        print(self.comments.__str__())
        print( self.aviTag)
        print(self.avi.__str__())
        print( self.laptimingTag)
        print(self.laptiming.__str__())
        print( self.columnNamesTag)
        print(self.columnNames.__str__())
        print( self.dataTag)
        print("records: "+ str(self.data.__len__()))
        print(self.lapcount)

        print( "laps " + str(self.lapcount))
        print(self.Laps)
        print("\n\n")
        print(  "sumFuelConsumed : "  + str(self.sumFuelConsumed) )    
        print(  "minFuel : "  + str(self.minFuel        ) )   
        print(  "maxFuel : "  + str(self.maxFuel        ) )  
        print(  "fuelConsumed : "  + str(self.fuelConsumed   ) )  
        print(  "minOdo : "  + str(self.minOdo         ) )  
        print(  "maxOdo : "  + str(self.maxOdo         ) )  
        print(  "totalOdo : "  + str(self.totalOdo       ) )   
        print(  "LperKM : "  + str(self.LperKM         ) )
        
        print(  "maxTCoolant : "  + str(self.maxTCoolant    ) )
        print(  "maxTAirCharge : "  + str(self.maxTAirCharge  ) )
        print(  "maxToil : "  + str(self.maxToil        ) )
        print(  "maxTClutch : "  + str(self.maxTClutch     ) )
        print(  "Vmax : "  + str(self.Vmax           ) )
        print(  "maxTAmbient : "  + str(self.maxTAmbient    ) )
        
        print(  "MeanTCoolant : "  + str(self.MeanTCoolant   ) )
        print(  "MeanTAirCharge : "  + str(self.MeanTAirCharge ) )
        print(  "MeanToil : "  + str(self.MeanToil       ) )
        print(  "MeanTClutch : "  + str(self.MeanTClutch    ) )
        print(  "VMean : "  + str(self.VMean          ) )
        print(  "MeanTAmbient : "  + str(self.MeanTAmbient   ) )
        print(  "MeanPAmbient : "  + str(self.MeanPAmbient   ) )

        return ""
class runSheet(object):
    runs = []
    Sheettotals = None
    def __init__(self):
        self.runs = []
        self.Sheettotals = Sheettotals()
        return super().__init__()
    def appendRun(self,run):
        run.setid(len(self.runs))
        self.runs.append(run)
        self.Sheettotals.appendsheettotals(run)
class run(object):
    def __init__(self):
        
        self.minFuel        =0.0
        self.maxFuel        =0.0
        self.lapcount = 0
        self.fuelConsumed   =0.0
        self.minOdo         =0.0
        self.maxOdo         =0.0
        self.totalOdo       =0.0
        self.LperKM         =0.0
        self.maxTCoolant    =0.0
        self.maxTAirCharge  =0.0
        self.maxToil        =0.0
        self.maxTClutch     =0.0
        self.Vmax           =0.0
        self.maxTAmbient    =0.0
        self.MeanTCoolant   =0.0
        self.MeanTAirCharge =0.0
        self.MeanToil       =0.0
        self.MeanTClutch    =0.0
        self.VMean          =0.0
        self.MeanTAmbient   =0.0
        self.MeanPAmbient   =0.0
        self.currentFuel =0.0
        self.avgLap = 0.0
        self.fastestLap = 0.0
        self.tyrepressures ={}
        #manual
        self.fuelAdded = 0.0
        self.tyres =""
        self.comments = ""
        self.laps = []
        self.datapoints = 0
        
        return super().__init__()
    def setValues(self,laps,minFuel,maxFuel,fuelConsumed,minOdo,maxOdo,totalOdo,LperKM,maxTCoolant,maxTAirCharge,maxToil,maxTClutch,Vmax           
                                                ,maxTAmbient    
                                                ,MeanTCoolant   
                                                ,MeanTAirCharge 
                                                ,MeanToil       
                                                ,MeanTClutch    
                                                ,VMean          
                                                ,MeanTAmbient   
                                                ,MeanPAmbient
                                                ,fueladded
                                                , tyres 
                                                ,comments
                                                ,datapoints
                                                ,tyrepressures  ):
        self.laps = laps
        self.lapcount= len(laps)
        nplaps = np.array(laps)
        self.tyres          = tyres
        npLaptimes = np.copy(nplaps[:,2]).astype(float) 
        self.avgLap         = float(np.mean(npLaptimes)) 
        self.fastestLap     = float(np.min(npLaptimes))
        self.minFuel        = minFuel       
        self.maxFuel        = maxFuel       
        self.fuelConsumed   = fuelConsumed  
        self.minOdo         = minOdo        
        self.maxOdo         = maxOdo        
        self.totalOdo       = totalOdo      
        self.LperKM         = LperKM        
        self.maxTCoolant    = maxTCoolant   
        self.maxTAirCharge  = maxTAirCharge 
        self.maxToil        = maxToil       
        self.maxTClutch     = maxTClutch    
        self.Vmax           = Vmax          
        self.maxTAmbient    = maxTAmbient   
        self.MeanTCoolant   = MeanTCoolant  
        self.MeanTAirCharge = MeanTAirCharge
        self.MeanToil       = MeanToil      
        self.MeanTClutch    = MeanTClutch   
        self.VMean          = VMean         
        self.MeanTAmbient   = MeanTAmbient  
        self.MeanPAmbient   = MeanPAmbient  
        self.fuelAdded = fueladded
        self.tyres = tyres
        self.comments = comments
        self.curFuel = self.fuelAdded - self.fuelConsumed
        self.datapoints= datapoints
        self.tyrepressures =tyrepressures
    def setid(self,id):
        self.id=id+1
class Sheettotals(object):
    
    totalOdo = 0.0
    totalperTyre ={}
    totalLaps = 0
    avgLap = 0.0
    fastestLap = 0.0
    
    totalFuelUsed=0.0
    constLperlap =0.0
    constLperkm=0.0
    TCoolantMax =0.0
    TAirchargeMax=0.0
    TOilMax=0.0
    TclutchMax = 0.0
    TCoolantAvg =0.0
    TAirchargeAvg=0.0
    TOilAvg       =0.0
    TclutchAvg      =0.0 
    totaldatapoints      = 0
    def __init__(self):
        self.runs = 0
        self.totalOdo = 0.0
        self.totalLaps = 0
        self.avgLap = 0.0
        self.fastestLap = 0.0
        self.totalperTyre = {}
        self.totalFuelUsed = 0.0
        self.constLperlap = 0.0
        self.constLperkm=0.0
        self.TCoolantMax = 0.0
        self.TAirchargeMax = 0.0
        self.TOilMax=0.0
        self.TclutchMax = 0.0
        self.TCoolantAvg = 0.0
        self.TAirchargeAvg = 0.0
        self.TOilAvg=0.0
        self.TclutchAvg = 0.0
        self.totaldatapoints= 0
        self.vmax =0.0 
        return super().__init__()
    def appendsheettotals(self,_run = run()):
        
        self.totaldatapoints = self.totaldatapoints + _run.datapoints

        self.runs = self.runs+1
        self.totalOdo =self.totalOdo+ _run.totalOdo 
        self.totalLaps = self.totalLaps+ _run.lapcount
        self.avgLap = (self.avgLap + _run.avgLap)/2
        if(float(self.fastestLap) > float(_run.fastestLap)):
            self.fastestLap = _run.FastestLap
        self.appendTyreOdo(_run.tyres,_run.totalOdo)
        self.totalFuelUsed = self.totalFuelUsed + _run.fuelConsumed
        self.constLperlap = self.totalFuelUsed/self.totalLaps
        self.constLperkm= self.totalFuelUsed/self.totalOdo
        if self.TCoolantMax < _run.maxTCoolant:
            self.TCoolantMax = _run.maxTCoolant
        if self.TAirchargeMax < _run.maxTAirCharge:
            self.TAirchargeMax = _run.maxTAirCharge
        if self.TOilMax < _run.maxToil:
            self.TOilMax=_run.maxToil
        if self.TclutchMax < _run.maxTClutch:
            self.TclutchMax =  _run.maxTClutch
        self.TCoolantAvg = ((self.TCoolantAvg*(self.totaldatapoints-_run.datapoints) + _run.MeanTCoolant*_run.datapoints)/self.totaldatapoints)
        self.TAirchargeAvg = ((self.TAirchargeAvg*(self.totaldatapoints-_run.datapoints) + _run.MeanTAirCharge*_run.datapoints)/self.totaldatapoints)
        self.TOilAvg=((self.TOilAvg*(self.totaldatapoints-_run.datapoints) + _run.MeanToil*_run.datapoints)/self.totaldatapoints)
        self.TclutchAvg = ((self.TclutchAvg*(self.totaldatapoints-_run.datapoints) + _run.MeanTClutch*_run.datapoints)/self.totaldatapoints)
    def appendTyreOdo(self, tyre, totalOdo):
        
        if tyre in self.totalperTyre:
            self.totalperTyre[tyre] =self.totalperTyre[tyre]+totalOdo
        else:
            self.totalperTyre[tyre]= totalOdo
        
def main():
    vboReader = VBOReader("#118_2019_04_04_132304_0001.vbo")
    vboReader.setup()


