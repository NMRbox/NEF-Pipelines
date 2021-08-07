import functools
import operator
from collections import Counter
from dataclasses import dataclass, field
from textwrap import dedent
from typing import List, Union, TextIO, Dict, Callable, Optional, Tuple

from tabulate import tabulate

from lib.sequence_lib import translate_1_to_3, TRANSLATIONS_1_3
from lib.structures import SequenceResidue, LineInfo
from lib.util import is_int

# known field types
DATA = 'DATA'
REMARK = 'REMARK'
VALUES = '__VALUES__'
SEQUENCE = 'SEQUENCE'
FORMAT = 'FORMAT'
VARS = 'VARS'
COMMENT = '#'
NULLSTRING = 'NULLSTRING'
NULLVALUE = 'NULLVALUE'


@dataclass(frozen = True)
class DbRecord:
    index: int
    type: str
    values: Tuple[Union[int, str, float]]


@dataclass
class DbFile:
    name: str = 'unknown'
    records: List[DbRecord] = field(default_factory=list)


def _raise_data_before_format(line_info):
    msg = f"""\
            bad nmrpipe db file, data seen before VAR and FORMAT 
            file: {line_info.file_name}' 
            line no: {line_info.line_no}
            line: {line_info.line}
            """
    msg = dedent(msg)
    raise DataBeforeFormat(msg)


def read_db_file_records(file_h: TextIO, file_name: str = 'unknown') -> DbFile:

    """
    Read from NmrPipe (NIH) tab/gdb-file
    Args:
        file_h (TextIO): a file like object
        file_name (str): the name of the file being read (for debugging)

    Returns DbFile:
        a list of all the records in the fiule
    """


    records: List[DbRecord] = []
    column_names = None
    column_formats = None
    record_count = Counter()

    for line_index, line in enumerate(file_h):
        line_info = LineInfo(file_name, line_index+1, line)
        line = line.strip()

        raw_fields = line.strip().split()

        if len(line) == 0:
            continue

        record_type = raw_fields[0]
        record_count[record_type] += 1

        if len(raw_fields) > 1:
            fields = raw_fields[1:]
        else:
            fields = raw_fields

        handled = False

        if record_type == 'VARS':
            if record_count[record_type] != 1:
                _raise_multiple('VARS', line_info)

            column_names = fields
            records.append(DbRecord(record_count[record_type], record_type, column_names))
            handled = True

        if record_type == 'FORMAT':
            column_formats = _formats_to_constructors(fields, line_info)

            if record_count[record_type] != 1:
                _raise_multiple('FORMAT', line_info)

            _check_var_and_format_count_raise_if_bad(column_names, column_formats, line_info)

            records.append(DbRecord(record_count[record_type], record_type, fields))
            handled = True

        if record_type in ('REMARK', '#'):
            records.append(DbRecord(record_count[record_type], record_type, line))
            handled = True

        if is_int(record_type):
            if column_names and column_formats:
                record_count['__VALUES__'] += 1

                del record_count[record_type]

                values = _build_values_or_raise(column_formats, column_names, fields, line_info)

                record = DbRecord(record_count['__VALUES__'], '__VALUES__', values)
                records.append(record)

                handled = True



            else:
                _raise_data_before_format(line_info)

        if not handled:
            records.append(DbRecord(record_count[record_type], record_type, fields))


    return DbFile(file_name, records)

def _find_nth(haystack, needle, n):
    # https://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string/41626399#41626399
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def _build_values_or_raise(column_formats, column_names, fields, line_info):
    non_index_column_formats = _check_column_count_raise_if_bad(column_formats, column_names, line_info)
    result = []
    field_count = Counter()
    for column_no, (raw_field, constructor) in enumerate(zip(fields, non_index_column_formats)):
        try:
            field_count[raw_field] += 1
            value = constructor(raw_field)

        except Exception:
            absolute_column = _find_nth(line_info.line, raw_field, field_count[raw_field])
            msg = f"""
                    Couldn't convert {raw_field} to type {_constructor_to_name(constructor)}
                    file: {line_info.file_name}
                    line no: {line_info.line_no}
                    column: {column_no + 1}
                    line: {line_info.line.rstrip()}
                          {' ' * absolute_column + '^'}
                """
            msg = dedent(msg)
            raise BadFieldFormat(msg)
        result.append(value)
    return result


def _raise_multiple(format_str, line_info):
    msg = f"""\
                bad NMRPipe db file, multiple {format_str} statements found
                file: {line_info.file_name}
                line no: {line_info.line_no}
                line: {line_info.line}
                """
    msg = dedent(msg)

    if format_str == 'VARS':
        raise MultipleVars(msg)
    elif format_str == 'FORMAT':
        raise MultipleFormat(msg)



