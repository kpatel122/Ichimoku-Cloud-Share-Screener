import urllib.request, json
import urllib
from datetime import datetime, timedelta
import xlrd
import time
import sys
from ShareAnalysis import IchimokuCloud
API_ALPHA = ""
 

ALL_SYMBOLS = 1 #excel coloumn references
SUBSET_SYMBOLS = 3
DELAY = 10 #api delay


class SymbolMetaData:
    def __init__(self):
        self.information = ""
        self.symbol = ""
        self.lastrefreshed = ""
        self.timezone = ""

        self.tekanSanDelta = 0.0
        
class TimeSeries:
    def __init__(self):
        self.timeSeries = ""
        self.open=0.0
        self.high=0.0
        self.low=0.0
        self.close=0.0
        self.volume=0
            
class Symbol:
    def __init__(self):
        self.metadata = SymbolMetaData()
        self.timeSeriesEntries = []
    

def getKey(symbol):
    return symbol.metadata.tekanSanDelta
    #return symbol.timeSeriesEntries[0].close

def SymbolAnalysis(Symbol):
    #print(Symbol.metadata.symbol)
    symbolName = Symbol.metadata.symbol
    
    ic=IchimokuCloud()
    ic.Calculate(Symbol)
    Symbol.metadata.tekanSanDelta = ic.CalculateTekanSanDelta(Symbol)
    if(ic.IsBear(Symbol)==True):
        return symbolName
    else:
        return ""


def CreateTimeSeriesSymbolsFromAlphaVantage(SymbolName,Function="TIME_SERIES_DAILY",Interval=""):
    if(Interval!=""):
        urlString = "https://www.alphavantage.co/query?function="+Function+"&Outputsize=Compact&symbol="+SymbolName+"&interval="+Interval+"&apikey="+API_ALPHA
    else:
        urlString = "https://www.alphavantage.co/query?function="+Function+"&Outputsize=Compact&symbol="+SymbolName+"&apikey="+API_ALPHA
    #print(urlString)    

    str = "" #log string
    try:
        with urllib.request.urlopen(urlString) as url:    
            data = json.loads(url.read().decode())
            if("Information" in data):
                str = SymbolName + 'API Info: ' + data["Information"] + '\n'
                Log(str)
                return -1

            if("Error Message" in data):
                str="Unkown Symbol: " + SymbolName + " "+data["Error Message"]
                Log(str)
                return 0
            
            
            metadata = data["Meta Data"]
            s = Symbol()
            s.metadata.symbol = metadata["2. Symbol"]
            s.metadata.lastrefreshed = metadata["3. Last Refreshed"]
            s.metadata.information = metadata["1. Information"]
            if(Function == "TIME_SERIES_DAILY" or Function == "TIME_SERIES_DAILY_ADJUSTED"):
                s.metadata.timezone = metadata["5. Time Zone"]
            else:
                s.metadata.timezone = metadata["6. Time Zone"]
                
            #print(s.metadata.symbol)
            #print(s.metadata.lastrefreshed)
            #print(s.metadata.timezone)
            #print(s.metadata.information)
            keyslist = list(data.keys())
            timeserieskey = keyslist[1]

            for d in data[timeserieskey]:
                t = TimeSeries()
                t.timeSeries = d
                t.open=float(data[timeserieskey][d]['1. open'])
                t.high=float(data[timeserieskey][d]['2. high'])
                t.low=float(data[timeserieskey][d]['3. low'])
                t.close=float(data[timeserieskey][d]['4. close'])
                t.volume=int(data[timeserieskey][d]['5. volume'])
                s.timeSeriesEntries.append(t)
                
            return s
    except urllib.error.HTTPError as err:
        str = "HTTP ERROR: "
        if hasattr(err,'code'):
            str += "code " + err.code
            Log(str)
        if hasattr(err,'reason'):
            str+= " Reason " + err.reason
        Log(str)
        return None

def Log(str):
    global log
    print(str)
    log.write(str)
    log.flush()

def printDelay(delay):
    for i in range(delay,0,-1):
        sys.stdout.write(str(i)+' ')
        sys.stdout.flush()
        time.sleep(1)

def CreateTimeSeriesSymbolsFromAlphaVantageExcel(ExcelData,Function):
    first = True #skip the header coloumn
    flaggedSymbols = []
    res = ""
    allSymbolsData = []
    resFile = open("flagged.txt","w")
    retrys = 1
    MAX_RETRYS = 5 #maximumtime to try and get a result from the api   
    RETRY_WAIT=60
    logStr=""

    for row in ExcelData:
        if(first):
            first = False #skip the header
            continue
        if(row.value != ""):
            print(row.value)
            s = CreateTimeSeriesSymbolsFromAlphaVantage(row.value)
            if(s==None):#http error occured
                while(s==None):#keep trying till we get a result
                    logStr="Retry ",retrys, " for ", row.value 
                    Log(logStr)
                    time.sleep(RETRY_WAIT)
                    s = CreateTimeSeriesSymbolsFromAlphaVantage(row.value)
                    retrys = retrys + 1
                    
                    if( (retrys-1 == MAX_RETRYS) and (s == None)):
                        Log("Max Retrys reached, exiting...")
                        return allSymbolsData

            if(s == -1):#over call of the api
                Log("Exiting...")
                return allSymbolsData
            if(s == 0):#unkown symbol
                continue

            #all good in the hood    
            allSymbolsData.append(s)
            res = SymbolAnalysis(s)
            if(res !=""):
                flaggedSymbols.append(s)
                val = res+'\n'
                resFile.write(val)
                resFile.flush()    
            printDelay(DELAY)
            #time.sleep(DELAY)

    print("\n*****Analysis Results Ichimoku Cloud*******")
    slist = sorted(flaggedSymbols, key=getKey,reverse=True)
    flaggedSorted = open("flagged_sorted.txt","w")
    val = ""
    for r in slist:
        val = str(r.metadata.symbol + " " + str(r.timeSeriesEntries[0].close) + " TD " + str(r.metadata.tekanSanDelta) + "\n")
        print(val)
        flaggedSorted.write(val)
        flaggedSorted.flush()
    print("*******************************************")
            
    resFile.close()
    flaggedSorted.close()    
    return allSymbolsData
    
 
