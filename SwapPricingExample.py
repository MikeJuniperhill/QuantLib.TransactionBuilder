import json, re, os, sys
import numpy as np
import QuantLib as ql

# class for handling transformations between custom object and JSON file
class JsonHandler:
    
    # transform json file to custom object
    def FileToObject(file):
        # nested function: transform dictionary to custom object
        def DictionaryToObject(dic):
            if("__class__" in dic):
                class_name = dic.pop("__class__")
                module_name = dic.pop("__module__")
                module = __import__(module_name)
                class_ = getattr(module, class_name)
                obj = class_(**dic)
            else:
                obj = dic
            return obj        
        return DictionaryToObject(json.load(open(file, 'r')))
    
    # transform custom object to json file
    def ObjectToFile(obj, file):
        # nested function: check whether an object can be json serialized
        def IsSerializable(obj):
            check = True
            try:
                # throws, if an object is not serializable
                json.dumps(obj)
            except:
                check = False
            return check
        # nested function: transform custom object to dictionary
        def ObjectToDictionary(obj):
            dic = { "__class__": obj.__class__.__name__, "__module__": obj.__module__ }            
            dic.update(obj.__dict__)
            # remove all non-serializable items from dictionary before serialization
            keysToBeRemoved = []
            for k, v in dic.items():
                if(IsSerializable(v) == False):
                    keysToBeRemoved.append(k)
            [dic.pop(k, None) for k in keysToBeRemoved]
            return dic
        json.dump(ObjectToDictionary(obj), open(file, 'w'))

# utility class for different QuantLib type conversions 
class Convert():
    
    # convert date string ('yyyy-mm-dd') to QuantLib Date object
    def to_date(s):
        monthDictionary = {
            '01': ql.January, '02': ql.February, '03': ql.March,
            '04': ql.April, '05': ql.May, '06': ql.June,
            '07': ql.July, '08': ql.August, '09': ql.September,
            '10': ql.October, '11': ql.November, '12': ql.December
        }
        arr = re.findall(r"[\w']+", s)
        return ql.Date(int(arr[2]), monthDictionary[arr[1]], int(arr[0]))
    
    # convert string to QuantLib businessdayconvention enumerator
    def to_businessDayConvention(s):
        if (s.upper() == 'FOLLOWING'): return ql.Following
        if (s.upper() == 'MODIFIEDFOLLOWING'): return ql.ModifiedFollowing
        if (s.upper() == 'PRECEDING'): return ql.Preceding
        if (s.upper() == 'MODIFIEDPRECEDING'): return ql.ModifiedPreceding
        if (s.upper() == 'UNADJUSTED'): return ql.Unadjusted
        
    # convert string to QuantLib calendar object
    def to_calendar(s):
        if (s.upper() == 'TARGET'): return ql.TARGET()
        if (s.upper() == 'UNITEDSTATES'): return ql.UnitedStates()
        if (s.upper() == 'UNITEDKINGDOM'): return ql.UnitedKingdom()
        # TODO: add new calendar here
        
    # convert string to QuantLib swap type enumerator
    def to_swapType(s):
        if (s.upper() == 'PAYER'): return ql.VanillaSwap.Payer
        if (s.upper() == 'RECEIVER'): return ql.VanillaSwap.Receiver
        
    # convert string to QuantLib frequency enumerator
    def to_frequency(s):
        if (s.upper() == 'DAILY'): return ql.Daily
        if (s.upper() == 'WEEKLY'): return ql.Weekly
        if (s.upper() == 'MONTHLY'): return ql.Monthly
        if (s.upper() == 'QUARTERLY'): return ql.Quarterly
        if (s.upper() == 'SEMIANNUAL'): return ql.Semiannual
        if (s.upper() == 'ANNUAL'): return ql.Annual

    # convert string to QuantLib date generation rule enumerator
    def to_dateGenerationRule(s):
        if (s.upper() == 'BACKWARD'): return ql.DateGeneration.Backward
        if (s.upper() == 'FORWARD'): return ql.DateGeneration.Forward
        # TODO: add new date generation rule here

    # convert string to QuantLib day counter object
    def to_dayCounter(s):
        if (s.upper() == 'ACTUAL360'): return ql.Actual360()
        if (s.upper() == 'ACTUAL365FIXED'): return ql.Actual365Fixed()
        if (s.upper() == 'ACTUALACTUAL'): return ql.ActualActual()
        if (s.upper() == 'ACTUAL365NOLEAP'): return ql.Actual365NoLeap()
        if (s.upper() == 'BUSINESS252'): return ql.Business252()
        if (s.upper() == 'ONEDAYCOUNTER'): return ql.OneDayCounter()
        if (s.upper() == 'SIMPLEDAYCOUNTER'): return ql.SimpleDayCounter()
        if (s.upper() == 'THIRTY360'): return ql.Thirty360()

