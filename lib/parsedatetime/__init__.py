

"""parsedatetime

Parse human-readable date/time text.
Adapted from BoxKite by' Mike Taylor (bear@bear.im)

Requires Python 2.6 or later
"""

import re
import time
import datetime
import calendar
import logging
import email.utils

try:
    from itertools import imap
except ImportError:
    imap = map
from itertools import chain

import pdt_locales

# as a library, do *not* setup logging
# see http://docs.python.org/2/howto/logging.html#configuring-logging-for-a-library
# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

log = logging.getLogger(__name__)
log.addHandler(NullHandler())

pdtLocales = { 'icu':   pdt_locales.pdtLocale_icu,
               'en_US': pdt_locales.pdtLocale_en,
             }



# # rfc822.py defines several time zones, but we define some extra ones.
# # 'ET' is equivalent to 'EST', etc.
# _additional_timezones = {'AT': -400, 'ET': -500,
#                          'CT': -600, 'MT': -700,
#                          'PT': -800}
# email.utils._timezones.update(_additional_timezones)


class Calendar:
    """
    A collection of routines to input, parse and manipulate date and times.
    The text can either be 'normal' date values or it can be human readable.
    """

    def __init__(self, constants=None):
        """
        Default constructor for the L{Calendar} class.

        @type  constants: object
        @param constants: Instance of the class L{Constants}

        @rtype:  object
        @return: L{Calendar} instance
        """
          # if a constants reference is not included, use default
        if constants is None:
            self.ptc = Constants()
        else:
            self.ptc = constants

        self.weekdyFlag    = False  # monday/tuesday/...
        self.dateStdFlag   = False  # 07/21/06
        self.dateStrFlag   = False  # July 21st, 2006
        self.timeStdFlag   = False  # 5:50
        self.meridianFlag  = False  # am/pm
        self.dayStrFlag    = False  # tomorrow/yesterday/today/..
        self.timeStrFlag   = False  # lunch/noon/breakfast/...
        self.modifierFlag  = False  # after/before/prev/next/..
        self.modifier2Flag = False  # after/before/prev/next/..
        self.unitsFlag     = False  # hrs/weeks/yrs/min/..
        self.qunitsFlag    = False  # h/m/t/d..

        self.timeFlag      = 0
        self.dateFlag      = 0
        self.list_of_matchers =   [ self.ptc.CRE_WEEKDAY,
                                    self.ptc.CRE_MODIFIER,
                                    self.ptc.CRE_MODIFIER2,
                                    self.ptc.CRE_NUMBER,
                                    self.ptc.CRE_UNITS,
                                    self.ptc.CRE_QUNITS,
                                    self.ptc.CRE_MUNITS,
                                    self.ptc.CRE_DATE3,
                                    self.ptc.CRE_DATE4,
                                    self.ptc.CRE_DATE5,
                                    self.ptc.CRE_DATE,
                                    self.ptc.CRE_DAY,
                                    self.ptc.CRE_WEEKDAY,
                                    self.ptc.CRE_SPECIAL,
                                    self.ptc.CRE_TIME,
                                    self.ptc.CRE_TIMEHMS2,
                                    self.ptc.CRE_TIMEHMS ]


    def _convertUnitAsWords(self, unitText):
        """
        Converts text units into their number value

        Five = 5
        Twenty Five = 25
        Two hundred twenty five = 225
        Two thousand and twenty five = 2025
        Two thousand twenty five = 2025

        @type  unitText: string
        @param unitText: number text to convert

        @rtype:  integer
        @return: numerical value of unitText
        """
        # TODO: implement this
        pass



    def parseHelper(self, matched_list):
        matched_entities = []
        for x in matched_list:
            curr = x[0]
            matched_entities.append(curr)
        return matched_entities

    def parse(self, datetimeString, sourceTime=None):
        """
        Input: An incoming message (string)
        Ouptut: A list of dates (list of strings)
        """

        datetimeString = re.sub(r'(\w)(\.)(\s)', r'\1\3', datetimeString)
        datetimeString = re.sub(r'(\w)(\'|")(\s|$)', r'\1 \3', datetimeString)
        datetimeString = re.sub(r'(\s|^)(\'|")(\w)', r'\1 \3', datetimeString)
        if sourceTime:
            if isinstance(sourceTime, datetime.datetime):
                log.debug('coercing datetime to timetuple')
                sourceTime = sourceTime.timetuple()
            else:
                if not isinstance(sourceTime, time.struct_time) and \
                   not isinstance(sourceTime, tuple):
                    raise Exception('sourceTime is not a struct_time')

        s         = datetimeString.strip().lower()
        parseStr  = ''
        totalTime = sourceTime

        if s == '' :
            if sourceTime is not None:
                return (sourceTime, self.dateFlag + self.timeFlag)
            else:
                return (time.localtime(), 0)

        self.timeFlag = 0
        self.dateFlag = 0

        dates_gotten = []
        for pattern in self.list_of_matchers:
            # Weekday
            m = pattern.search(s)
            if (m is not None):
                dates_gotten.append(m.group())
        word_date_matcher = re.compile(r'((the)? \w+(st|th|nd|rd))')
        units_matcher = re.compile(r'((last|next) (week|month|year))')
        time_matcher = re.compile(r'(at? ([1-9]|1[012])\s?(pm|am)?)')
        numeric_matcher = re.compile(r'(in a (few|couple) (of )?(hours|minutes|seconds|days|weeks|months|years))')
        number_word_date_matches = word_date_matcher.findall(s)
        # Now that we've figured out which parts of the sentene has parts of dates/times,
        # we now figure  out which date-like objects belong together
        time_matches = time_matcher.findall(s)
        unit_matches = units_matcher.findall(s)
        numeric_matches = numeric_matcher.findall(s)
        formatted_matched_dates = self.parseHelper(number_word_date_matches)
        formatted_matched_times = self.parseHelper(time_matches)
        formatted_matched_units = self.parseHelper(unit_matches)
        formatted_matched_numeric = self.parseHelper(numeric_matches)
        dates_gotten.extend(formatted_matched_dates)
        dates_gotten.extend(formatted_matched_times)
        dates_gotten.extend(formatted_matched_units)
        dates_gotten.extend(formatted_matched_numeric)
        curr_date_streak = False
        curr_date_string = []
        s = s.split(" ")
        dates_parts_gotten = [m.strip('\'\"-,.:;!? ') for m in dates_gotten]
        formatted_dates_parts_gotten = []
        for date in dates_parts_gotten:
            if ' ' in date:
                parts_of_entities = date.split(' ')
                formatted_dates_parts_gotten.extend(parts_of_entities)
            else:
                formatted_dates_parts_gotten.append(date)
        dates_gotten_dict = {i: True for i in formatted_dates_parts_gotten}
        dates_list = []
        # Here, given taht we have annotated parts of the sentence, congregate dates
        # i.e. 'Feb 20th' is not Feb and 20th, but is one entity
        for word in s:
            word = word.rstrip('\'\"-,.:;!?')
            if (curr_date_streak and dates_gotten_dict.get(word)):
                curr_date_string.append(word)
            elif dates_gotten_dict.get(word):
                curr_date_streak = True
                curr_date_string.append(word)
            else:
                dates_list.append(" ".join(curr_date_string))
                curr_date_string = []
                curr_date_streak = False
        dates_list.append(" ".join(curr_date_string))
        dates_list  = filter(None, dates_list)
        return dates_list