def DaysHighLow(number_of_days,data,offset_days=0):
    counter = 0
    low=0.0
    high=0.0
    currlow = 0.0
    currhigh =0.0
    offset_counter=0
    original_offset = offset_days #testing only

    #print("working len ", len(data["Time Series (Daily)"]))
     
    for d in data["Time Series (Daily)"]:
     #   print(d)
     #   print("high " + data["Time Series (Daily)"][d]['2. high'] + " low " + data["Time Series (Daily)"][d]['3. low'] )
        
        if(offset_days!=0):
            
            if(offset_counter != offset_days):
                offset_counter = offset_counter+1
                #print("*********SKIPPED********** ",offset_counter)
                continue;
            else:
                offset_days = 0
            
        
        if(counter == 0):
            low = float(data["Time Series (Daily)"][d]['3. low'])
            high = float(data["Time Series (Daily)"][d]['2. high'])
        else:
            currlow = float(data["Time Series (Daily)"][d]['3. low'])
            currhigh = float(data["Time Series (Daily)"][d]['2. high'])
            if(currlow < low):
                low = currlow
            if(currhigh>high):
                high = currhigh
                
        counter = counter + 1
        if(counter == number_of_days ):
            break
    #print(counter)

    #print("working high " , high, " working low " ,low, " days ", number_of_days, " offset ", original_offset)
    
    return high,low

def VerifySymbol(symbol,file):    
    with urllib.request.urlopen("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&Outputsize=Compact&symbol="+symbol+"&apikey="+API_ALPHA) as url:
        data = json.loads(url.read().decode())
        if("Information" in data):
            val = 'API Info: ' + data["Information"] + '\n'
            print(val)
            file.write(val)
            file.flush()        
            return -1
        if("Error Message" in data):
            return 0
        return 1
    
def UnkownSymbol(UnkownValue, file):
    print("Unknown " + UnkownValue)
    val = str(UnkownValue) + '\n'
    file.write(val)
    file.flush()
    


def VerifySymbols(SymbolColoumn):
    first = True
    print("Unkown Symbols:")
    counter = 0
    res = 0

    file = open("verifyresults.txt","w") 
    for row in SymbolColoumn:
        if(first):
            first = False #skip the header
            continue
        print("Checking "+ row.value)
        if(" " in row.value): #spaces will mess up the request url
            UnkownSymbol(row.value,file)
            counter = counter + 1
            continue
        res = VerifySymbol(row.value, file)
        if(res == -1):
            print("API call exceeded program terminates")
            break    
        if (res == 0) :
            UnkownSymbol(row.value,file)
            counter = counter + 1
        time.sleep(DELAY)
    if(res!=-1):
        print("...Finished Verification: ", counter ," Resolutions needed")
        msg = str(counter) + " Resolutions needed"
        file.write(msg)
    file.close()

def IchimokuCloud_(symbol):
    Tenkan_sen = 0.0 #(9-day high + 9-day low) / 2
    Kijun_sen = 0.0 #(26-day high + 26-day low) / 2
    SenkouSpanA = 0.0 #(Tenkan-sen + Kijun-sen) / 2
    SenkouSpanB = 0.0 # (52-day high + 52-day low) / 2
    high=0.0
    low=0.0
    offset = 26#ichimoku cloud offset for senkou span
    
    #Chikou Span = Close plotted 26-days in the past.
    with urllib.request.urlopen("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&Outputsize=Compact&symbol="+symbol+"&apikey="+API_ALPHA) as url:
        data = json.loads(url.read().decode())
        if("Error Message" in data):
            print("Unkown Symbol " + symbol)
            return

        for d in data["Time Series (Daily)"]:
            close_price = float(data["Time Series (Daily)"][d]['4. close'])
            break;
            
            
        #tekan_sen kijun sen for senkospan, 26 periods back
        high,low = DaysHighLow(9,data,offset)
        Tenkan_sen = (high + low) / 2 

        high,low = DaysHighLow(26,data,offset)
        Kijun_sen = (high + low) / 2

        SenkouSpanA = (Tenkan_sen + Kijun_sen) / 2

        high,low = DaysHighLow(52,data,offset)
        SenkouSpanB = (high + low) / 2

        #current tekan sen kijun sen
        high,low = DaysHighLow(9,data)
        Tenkan_sen = (high + low) / 2 

        high,low = DaysHighLow(26,data)
        Kijun_sen = (high + low) / 2

        #print("Symbol:" + symbol)
        #print("Price:",close_price)
        print("Tenkan_sen:",Tenkan_sen)
        print("Kijun_sen:",Kijun_sen)
        
        print("SenkouSpanA: ",SenkouSpanA)
        print("SenkouSpanB: ",SenkouSpanB)
   

 
    
book = xlrd.open_workbook("trading212.xlsx")
sheet = book.sheet_by_index(0)

#VerifySymbols(sheet.col(ALL_SYMBOLS))

apiKeyFile = open("keys.txt","r")
API_ALPHA = apiKeyFile.read()
apiKeyFile.close()

log= open("log.txt","w")
CreateTimeSeriesSymbolsFromAlphaVantageExcel(sheet.col(ALL_SYMBOLS),"TIME_SERIES_DAILY")
log.close()
 










