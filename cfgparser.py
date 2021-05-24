# -----------------------------------------------------------------------------
# cfgparser -- extended subclass of the stdlib ConfigParser
# Copyright 2014, Ensoft Ltd
# -----------------------------------------------------------------------------

try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import re
import collections
import ast

"""
The CfgParser module defines an extended subclass of the stdlib ConfigParser.

This extended subclass provides the following extra functionality:

  . Evaluated values, using ast.eval_literal
  . Lists of values can be automatically parsed into lists
  . Section categories: sections can be grouped into categories by naming them
    in the style "category: name". New methods are provided to access the
    categories and sections within them
  . Ease of use helper class for repeated access to a single section

Evaluated values
----------------

A new "geteval" method is provided that uses ast.eval_literal to interpret the
values. It also performs the additional boolean conversion of the ConfigParser
getboolean method. If the value cannot be converted in this way, then the
string is returned unchanged.

Lists of values
---------------

Some values actually describe a list of values. CfgParser.getlist can
automatically convert such values into a list. It recognises newlines and/or
commas as separators between individual values, and has an optional keyword
argument to also evaluate each item in the list as "geteval" does.

Section Categories
------------------

If a section name contains a single colon, then the left part is considered
a category name. All sections with the same category can be accessed using
the "categories" method. All access methods also acquire an additional
"category" keyword argument, which can be used to access the section without
needing to worry about the exact spacing/capitalisation used in the config
file.

ConfigSection helper class
--------------------------

In order to avoid needing to repeatedly pass the section argument to get or
related methods, a new "section" method returns an instance of a new
ConfigSection helper class. This class exports methods with the same names
as each method on CfgParser that takes a "section" argument, but without
that argument.

"""

_EMPTY = object()

class CfgParser(configparser.ConfigParser):
    SPLITTER = re.compile("[,\n]")

    def __init__(self, defaults={}, dict_type=collections.OrderedDict,
                 allow_no_value=False):
        configparser.ConfigParser.__init__(self, defaults=defaults,
                                           dict_type=dict_type,
                                           allow_no_value=allow_no_value)
        self._categories = None

    # Helper class to make access to a given section easier

    class ConfigSection(object):
        def __init__(self, cfg, section):
            self.cfg = cfg
            self.section = section
        def options(self):
            return self.cfg.options(self.section)
        def has_option(self, option):
            return self.cfg.has_option(self.section, option)
        def get(self, option, raw=False, vars=None, evaluate=False,
                default=_EMPTY):
            return self.cfg.get(self.section, option, raw=raw, vars=vars,
                                evaluate=evaluate, default=default)
        def getlist(self, option, evaluate=False, default=_EMPTY):
            return self.cfg.getlist(self.section, option, evaluate=evaluate,
                                    default=default)
        def geteval(self, option, default=_EMPTY):
            return self.cfg.geteval(self.section, option, default=default)
        def items(self):
            return self.cfg.items(self.section)

    def section(self, section, category=None):
        if category is None:
            return self.ConfigSection(self, section)
        else:
            self._parse_categories()
            return self.ConfigSection(self,
                      self._categories[self.optionxform(category)][section])

    # Support for Categories

    def _parse_categories(self):
        if self._categories is not None:
            return
        self._categories = collections.OrderedDict()
        for fullname in self.sections():
            section = self.optionxform(fullname).strip()
            if section.count(':') == 1:
                cat, name = map(str.strip, section.split(':'))
                secs = self._categories.setdefault(cat,
                                                   collections.OrderedDict())
                secs[name] = fullname

    def categories(self):
        self._parse_categories()
        return self._categories.keys()

    def sections(self, category=None):
        if category is None:
            return configparser.ConfigParser.sections(self)
        else:
            self._parse_categories()
            return self._categories[self.optionxform(category)].keys()

    def has_section(self, section, category=None):
        if category is None:
            return configparser.ConfigParser.has_section(self, section)
        else:
            self._parse_categories()
            return (self.optionxform(category) in self._categories and
                    section in self._categories[self.optionxform(category)])

    def options(self, section, category=None):
        if category is None:
            return configparser.ConfigParser.options(self, section)
        else:
            self._parse_categories()
            return configparser.ConfigParser.options(self,
                       self._categories[self.optionxform(category)]
                                       [self.optionxform(section)])

    def has_option(self, section, option, category=None):
        if category is None:
            return configparser.ConfigParser.has_option(self, section, option)
        else:
            self._parse_categories()
            return configparser.ConfigParser.has_option(self,
                        self._categories[self.optionxform(category)]
                                        [self.optionxform(section)], option)

    def items(self, section, category=None):
        if category is None:
            return configparser.ConfigParser.items(self, section)
        else:
            self._parse_categories()
            return configparser.ConfigParser.items(self,
                            self._categories[self.optionxform(category)]
                                            [self.optionxform(section)])

    def get(self, section, option, raw=False, vars={}, category=None,
            evaluate=False, default=_EMPTY):
        if category is not None:
            self._parse_categories()
            try:
                section = (self._categories[self.optionxform(category)]
                                           [self.optionxform(section)])
            except KeyError:
                if default != _EMPTY:
                    return default
                raise configparser.NoSectionError
        try:
            val = configparser.ConfigParser.get(self, section, option,
                                                raw=raw, vars=vars)
        except configparser.NoOptionError:
            if default != _EMPTY:
                return default
            raise

        if evaluate:
            val = self._evaluate(val)
        return val

    # Support for evaluated values and lists of values

    @staticmethod
    def _evaluate(val):
        try:
            return ast.literal_eval(val)
        except Exception:
            if val.lower() in {'no', 'false', 'off'}:
                val = False
            elif val.lower() in {'yes', 'true', 'on'}:
                val = True
            return val

    def getlist(self, section, option, evaluate=False, category=None,
                default=_EMPTY):
        try:
            val = self.get(section, option, category=category)
        except configparser.NoOptionError:
            if default is not _EMPTY:
                return default
            raise
        lst = [s.strip() for s in self.SPLITTER.split(val) if s.strip()]
        if evaluate:
            return [self._evaluate(i) for i in lst]
        else:
            return lst

    def geteval(self, section, option, category=None, default=_EMPTY):
        return self.get(section, option, category=category, evaluate=True,
                        default=default)