def _check_var_and_format_count_raise_if_bad(column_names, column_formats, line_info):
    if column_names is None:
        msg = f'''\
               no column names defined by a VARS line when FORMAT line read
               file: {line_info.file_name}
               line no: {line_info.line_no}
               line: {line_info.line}'''
        msg = dedent(msg)
        raise NoVarsLine(msg)

    num_formats = len(column_names)
    num_column_names = len(column_formats)
    if num_formats != num_column_names:
        msg = f'''\
                  number of column names and formats must agree
                  got {num_column_names} column names and {num_formats} formats
                  file: {line_info.file_name}
                  line no: {line_info.line_no}
                  line: {line_info.line}
               '''
        msg = dedent(msg)

        raise WrongColumnCount(msg)


def _check_column_count_raise_if_bad(column_formats, column_names, line_info):
    non_index_column_formats = column_formats[1:]
    raw_fields = line_info.line.split()
    num_fields = len(raw_fields)
    num_columns = len(non_index_column_formats) + 1

    missing_fields = ['*'] * abs(num_fields - num_columns)
    raw_fields = [*raw_fields, *missing_fields]

    if num_fields != num_columns:
        column_formats = _constructor_names(column_formats)
        tab = [
            column_names,
            column_formats,
            raw_fields,

        ]
        tabulated = tabulate(tab, tablefmt='plain')
        msg = f"""\
                number fields ({num_fields + 1}) doesn't not match number of columns ({num_columns + 1})
                
                expected 
                %s
                
                missing fields marked with *
                
                file: {line_info.file_name}
                line no: {line_info.line_no}
                line: {line_info.line}
                
            """
        msg = dedent(msg)
        msg = msg % tabulated
        raise WrongColumnCount(msg)
    return non_index_column_formats


def _formats_to_constructors(formats, line_info):
    result = []

    field_counter = Counter()
    for column_index, field_format in enumerate(formats):
        field_counter[field_format] += 1
        field_format = field_format.strip()
        field_format = field_format[-1]

        if field_format == 'd':
            result.append(int)
        elif field_format == 'f':
            result.append(float)
        elif field_format == 's':
            result.append(str)
        elif field_format == 'e':
            result.append(float)
        else:
            format_column = _find_nth(line_info.line, field_format, field_counter[field_format])
            msg = f'''
                unexpected format {field_format} at index {column_index+1}, expected formats are s, d, e, f (string, integer, scientific(float), float)
                file: {line_info.file_name}
                line no: {line_info.line_no}
                line: {line_info.line}
                      {' ' * format_column + '^'}
                
            '''
            raise BadFieldFormat(msg)
    return result


OptionDbRecordPredicate = Optional[Callable[[DbRecord], bool]]


def select_records(gdb: DbFile, record_type: str, predicate: OptionDbRecordPredicate = None) -> List[DbRecord]:
    """
    Select records from a gdb file by type and predicate
    Args:
        gdb (DbFile): gdb/tab file
        type (str): the type of the record #, REMARK, __VALUE__ etc
        predicate (OptionDbRecordPredicate): an optional test to apply to the record

    Returns List[DbRecord]:
        the selected gdb/tab records
    """
    result = [record for record in gdb.records if record.type == record_type]
    if predicate:
        result = [record for record in result if predicate(record)]
    return result



def gdb_to_3let_sequence(gdb: DbFile, translations: Dict[str, str] = TRANSLATIONS_1_3) -> List[SequenceResidue]:
    data_records = [record for record in gdb.records if record.type == 'DATA']
    sequence_records = [record.values[1:] for record in data_records if record.values[0] == 'SEQUENCE']

    flattened_records = functools.reduce(operator.iconcat, sequence_records, [])
    sequence_string = ''.join(flattened_records)

    return translate_1_to_3(sequence_string, translations)


def _constructor_to_name(constructor):
    constructors_to_type_name = {
        int: 'int',
        float: 'float',
        str: 'str'
    }

    return constructors_to_type_name[constructor]


def _constructor_names(constructors):

    result = []
    for constructor in constructors:
        result.append(_constructor_to_name(constructor))

    return result


class BadNmrPipeFile(Exception):
    """
    Base exception for bad nmr pipe files, this is the one to catch!
    """
    pass


class BadFieldFormat(BadNmrPipeFile):
    """
    One of the fields int he file has a bad format
    """
    pass


class WrongColumnCount(BadNmrPipeFile):
    """
    The number of columns in the VARS FORMAT or data lines disagree in their count
    """
    pass


class NoVarsLine(BadNmrPipeFile):
    """
    Tried to read data without a VARS line
    """
    pass


class NoFormatLine(BadNmrPipeFile):
    """
    Tried to read data without a FORMAT line
    """
    pass


class MultipleVars(BadNmrPipeFile):
    """
    Multiple VARS lines detected
    """
    pass


class MultipleFormat(BadNmrPipeFile):
    """
    Multiple FORMAT lines detected
    """
    pass


class DataBeforeFormat(BadNmrPipeFile):
    """
    Data seen before VARS and FORMAT lines detected
    """
    pass