# wrapper class for QuantLib vanilla interest rate swap
class VanillaSwap(object):
    
    def __init__(self, ID, swapType, nominal, startDate, maturityDate, fixedLegFrequency, 
        fixedLegCalendar, fixedLegConvention, fixedLegDateGenerationRule, fixedLegRate, fixedLegDayCount,
        fixedLegEndOfMonth, floatingLegFrequency, floatingLegCalendar, floatingLegConvention, 
        floatingLegDateGenerationRule, floatingLegSpread, floatingLegDayCount, floatingLegEndOfMonth):

        self.ID = ID
        self.swapType = swapType
        self.nominal = nominal
        self.startDate = startDate
        self.maturityDate = maturityDate
        self.fixedLegFrequency = fixedLegFrequency
        self.fixedLegCalendar = fixedLegCalendar
        self.fixedLegConvention = fixedLegConvention
        self.fixedLegDateGenerationRule = fixedLegDateGenerationRule
        self.fixedLegRate = fixedLegRate
        self.fixedLegDayCount = fixedLegDayCount
        self.fixedLegEndOfMonth = fixedLegEndOfMonth
        self.floatingLegFrequency = floatingLegFrequency
        self.floatingLegCalendar = floatingLegCalendar
        self.floatingLegConvention = floatingLegConvention
        self.floatingLegDateGenerationRule = floatingLegDateGenerationRule
        self.floatingLegSpread = floatingLegSpread
        self.floatingLegDayCount = floatingLegDayCount
        self.floatingLegEndOfMonth = floatingLegEndOfMonth
        
    def setPricingEngine(self, engine, floatingLegIborIndex):
        # create fixed leg schedule
        fixedLegSchedule = ql.Schedule(
            Convert.to_date(self.startDate), 
            Convert.to_date(self.maturityDate),
            ql.Period(Convert.to_frequency(self.fixedLegFrequency)), 
            Convert.to_calendar(self.fixedLegCalendar), 
            Convert.to_businessDayConvention(self.fixedLegConvention),
            Convert.to_businessDayConvention(self.fixedLegConvention),
            Convert.to_dateGenerationRule(self.fixedLegDateGenerationRule),
            self.fixedLegEndOfMonth)
        
        # create floating leg schedule
        floatingLegSchedule = ql.Schedule(
            Convert.to_date(self.startDate), 
            Convert.to_date(self.maturityDate),
            ql.Period(Convert.to_frequency(self.floatingLegFrequency)), 
            Convert.to_calendar(self.floatingLegCalendar), 
            Convert.to_businessDayConvention(self.floatingLegConvention),
            Convert.to_businessDayConvention(self.floatingLegConvention),
            Convert.to_dateGenerationRule(self.floatingLegDateGenerationRule),
            self.floatingLegEndOfMonth)

        # create vanilla interest rate swap instance
        self.instrument = ql.VanillaSwap(
            Convert.to_swapType(self.swapType), 
            self.nominal, 
            fixedLegSchedule, 
            self.fixedLegRate, 
            Convert.to_dayCounter(self.fixedLegDayCount), 
            floatingLegSchedule,
            floatingLegIborIndex, # use given index argument
            self.floatingLegSpread, 
            Convert.to_dayCounter(self.floatingLegDayCount))    
        
        # pair instrument with pricing engine
        self.instrument.setPricingEngine(engine)        

    def NPV(self):
        return self.instrument.NPV()

# read all JSON files from repository, create vanilla swap instances
repository = sys.argv[1]
files = os.listdir(repository)
swaps = [JsonHandler.FileToObject(repository + file) for file in files]

# create valuation curve, index fixings and pricing engine
curveHandle = ql.YieldTermStructureHandle(ql.FlatForward(ql.Date(5, ql.July, 2019), 0.02, ql.Actual360()))
engine = ql.DiscountingSwapEngine(curveHandle)
index = ql.USDLibor(ql.Period(ql.Quarterly), curveHandle)
index.addFixings([ql.Date(12, ql.June, 2019)], [0.02])

# set pricing engine (and floating index) and request pv for all swaps
for swap in swaps:
    swap.setPricingEngine(engine, index)
    print(swap.ID, swap.NPV())
