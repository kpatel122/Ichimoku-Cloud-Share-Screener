
class IchimokuCloud:
    def __init__(self):
        #self.symbolName = 
        self.tenkanSen = 0.0 #(9-day high + 9-day low) / 2
        self.kijunSen = 0.0 #(26-day high + 26-day low) / 2
        self.senkouSpanA = 0.0 #(Tenkan-sen + Kijun-sen) / 2
        self.senkouSpanB = 0.0 # (52-day high + 52-day low) / 2


        #high=0.0
        #low=0.0
        #offset = 26#ichimoku cloud offset for senkou span
        #close_price = 0.0
    def DaysHighLow(self,symbol,numberOfDays,offsetDays=0):
        if(offsetDays > len(symbol.timeSeriesEntries)):
            print("******** Not enough data for offset ", offsetDays, " entries ",  len(symbol.timeSeriesEntries))
            return 1,1

        
        low = symbol.timeSeriesEntries[offsetDays].low
        high = symbol.timeSeriesEntries[offsetDays].high
        currlow = 0.0
        currhigh = 0.0
        
        symbolsLen = len(symbol.timeSeriesEntries)#sometimes theres not enough data entries from the api to go x days back
        if((numberOfDays+offsetDays)<symbolsLen):
            listRange = numberOfDays
        else:
            print("***Warning not enough data entries to calculate days + offset: Required ",(numberOfDays+offsetDays), " Actual ", symbolsLen )
            listRange = symbolsLen-offsetDays
            #print("Using range ", listRange)
        
        for x in range(listRange):
            
            c = symbol.timeSeriesEntries[x+offsetDays]
            currlow = c.low
            currhigh = c.high

            if(currlow < low):
                low = currlow
            if(currhigh>high):
                high = currhigh

        #print("Testing High ", high, " Testing Low ", low, " days ", numberOfDays, " offset ", offsetDays)
        return high,low
        
    def PrintIchimokuCloud(self):

        print("Tenkan_sen:",self.tenkanSen)
        print("Kijun_sen:",self.kijunSen)
        
        print("SenkouSpanA: ",self.senkouSpanA)
        print("SenkouSpanB: ",self.senkouSpanB)

    def CalculateTekanSanDelta(self,symbol):
        delta = 0.0
        
        #tenkanSen (9-day high + 9-day low) 1 period back
        high,low = self.DaysHighLow(symbol,9,1)
        tenkanSenBack = (high + low) / 2

        delta = self.tenkanSen - tenkanSenBack 
        return delta

        
    def Calculate(self,symbol):
    
        offset = 26 #senkou spans calculated 26 periods back
        high = 0.0
        low =0.0

        #senkou span calculations
        #tenkanSen (9-day high + 9-day low) / 2: 26 periods back
        high,low = self.DaysHighLow(symbol,9,offset)
        self.tenkanSen = (high + low) / 2 

        #kijunSen (26-day high + 26-day low) / 2: 26 periods back
        high,low = self.DaysHighLow(symbol,26,offset)
        self.kijunSen = (high + low) / 2

        #senkouSpanA (Tenkan-sen + Kijun-sen) / 2: 26 periods back 
        self.senkouSpanA = (self.tenkanSen + self.kijunSen) / 2

        #SenkouSpanB (52-day high + 52-day low) / 2: 26 periods back
        high,low = self.DaysHighLow(symbol,52,offset)
        self.senkouSpanB = (high + low) / 2

        #current tekan sen kijun sen

        #tenkanSen (9-day high + 9-day low)
        high,low = self.DaysHighLow(symbol,9)
        self.tenkanSen = (high + low) / 2 

        #kijunSen (26-day high + 26-day low) / 2
        high,low = self.DaysHighLow(symbol,26)
        self.kijunSen = (high + low) / 2
    
    def IsBear(self, Symbol):
         #print(Symbol.metadata.symbol)
        symbolName = Symbol.metadata.symbol
        price = Symbol.timeSeriesEntries[0].close
       
        bear = False
        if(price>self.tenkanSen):
            if(self.tenkanSen>self.kijunSen):
                if(self.kijunSen>self.senkouSpanA):
                    print("Above TK Lines and Cloud A " + symbolName + " ", price)
                    bear = True
                    if(self.senkouSpanA>self.senkouSpanB):
                        print("Above All IC Lines " + symbolName + " ", price)
                        bear = True

        return bear


        
        
        

        
