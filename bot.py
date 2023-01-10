#region imports
from AlgorithmImports import *
#endregion
from System.Drawing import Color
from collections import deque


class Bollinger(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 3, 23)
        self.SetEndDate(2022, 3,8 )
        self.SetCash(100000)
     
        self.pair = self.AddEquity("SPY", Resolution.Minute).Symbol
       
        self.bb = self.BB(self.pair, 14, 2)
       
        #self.vwap = self.VWAP("SPY", 20)
        self.ema1 = self.EMA(self.pair,30,Resolution.Minute)
        
        self.ema2 = self.EMA(self.pair,100,Resolution.Minute)
        self.ema3 = self.EMA(self.pair,150,Resolution.Minute)

        self.atr = self.ATR(self.pair, 7, Resolution.Minute)
        self.rsi = self.RSI(self.pair,16, MovingAverageType.Simple, Resolution.Minute)
        self.max_ema1 = IndicatorExtensions.MAX(self.ema1, 4)
        self.max_ema2 = IndicatorExtensions.MAX(self.ema2, 4)
        self.max_ema3 = IndicatorExtensions.MAX(self.ema3, 4)
        self.min_ema1 = IndicatorExtensions.MIN(self.ema1, 4)
        self.min_ema2 = IndicatorExtensions.MIN(self.ema2, 4)
        self.min_ema3 = IndicatorExtensions.MIN(self.ema3, 4)

        self.max_ema11 = RollingWindow[float](5)
        self.max_ema22 = RollingWindow[float](5)
        self.max_ema33 = RollingWindow[float](5)
        self.min_ema11 = RollingWindow[float](5)
        self.min_ema22 = RollingWindow[float](5)
        self.min_ema33 = RollingWindow[float](5)

        self.delta3 = IndicatorExtensions.Over(self.ema1, self.ema2)
        self.delta4 = IndicatorExtensions.Over(self.ema2, self.ema3)
        self.delta1 = IndicatorExtensions.Over(self.ema2, self.ema1)
        self.delta2 = IndicatorExtensions.Over(self.ema3, self.ema2)
        self.maxWindow = RollingWindow[float](20)
        self.minWindow = RollingWindow[float](20)
        self.closeWindow = RollingWindow[float](3)
        
        global trend, BullTrend, BullAngle
        trend = 0
        BullTrend = 0
        BullAngle = 0
        stockPlot = Chart('Trade Plot')
        stockPlot.AddSeries(Series('TP', SeriesType.Scatter, '$', 
                            Color.Green, ScatterMarkerSymbol.Diamond))
        stockPlot.AddSeries(Series('SL', SeriesType.Scatter, '$', 
                            Color.Red, ScatterMarkerSymbol.Diamond))
        stockPlot.AddSeries(Series('Buy Bull', SeriesType.Scatter, '$', 
                            Color.Black, ScatterMarkerSymbol.Triangle))
        stockPlot.AddSeries(Series('Sell Bull', SeriesType.Scatter, '$', 
                            Color.Navy, ScatterMarkerSymbol.TriangleDown)) 
        stockPlot.AddSeries(Series('Buy Bol', SeriesType.Scatter, '$', 
                            Color.Black, ScatterMarkerSymbol.Diamond))
        stockPlot.AddSeries(Series('Sell Bol', SeriesType.Scatter, '$', 
                            Color.Blue, ScatterMarkerSymbol.Diamond))                                         
        stockPlot.AddSeries(Series('BuySignal', SeriesType.Scatter, '$', 
                            Color.Green, ScatterMarkerSymbol.Triangle))
        stockPlot.AddSeries(Series('SellSignal', SeriesType.Scatter, '$', 
                            Color.Red, ScatterMarkerSymbol.TriangleDown))
        stockPlot.AddSeries(Series('high', SeriesType.Scatter, '$', 
                            Color.Yellow, ScatterMarkerSymbol.Diamond))
        stockPlot.AddSeries(Series('low', SeriesType.Scatter, '$', 
                            Color.Orange, ScatterMarkerSymbol.Diamond))
       
        stockPlot.AddSeries(Series('downtrend', SeriesType.Scatter, '$', 
                            Color.Red, ScatterMarkerSymbol.Triangle))
        stockPlot.AddSeries(Series('uptrend', SeriesType.Scatter, '$', 
                            Color.Green, ScatterMarkerSymbol.Triangle))
       
        self.AddChart(stockPlot)
        self.SetWarmUp(timedelta(6))

    def OnData(self, data):
        if data[self.pair] is None:
	        return
        if not self.bb.IsReady:
            return
      
        if not self.rsi.IsReady:
            return
        if not self.atr.IsReady:
            return            
        if not self.ema1.IsReady:
            return    
         
        if not self.ema2.IsReady:
            return  
        if not self.ema3.IsReady:
            return       
    
        self.max_ema11.Add(self.ema1.Current.Value)  
        self.max_ema22.Add(self.ema2.Current.Value)  
        self.max_ema33.Add(self.ema3.Current.Value)  
        self.min_ema11.Add(self.ema1.Current.Value)  
        self.min_ema22.Add(self.ema2.Current.Value)  
        self.min_ema33.Add(self.ema3.Current.Value)  
        self.maxWindow.Add(data[self.pair].High)  
        self.minWindow.Add(data[self.pair].Low)  
        self.closeWindow.Add(data[self.pair].Close)  

        if not self.maxWindow.IsReady:
            return    
        if not self.minWindow.IsReady:
            return   
        if not self.max_ema11.IsReady:
            return      
        if not self.max_ema22.IsReady:
            return   
        if not self.max_ema33.IsReady:
            return  
        if not self.min_ema11.IsReady:
            return      
        if not self.min_ema22.IsReady:
            return   
        if not self.min_ema33.IsReady:
            return        
        if not self.closeWindow.IsReady:
            return                             
        price = data[self.pair].Price  

        global BullTrend,trend,slatr,TP,SL,tpratio,high,low,BullAngle,priceHelp

        
        low = min(self.minWindow)
        high = max(self.maxWindow)
        low2 = self.minWindow[0]
        high2 = self.maxWindow[0]
        
        #add candles on chart
        self.Plot("Trade Plot", "high", high2)
        self.Plot("Trade Plot", "low", low2)
        

       #bull angle

        if  self.max_ema11[4]/self.ema1.Current.Value < 0.9998 and self.max_ema22[4]/self.ema2.Current.Value < 0.9998 and self.max_ema33[4]/self.ema3.Current.Value < 0.9998:
             BullAngle = 1

             #down
        elif self.ema1.Current.Value/self.max_ema11[4] < 0.9998 and self.ema2.Current.Value/self.max_ema22[4] < 0.9998 and self.ema3.Current.Value/self.max_ema33[4] < 0.9998:
             BullAngle = 1
        else: 
            BullAngle = 0

        if low >= self.ema2.Current.Value:
            trend = 1 
            """
            print("uptrend")
            self.Plot("Trade Plot", "uptrend", price)
            """
        elif high <= self.ema2.Current.Value:
            trend = -1
            """
            print("downtrend")
            self.Plot("Trade Plot", "downtrend", price)
            """
        else: 
            trend = 0

        #bull trend

        if self.ema1.Current.Value >= max(self.max_ema11) and self.ema2.Current.Value >= max(self.max_ema22) and self.ema3.Current.Value >= max(self.max_ema33):
          

            if self.delta1.Current.Value < 0.99989 and self.delta2.Current.Value < 0.99989:
                BullTrend = 1
                #self.Plot("Trade Plot", "delta", self.delta1.Current.Value)
                """
                print("uptrend")
                self.Plot("Trade Plot", "uptrend", price)
                """
        elif self.ema2.Current.Value <= min(self.min_ema22) and self.ema3.Current.Value <= min(self.min_ema33):
            
            if self.delta3.Current.Value < 0.99989 and self.delta4.Current.Value < 0.99989:
                BullTrend = -1
                """
                print("downtrend")
                self.Plot("Trade Plot", "downtrend", price)
                """
        else:
            BullTrend = 0
        
        self.Plot("Trade Plot", "Price", price)
        self.Plot("Trade Plot", "Ema2", self.ema2.Current.Value)
        #self.Plot("Trade Plot", "UpperBand", self.bb.UpperBand.Current.Value)
        #self.Plot("Trade Plot", "LowerBand", self.bb.LowerBand.Current.Value)
        
        """
        for debugging, where StonksBot should buy/sell
        if  BullTrend == -1 and  BullAngle == 1 and price < self.ema2.Current.Value and self.maxWindow[1] >= self.ema2.Current.Value and self.maxWindow[1] < self.ema3.Current.Value and self.maxWindow[2] < self.ema3.Current.Value :
              
              
             self.Plot("Trade Plot", "SellSignal", price)
             
        if  trend == 1 and self.bb.LowerBand.Current.Value >= price and self.rsi.Current.Value < 45 :
              
               self.Plot("Trade Plot", "BuySignal", price)
               
  """
        if not self.Portfolio.Invested:
           
           if BullTrend == 1 and BullAngle == 1 and price > self.ema1.Current.Value and self.minWindow[1] <= self.ema1.Current.Value and self.ema3.Current.Value < self.minWindow[1] and self.ema3.Current.Value < self.minWindow[2]:
             
             self.SetHoldings(self.pair, 1, tag = "Bull trend buy")
             SL = self.minWindow[1] - self.atr.Current.Value 
             TP = price+(price-self.minWindow[1]) + self.atr.Current.Value 
             priceHelp = price
            
             self.Plot("Trade Plot", "Buy Bull", price)

           elif BullTrend ==-1 and  BullAngle == 1 and price < self.ema2.Current.Value and self.maxWindow[1] >= self.ema2.Current.Value and self.maxWindow[1] < self.ema3.Current.Value and self.maxWindow[2] < self.ema3.Current.Value :
             
             self.SetHoldings(self.pair, -1, tag = "Bull trend sell")
             SL = self.maxWindow[1] + (1/4)*self.atr.Current.Value 
             TP = price - 87/100*(self.maxWindow[1] - price  )  
             priceHelp = price
            # self.Plot("Trade Plot", "TP", TP)
           #  self.Plot("Trade Plot", "SL", SL)
             self.Plot("Trade Plot", "Sell Bull", price)
              
           
           elif  trend == 1  and self.rsi.Current.Value < 45 and self.closeWindow[1] <= self.bb.LowerBand.Current.Value :
              self.SetHoldings(self.pair, 1, tag = "Bollinger buy")
              
              slatr = 5 * self.atr.Current.Value  
              tpratio = 1
              SL = price - slatr
              TP = price + slatr*tpratio
              priceHelp = price
              self.Plot("Trade Plot", "Buy Bol", price)
            #  self.Plot("Trade Plot", "TP", TP)
            #  self.Plot("Trade Plot", "SL", SL)
            
           elif  trend == -1 and self.bb.UpperBand.Current.Value <= self.closeWindow[1] and self.rsi.Current.Value > 55  :
               self.SetHoldings(self.pair, -1, tag = "Bollinger sell")
               self.Plot("Trade Plot", "Sell Bol", price)
               priceHelp = price
               slatr = 5 * self.atr.Current.Value  
               tpratio = 1
               SL = price + slatr
               TP = price - slatr*tpratio 
             #  self.Plot("Trade Plot", "TP", TP)
              # self.Plot("Trade Plot", "SL", SL)
        
        else:  
            
            if self.Portfolio[self.pair].IsLong:
                """
                if self.ema3.Current.Value > self.closeWindow[1]  :
                    self.Liquidate(tag = "ema 150 long")
                    self.Plot("Trade Plot", "Liquidate ema150", price)
                    """

                if self.rsi.Current.Value>=90 and price > high :
                    self.Liquidate(tag = "rsi 90" + " profit: " + str((price - priceHelp)/priceHelp))
                    self.Plot("Trade Plot", "TP", price)
                    #self.Plot("Trade Plot", "Liquidate 90", price)

                if price >= TP:
                    if self.rsi.Current.Value < 60 or self.closeWindow[1]<price:
                        SL = TP - self.atr.Current.Value
                        TP = TP + self.atr.Current.Value * 2
                    else:    
                      self.Liquidate(tag = "TP long" + " profit: " + str((price - priceHelp)/priceHelp))
                      self.Plot("Trade Plot", "TP", price)
                if price <= SL:    
                   self.Liquidate(tag = "SL long"  + " diffrence: " + str((price - priceHelp)/priceHelp))
                   if ((price - priceHelp)/priceHelp) > 0:
                     self.Plot("Trade Plot", "TP", price)
                   else:
                     self.Plot("Trade Plot", "SL", price)

            if self.Portfolio[self.pair].IsShort:
                """
                if self.ema3.Current.Value < self.closeWindow[1] :
                     self.Liquidate(tag = "ema 150 short")
                     self.Plot("Trade Plot", "Liquidate ema150", price)
                     """
                if self.rsi.Current.Value<=10:
                    self.Liquidate(tag = "Liquidate 10" +" profit: " +str((priceHelp-price)/priceHelp))    
                    if ((priceHelp-price)/priceHelp) > 0:
                      self.Plot("Trade Plot", "TP", price) 
                    else:
                          self.Plot("Trade Plot", "SL", price) 
                if price <= TP:
                    if self.rsi.Current.Value > 30:
                        SL = TP + (1/10000)*TP
                        TP = TP - self.atr.Current.Value * 2
                    else:    
                       self.Liquidate(tag = "TP short" +" profit: " +str((priceHelp-price)/priceHelp)) 
                       self.Plot("Trade Plot", "TP", price)   
                if price >= SL:
                    if ((priceHelp-price)/priceHelp) > 0:
                        self.Plot("Trade Plot", "TP", price) 
                    else:
                        self.Plot("Trade Plot", "SL", price)
                    self.Liquidate(tag = "SL short" +" diffrence: " +str((priceHelp-price)/priceHelp))
                     
