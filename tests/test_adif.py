"""ADI reading and writing, against ADIF 3.1.7's own examples and the inputs that broke
the fleet's six parsers on 2026-10-29."""

from __future__ import annotations

import pytest

from qso_graph_lib.adif import iter_records, read, write

# ADIF 3.1.7, IV.A.7 "Sample ADI File", as printed in the specification.
SPEC_SAMPLE = """Generated on 2011-11-22 at 02:15:23Z for WN4AZY
<adif_ver:5>3.0.5
<programid:7>monolog
<USERDEF1:3:N>EPC
<USERDEF2:19:E>SweaterSize,{S,M,L}
<USERDEF3:15:N>ShoeSize,{5:20}
<EOH>
<qso_date:8>19900620
<time_on:4>1523
<call:5>VK9NS
<band:3>20M
<mode:4>RTTY
<sweatersize:1>M
<shoesize:2>11
<app_monolog_compression:3>off
<eor>
<qso_date:8>20101022
<time_on:4>0111
<call:5>ON4UN
<band:3>40M
<mode:3>PSK
<submode:5>PSK63
<epc:5>32123
<app_monolog_compression:3>off
<eor>
"""


def test_the_specification_s_sample_file():
    doc = read(SPEC_SAMPLE)
    assert doc.problems == []
    assert doc.header == {
        "ADIF_VER": "3.0.5", "PROGRAMID": "monolog", "USERDEF1": "EPC",
        "USERDEF2": "SweaterSize,{S,M,L}", "USERDEF3": "ShoeSize,{5:20}",
    }
    assert doc.header_text.startswith("Generated on 2011-11-22")
    assert [r.fields["CALL"] for r in doc.records] == ["VK9NS", "ON4UN"]
    assert doc.records[1].fields["SUBMODE"] == "PSK63"
    assert doc.records[0].fields["APP_MONOLOG_COMPRESSION"] == "off"


@pytest.mark.parametrize("text", [
    # IV.A.6: both of the specification's ways of writing the WN4AZY record.
    "<call:6>WN4AZY<band:3>20M<mode:4>RTTY<qso_date:8>19960513<time_on:4>1305<eor>",
    "<qso_date:8>19960513\n<time_on:4>1305\n<call:6>WN4AZY\n<band:3>20M\n<mode:4>RTTY\n<eor>",
])
def test_the_specification_s_two_forms_of_one_record(text):
    doc = read(text)
    assert doc.problems == [] and doc.header == {}
    assert doc.records[0].fields == {
        "CALL": "WN4AZY", "BAND": "20M", "MODE": "RTTY", "QSO_DATE": "19960513",
        "TIME_ON": "1305",
    }


def test_type_indicators_are_kept_and_names_are_case_independent():
    rec = read("<Call:5:s>K1ABC<FREQ:6:N>14.074<eor>").records[0]
    assert rec.fields == {"CALL": "K1ABC", "FREQ": "14.074"}
    assert rec.types == {"CALL": "S", "FREQ": "N"}


def test_the_data_is_exactly_its_length_and_is_not_trimmed():
    rec = read("<COMMENT:7>  hi   <EOR>").records[0]
    assert rec.fields["COMMENT"] == "  hi   "


def test_text_outside_data_specifiers_is_ignored():
    rec = read("<CALL:5>K1ABC some note <BAND:3>20m // and this <EOR>").records[0]
    assert rec.fields == {"CALL": "K1ABC", "BAND": "20m"}


def test_a_zero_length_field():
    fields = read("<NAME:0><CALL:5>K1ABC<EOR>").records[0].fields
    assert fields == {"NAME": "", "CALL": "K1ABC"}


# --- the inputs that broke the fleet's parsers -----------------------------------------

def test_a_value_containing_angle_brackets_is_kept():
    """qsp-client's reader dropped this field."""
    rec = read("<CALL:5>K1ABC<COMMENT:9>a<b>c<d>e<EOR>").records[0]
    assert rec.fields["COMMENT"] == "a<b>c<d>e"


def test_a_value_containing_a_literal_eor_is_kept_and_counts_one_record():
    doc = read("<CALL:5>K1ABC<COMMENT:7>x<eor>y<EOR>")
    assert len(doc.records) == 1 and doc.records[0].fields["COMMENT"] == "x<eor>y"


def test_header_fields_are_never_a_qso_s_fields():
    """eqsl-mcp merged ADIF_VER and PROGRAMID into the first QSO, trailing spaces kept."""
    doc = read("Header text <ADIF_VER:5>3.1.7 <PROGRAMID:4>Test <EOH><CALL:5>K1ABC<EOR>")
    assert doc.header == {"ADIF_VER": "3.1.7", "PROGRAMID": "Test"}
    assert doc.records[0].fields == {"CALL": "K1ABC"}


def test_a_non_ascii_value_does_not_cost_the_fields_after_it():
    """qsp-client's reader kept only CALL from this record."""
    doc = read("<CALL:5>DL1AA<NAME:6>Jürgen<QTH:6>Berlin<EOR>")
    assert doc.records[0].fields == {"CALL": "DL1AA", "NAME": "Jürgen", "QTH": "Berlin"}
    assert doc.problems == []