def _initSymbols(ptc):
    """
    Initialize symbols and single character constants.
    """
      # build am and pm lists to contain
      # original case, lowercase, first-char and dotted
      # versions of the meridian text

    if len(ptc.locale.meridian) > 0:
        am     = ptc.locale.meridian[0]
        ptc.am = [ am ]

        if len(am) > 0:
            ptc.am.append(am[0])
            ptc.am.append('{0}.{1}.'.format(am[0], am[1]))
            am = am.lower()
            ptc.am.append(am)
            ptc.am.append(am[0])
            ptc.am.append('{0}.{1}.'.format(am[0], am[1]))
    else:
        am     = ''
        ptc.am = [ '', '' ]

    if len(ptc.locale.meridian) > 1:
        pm     = ptc.locale.meridian[1]
        ptc.pm = [ pm ]

        if len(pm) > 0:
            ptc.pm.append(pm[0])
            ptc.pm.append('{0}.{1}.'.format(pm[0], pm[1]))
            pm = pm.lower()
            ptc.pm.append(pm)
            ptc.pm.append(pm[0])
            ptc.pm.append('{0}.{1}.'.format(pm[0], pm[1]))
    else:
        pm     = ''
        ptc.pm = [ '', '' ]


class Constants(object):
    """
    Default set of constants for parsedatetime.

    If PyICU is present, then the class will first try to get PyICU
    to return a locale specified by C{localeID}.  If either C{localeID} is
    None or if the locale does not exist within PyICU, then each of the
    locales defined in C{fallbackLocales} is tried in order.

    If PyICU is not present or none of the specified locales can be used,
    then the class will initialize itself to the en_US locale.

    if PyICU is not present or not requested, only the locales defined by
    C{pdtLocales} will be searched.
    """
    def __init__(self, localeID=None, usePyICU=True, fallbackLocales=['en_US']):
        self.localeID        = localeID
        self.fallbackLocales = fallbackLocales

        if 'en_US' not in self.fallbackLocales:
            self.fallbackLocales.append('en_US')

          # define non-locale specific constants

        self.locale   = None
        self.usePyICU = usePyICU

        # starting cache of leap years
        # daysInMonth will add to this if during
        # runtime it gets a request for a year not found
        self._leapYears = [ 1904, 1908, 1912, 1916, 1920, 1924, 1928, 1932, 1936, 1940, 1944,
                            1948, 1952, 1956, 1960, 1964, 1968, 1972, 1976, 1980, 1984, 1988,
                            1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024, 2028, 2032,
                            2036, 2040, 2044, 2048, 2052, 2056, 2060, 2064, 2068, 2072, 2076,
                            2080, 2084, 2088, 2092, 2096 ]

        self.Second =   1
        self.Minute =  60 * self.Second
        self.Hour   =  60 * self.Minute
        self.Day    =  24 * self.Hour
        self.Week   =   7 * self.Day
        self.Month  =  30 * self.Day
        self.Year   = 365 * self.Day

        self._DaysInMonthList = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        self.rangeSep         = '-'
        self.BirthdayEpoch    = 50

        # YearParseStyle controls how we parse "Jun 12", i.e. dates that do
        # not have a year present.  The default is to compare the date given
        # to the current date, and if prior, then assume the next year.
        # Setting this to 0 will prevent that.

        self.YearParseStyle = 1

        # DOWParseStyle controls how we parse "Tuesday"
        # If the current day was Thursday and the text to parse is "Tuesday"
        # then the following table shows how each style would be returned
        # -1, 0, +1
        #
        # Current day marked as ***
        #
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1
        # current         -1,0     ***
        # week +1          +1
        #
        # If the current day was Monday and the text to parse is "Tuesday"
        # then the following table shows how each style would be returned
        # -1, 0, +1
        #
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1           -1
        # current      *** 0,+1
        # week +1

        self.DOWParseStyle = 1

        # CurrentDOWParseStyle controls how we parse "Friday"
        # If the current day was Friday and the text to parse is "Friday"
        # then the following table shows how each style would be returned
        # True/False. This also depends on DOWParseStyle.
        #
        # Current day marked as ***
        #
        # DOWParseStyle = 0
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1
        # current                      T,F
        # week +1
        #
        # DOWParseStyle = -1
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1                       F
        # current                       T
        # week +1
        #
        # DOWParseStyle = +1
        #
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1
        # current                       T
        # week +1                       F

        self.CurrentDOWParseStyle = False

        if self.usePyICU:
            self.locale = pdtLocales['icu'](self.localeID)

            if self.locale.icu is None:
                self.usePyICU = False
                self.locale   = None

        if self.locale is None:
            if not self.localeID in pdtLocales:
                for id in range(0, len(self.fallbackLocales)):
                    self.localeID = self.fallbackLocales[id]
                    if self.localeID in pdtLocales:
                        break

            self.locale = pdtLocales[self.localeID]()

        if self.locale is not None:
              # escape any regex special characters that may be found
            wd   = tuple(map(re.escape, self.locale.Weekdays))
            swd  = tuple(map(re.escape, self.locale.shortWeekdays))
            mth  = tuple(map(re.escape, self.locale.Months))
            smth = tuple(map(re.escape, self.locale.shortMonths))

            self.locale.re_values['months']      = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % mth
            self.locale.re_values['shortmonths'] = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % smth
            self.locale.re_values['days']        = '%s|%s|%s|%s|%s|%s|%s' % wd
            self.locale.re_values['shortdays']   = '%s|%s|%s|%s|%s|%s|%s' % swd

            self.locale.re_values['numbers']     = '|'.join(map(re.escape, self.locale.numbers))

            l = []
            for s in self.locale.units:
                l = l + self.locale.units[s]
            self.locale.re_values['units'] = '|'.join(tuple(map(re.escape, l)))

            l = []
            lbefore = []
            lafter  = []
            for s in self.locale.Modifiers:
                l.append(s)
                if self.locale.Modifiers[s] < 0:
                    lbefore.append(s)
                elif self.locale.Modifiers[s] > 0:
                    lafter.append(s)
            self.locale.re_values['modifiers']        = '|'.join(tuple(map(re.escape, l)))
            self.locale.re_values['modifiers-before'] = '|'.join(tuple(map(re.escape, lbefore)))
            self.locale.re_values['modifiers-after']  = '|'.join(tuple(map(re.escape, lafter)))

            # todo: analyze all the modifiers to figure out which ones truly belong where.
            #       while it is obvious looking at the code that _evalModifier2 should be
            #       handling 'after', it remains to be researched which ones belong where
            #       and how to make it locale-independent
            lmodifiers = []
            lmodifiers2 = []
            for s in self.locale.Modifiers:
                if self.locale.Modifiers[s] < 0 or s in ['after', 'from']:
                    lmodifiers2.append(s)
                elif self.locale.Modifiers[s] > 0:
                    lmodifiers.append(s)
            self.locale.re_values['modifiers-one'] = '|'.join(tuple(map(re.escape, lmodifiers)))
            self.locale.re_values['modifiers-two'] = '|'.join(tuple(map(re.escape, lmodifiers2)))

            l = []
            for s in self.locale.re_sources:
                l.append(s)
            self.locale.re_values['sources'] = '|'.join(tuple(map(re.escape, l)))

              # build weekday offsets - yes, it assumes the Weekday and shortWeekday
              # lists are in the same order and Mon..Sun (Python style)
            o = 0
            for key in self.locale.Weekdays:
                self.locale.WeekdayOffsets[key] = o
                o += 1
            o = 0
            for key in self.locale.shortWeekdays:
                self.locale.WeekdayOffsets[key] = o
                o += 1

              # build month offsets - yes, it assumes the Months and shortMonths
              # lists are in the same order and Jan..Dec
            o = 1
            for key in self.locale.Months:
                self.locale.MonthOffsets[key] = o
                o += 1
            o = 1
            for key in self.locale.shortMonths:
                self.locale.MonthOffsets[key] = o
                o += 1

            # self.locale.DaySuffixes = self.locale.re_values['daysuffix'].split('|')

        _initSymbols(self)

        # TODO add code to parse the date formats and build the regexes up from sub-parts
        # TODO find all hard-coded uses of date/time seperators

        # matching cases with "the 20th"
        self.RE_DATE5     = r'the \w*(?= )' % self.locale.re_values
        # not being used in code, but kept in case others are manually utilizing this regex for their own purposes
        self.RE_DATE4     = r'''(?P<date>(((?P<day>\d\d?)(?P<suffix>%(daysuffix)s)?(,)?(\s)?)
                                           (?P<mthname>(%(months)s|%(shortmonths)s))\s?
                                           (?P<year>\d\d(\d\d)?)?
                                         )
                                )''' % self.locale.re_values

        # I refactored DATE3 to fix Issue 16 http://code.google.com/p/parsedatetime/issues/detail?id=16
        # I suspect the final line was for a trailing time - but testing shows it's not needed
        # ptc.RE_DATE3     = r'''(?P<date>((?P<mthname>(%(months)s|%(shortmonths)s))\s?
        #                                  ((?P<day>\d\d?)(\s?|%(daysuffix)s|$)+)?
        #                                  (,\s?(?P<year>\d\d(\d\d)?))?))
        #                        (\s?|$|[^0-9a-zA-Z])''' % ptc.locale.re_values
        # self.RE_DATE3     = r'''(?P<date>(
        #                                   (((?P<mthname>(%(months)s|%(shortmonths)s))|
        #                                   ((?P<day>\d\d?)(?P<suffix>%(daysuffix)s)?))(\s)?){1,2}
        #                                   ((,)?(\s)?(?P<year>\d\d(\d\d)?))?
        #                                  )
        #                         )''' % self.locale.re_values

        # still not completely sure of the behavior of the regex and
        # whether it would be best to consume all possible irrelevant characters
        # before the option groups (but within the {1,3} repetition group
        # or inside of each option group, as it currently does
        # however, right now, all tests are passing that were,
        # including fixing the bug of matching a 4-digit year as ddyy
        # when the day is absent from the string
        self.RE_DATE3     = r'''(?P<date>
                                (
                                        (
                                            (^|\s)
                                            (?P<mthname>(%(months)s|%(shortmonths)s)(?![a-zA-Z_]))
                                        ){1}
                                        |
                                        (
                                            (^|\s)
                                            (?P<day>([1-9]|[0-2][0-9]|3[0-1])(?!(\d|pm|am)))
                                            (?P<suffix>%(daysuffix)s)?
                                        ){1}
                                        |
                                        (
                                            ,?\s?
                                            (?P<year>\d\d(\d\d)?)
                                        ){1}
                                ){1,3}
                            )''' % self.locale.re_values

        # not being used in code, but kept in case others are manually utilizing this regex for their own purposes
        self.RE_MONTH     = r'''(\s|^)
                                (?P<month>(
                                           (?P<mthname>(%(months)s|%(shortmonths)s))
                                           (\s?(?P<year>(\d\d\d\d)))?
                                          ))
                                (\s|$|[^0-9a-zA-Z])''' % self.locale.re_values
        self.RE_WEEKDAY   = r'''(\s|^)
                                (?P<weekday>(%(days)s|%(shortdays)s))
                                (\s|$|[^0-9a-zA-Z])''' % self.locale.re_values

        self.RE_NUMBER    = r'(%(numbers)s|\d+)' % self.locale.re_values

        self.RE_SPECIAL   = r'(?P<special>^[%(specials)s]+)\s+' % self.locale.re_values

        self.RE_UNITS     = r'''(?P<qty>(-?(\b(%(numbers)s)\b|\d+)\s*
                                         (?P<units>((\b%(units)s)s?))
                                        ))''' % self.locale.re_values
        self.RE_QUNITS    = r'''(?P<qty>(-?(\b(%(numbers)s)\b|\d+)\s?
                                         (?P<qunits>\b%(qunits)s)
                                         (\s?|,|$)
                                        ))''' % self.locale.re_values

        self.RE_MUNITS    = r'((last|next) (week|month|year))'


        # self.RE_MODIFIER  = r'''(\s?|^)
        #                         (?P<modifier>
        #                          (previous|prev|last|next|eod|eo|(end\sof)|(in\sa)))''' % self.locale.re_values
        # self.RE_MODIFIER2 = r'''(\s?|^)
        #                         (?P<modifier>
        #                          (from|before|after|ago|prior))
        #                         (\s?|$|[^0-9a-zA-Z])''' % self.locale.re_values
        self.RE_MODIFIER  = r'''(\s|^)
                                (?P<modifier>
                                 (%(modifiers-one)s))''' % self.locale.re_values
        self.RE_MODIFIER2 = r'''(\s|^)
                                (?P<modifier>
                                 (%(modifiers-two)s))
                                (\s|$|[^0-9a-zA-Z])''' % self.locale.re_values
        self.RE_TIMEHMS   = r'''(\s?|^)
                                (?P<hours>\d\d?)
                                (?P<tsep>%(timeseperator)s|)
                                (?P<minutes>\d\d)
                                (?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?''' % self.locale.re_values
        self.RE_TIMEHMS2  = r'''(?P<hours>(\d\d?))
                                ((?P<tsep>%(timeseperator)s|)
                                 (?P<minutes>(\d\d?))
                                 (?:(?P=tsep)
                                    (?P<seconds>\d\d?
                                     (?:[.,]\d+)?))?)?''' % self.locale.re_values
        self.RE_NLP_PREFIX = r'''(?P<nlp_prefix>
                                    (on)(\s)+1
                                    |
                                    (at|in)(\s)+2
                                    |
                                    (in)(\s)+3
                                )'''

        if 'meridian' in self.locale.re_values:
            self.RE_TIMEHMS2 += r'\s?(?P<meridian>(%(meridian)s))' % self.locale.re_values

        dateSeps = ''.join(self.locale.dateSep) + '.'

        self.RE_DATE      = r'''(\s?|^)
                                (?P<date>(\d\d?[%s]\d\d?([%s]\d\d(\d\d)?)?))
                                (\s?|$|[^0-9a-zA-Z])''' % (dateSeps, dateSeps)
        self.RE_DATE2     = r'[%s]' % dateSeps
        self.RE_DAY       = r'''(\s|^)
                                (?P<day>(today|tomorrow|yesterday))
                                (\s|$|[^0-9a-zA-Z])''' % self.locale.re_values
        self.RE_DAY2      = r'''(?P<day>\d\d?)(?P<suffix>%(daysuffix)s)?
                             ''' % self.locale.re_values
        # self.RE_TIME      = r'''(\s?|^)
        #                         (?P<time>(morning|breakfast|noon|lunch|evening|midnight|tonight|dinner|night|now))
        #                         (\s?|$|[^0-9a-zA-Z])''' % self.locale.re_values
        self.RE_TIME      = r'''(\s?|^)
                                (?P<time>(%(sources)s))
                                (\s?|$|[^0-9a-zA-Z])''' % self.locale.re_values
        self.RE_REMAINING = r'\s+'

        # Regex for date/time ranges
        self.RE_RTIMEHMS  = r'''(\s?|^)
                                (\d\d?)%(timeseperator)s
                                (\d\d)
                                (%(timeseperator)s(\d\d))?
                                (\s?|$)''' % self.locale.re_values
        self.RE_RTIMEHMS2 = r'''(\s?|^)
                                (\d\d?)
                                (%(timeseperator)s(\d\d?))?
                                (%(timeseperator)s(\d\d?))?''' % self.locale.re_values

        if 'meridian' in self.locale.re_values:
            self.RE_RTIMEHMS2 += r'\s?(%(meridian)s)' % self.locale.re_values

        self.RE_RDATE  = r'(\d+([%s]\d+)+)' % dateSeps
        self.RE_RDATE3 = r'''((((%(months)s))\s?
                              ((\d\d?)
                               (\s?|%(daysuffix)s|$)+)?
                              (,\s?\d\d\d\d)?))''' % self.locale.re_values

        # "06/07/06 - 08/09/06"
        self.DATERNG1 = self.RE_RDATE + r'\s?%(rangeseperator)s\s?' + self.RE_RDATE
        self.DATERNG1 = self.DATERNG1 % self.locale.re_values

        # "march 31 - june 1st, 2006"
        self.DATERNG2 = self.RE_RDATE3 + r'\s?%(rangeseperator)s\s?' + self.RE_RDATE3
        self.DATERNG2 = self.DATERNG2 % self.locale.re_values

        # "march 1rd -13th"
        self.DATERNG3 = self.RE_RDATE3 + r'\s?%(rangeseperator)s\s?(\d\d?)\s?(rd|st|nd|th)?'
        self.DATERNG3 = self.DATERNG3 % self.locale.re_values

        # "4:00:55 pm - 5:90:44 am", '4p-5p'
        self.TIMERNG1 = self.RE_RTIMEHMS2 + r'\s?%(rangeseperator)s\s?' + self.RE_RTIMEHMS2
        self.TIMERNG1 = self.TIMERNG1 % self.locale.re_values

        # "4:00 - 5:90 ", "4:55:55-3:44:55"
        self.TIMERNG2 = self.RE_RTIMEHMS + r'\s?%(rangeseperator)s\s?' + self.RE_RTIMEHMS
        self.TIMERNG2 = self.TIMERNG2 % self.locale.re_values

        # "4-5pm "
        self.TIMERNG3 = r'\d\d?\s?%(rangeseperator)s\s?' + self.RE_RTIMEHMS2
        self.TIMERNG3 = self.TIMERNG3 % self.locale.re_values

        # "4:30-5pm "
        self.TIMERNG4 = self.RE_RTIMEHMS + r'\s?%(rangeseperator)s\s?' + self.RE_RTIMEHMS2
        self.TIMERNG4 = self.TIMERNG4 % self.locale.re_values

        self.re_option = re.IGNORECASE + re.VERBOSE
        self.cre_source = { 'CRE_SPECIAL':   self.RE_SPECIAL,
                            'CRE_NUMBER':    self.RE_NUMBER,
                            'CRE_UNITS':     self.RE_UNITS,
                            'CRE_QUNITS':    self.RE_QUNITS,
                            'CRE_MUNITS':    self.RE_MUNITS,
                            'CRE_MODIFIER':  self.RE_MODIFIER,
                            'CRE_MODIFIER2': self.RE_MODIFIER2,
                            'CRE_TIMEHMS':   self.RE_TIMEHMS,
                            'CRE_TIMEHMS2':  self.RE_TIMEHMS2,
                            'CRE_DATE':      self.RE_DATE,
                            'CRE_DATE2':     self.RE_DATE2,
                            'CRE_DATE3':     self.RE_DATE3,
                            'CRE_DATE4':     self.RE_DATE4,
                            'CRE_DATE5':     self.RE_DATE5,
                            'CRE_MONTH':     self.RE_MONTH,
                            'CRE_WEEKDAY':   self.RE_WEEKDAY,
                            'CRE_DAY':       self.RE_DAY,
                            'CRE_DAY2':      self.RE_DAY2,
                            'CRE_TIME':      self.RE_TIME,
                            'CRE_REMAINING': self.RE_REMAINING,
                            'CRE_RTIMEHMS':  self.RE_RTIMEHMS,
                            'CRE_RTIMEHMS2': self.RE_RTIMEHMS2,
                            'CRE_RDATE':     self.RE_RDATE,
                            'CRE_RDATE3':    self.RE_RDATE3,
                            'CRE_TIMERNG1':  self.TIMERNG1,
                            'CRE_TIMERNG2':  self.TIMERNG2,
                            'CRE_TIMERNG3':  self.TIMERNG3,
                            'CRE_TIMERNG4':  self.TIMERNG4,
                            'CRE_DATERNG1':  self.DATERNG1,
                            'CRE_DATERNG2':  self.DATERNG2,
                            'CRE_DATERNG3':  self.DATERNG3,
                            'CRE_NLP_PREFIX': self.RE_NLP_PREFIX,
                          }
        self.cre_keys = list(self.cre_source.keys())

    def __getattr__(self, name):
        if name in self.cre_keys:
            value = re.compile(self.cre_source[name], self.re_option)
            setattr(self, name, value)
            return value
        elif name in self.locale.locale_keys:
            return getattr(self.locale, name)
        else:
            raise AttributeError(name)

    def daysInMonth(self, month, year):
        """
        Take the given month (1-12) and a given year (4 digit) return
        the number of days in the month adjusting for leap year as needed
        """
        result = None
        log.debug('daysInMonth(%s, %s)' % (month, year))
        if month > 0 and month <= 12:
            result = self._DaysInMonthList[month - 1]

            if month == 2:
                if year in self._leapYears:
                    result += 1
                else:
                    if calendar.isleap(year):
                        self._leapYears.append(year)
                        result += 1

        return result

    def buildSources(self, sourceTime=None):
        """
        Return a dictionary of date/time tuples based on the keys
        found in self.re_sources.

        The current time is used as the default and any specified
        item found in self.re_sources is inserted into the value
        and the generated dictionary is returned.
        """
        if sourceTime is None:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = time.localtime()
        else:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

        sources  = {}
        defaults = { 'yr': yr, 'mth': mth, 'dy':  dy,
                     'hr': hr, 'mn':  mn,  'sec': sec, }

        for item in self.re_sources:
            values = {}
            source = self.re_sources[item]

            for key in list(defaults.keys()):
                if key in source:
                    values[key] = source[key]
                else:
                    values[key] = defaults[key]

            sources[item] = ( values['yr'], values['mth'], values['dy'],
                              values['hr'], values['mn'], values['sec'], wd, yd, isdst )

        return sources