def test_a_length_counted_in_bytes_is_repaired_and_reported():
    """Five of six parsers lost QTH and left '<' in NAME."""
    doc = read("<CALL:5>DL1AA<NAME:7>Jürgen<QTH:6>Berlin<EOR>")
    assert doc.records[0].fields == {"CALL": "DL1AA", "NAME": "Jürgen", "QTH": "Berlin"}
    assert len(doc.problems) == 1 and "UTF-8 bytes" in doc.problems[0].message


def test_a_length_running_past_the_next_tag_does_not_swallow_the_record_end():
    """Five of six read 'K1ABC<EOR' and ran the next record into this one."""
    doc = read("<CALL:9>K1ABC<EOR><CALL:5>W9XYZ<EOR>")
    assert [r.fields for r in doc.records] == [{"CALL": "K1ABC"}, {"CALL": "W9XYZ"}]
    assert "runs past the next tag" in doc.problems[0].message


def test_a_length_running_past_the_end_is_clamped():
    doc = read("<CALL:50>K1ABC")
    assert doc.records[0].fields == {"CALL": "K1ABC"}
    assert any("past the end" in p.message for p in doc.problems)


def test_a_header_that_starts_with_angle_bracket_is_read_as_a_header_and_reported():
    """ADIF says a file starting with '<' has no Header; qrz-mcp's writer made such files."""
    doc = read("<ADIF_VER:5>3.1.7<PROGRAMID:4>Test<EOH><CALL:5>K1ABC<EOR>")
    assert doc.header == {"ADIF_VER": "3.1.7", "PROGRAMID": "Test"}
    assert doc.records[0].fields == {"CALL": "K1ABC"}
    assert "no Header" in doc.problems[0].message


def test_an_eoh_after_a_record_does_not_make_a_header():
    doc = read("<CALL:5>K1ABC<EOR><EOH><CALL:5>W9XYZ<EOR>")
    assert doc.header == {} and len(doc.records) == 2


def test_a_last_record_without_eor_is_kept_and_reported():
    doc = read("<CALL:5>K1ABC<EOR><CALL:5>W9XYZ")
    assert [r.fields["CALL"] for r in doc.records] == ["K1ABC", "W9XYZ"]
    assert "no <EOR>" in doc.problems[-1].message


def test_a_byte_order_mark_is_not_a_header():
    doc = read("﻿<CALL:5>K1ABC<EOR>")
    assert doc.header == {} and doc.records[0].fields == {"CALL": "K1ABC"}


def test_a_huge_declared_length_is_not_a_data_specifier():
    # Nine digits at most: a forged length cannot become an enormous integer.
    assert read("<CALL:9999999999>K1ABC<EOR>").records == []


def test_record_positions_cover_the_record_text():
    text = "hdr<EOH>\n<CALL:5>K1ABC<EOR>\n<CALL:5>W9XYZ<EOR>"
    recs = read(text).records
    assert [text[r.start:r.end] for r in recs] == ["<CALL:5>K1ABC<EOR>", "<CALL:5>W9XYZ<EOR>"]


# --- QRZ's escaped markers ------------------------------------------------------------

def test_escaped_markers_are_read_when_asked_and_values_are_left_as_sent():
    text = "&lt;call:5&gt;K1ABC&lt;comment:9&gt;a &lt; b!&lt;eor&gt;"
    assert read(text).records == []  # not without asking
    rec = read(text, escaped_markers=True).records[0]
    assert rec.fields == {"CALL": "K1ABC", "COMMENT": "a &lt; b!"}


# --- streaming ------------------------------------------------------------------------

def test_iter_records_matches_read_and_collects_the_same_problems():
    text = SPEC_SAMPLE + "<CALL:9>K1ABC<EOR>"
    found: list = []
    streamed = [r.fields for r in iter_records(text, problems=found)]
    doc = read(text)
    assert streamed == [r.fields for r in doc.records]
    assert found == doc.problems


# --- writing --------------------------------------------------------------------------

def test_write_round_trips_values_that_look_like_structure():
    records = [{"CALL": "K1ABC", "NAME": "Jürgen", "COMMENT": "x<eor>y <b>"}]
    text = write(records, header={"ADIF_VER": "3.1.7", "PROGRAMID": "test"})
    doc = read(text)
    assert doc.problems == []
    assert doc.header == {"ADIF_VER": "3.1.7", "PROGRAMID": "test"}
    assert doc.records[0].fields == records[0]


def test_a_written_header_never_begins_with_an_angle_bracket():
    assert write([], header={"ADIF_VER": "3.1.7"})[0] != "<"
    with pytest.raises(ValueError):
        write([], header={}, header_text="<oops>")


def test_without_a_header_records_are_one_per_line():
    assert write([{"CALL": "K1ABC"}, {"CALL": "W9XYZ"}]) == (
        "<CALL:5>K1ABC<EOR>\n<CALL:5>W9XYZ<EOR>\n")


@pytest.mark.parametrize(
    "name", ["", "BAD:NAME", "A<B", "A>B", "A,B", "A{B}", " LEAD", "TAB\tX"])
def test_a_name_adif_does_not_allow_is_refused(name):
    with pytest.raises(ValueError):
        write([{name: "x"}])


def test_a_value_that_is_not_text_is_refused():
    with pytest.raises(TypeError):
        write([{"FREQ": 14.074}])  # type: ignore[dict-item]
