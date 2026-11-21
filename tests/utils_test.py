import unittest

import gspread
import gspread.utils as utils
from gspread.exceptions import InvalidInputValue, NoFeasibleRegion


class UtilsTest(unittest.TestCase):
    def test_extract_id_from_url(self):
        url_id_list = [
            # New-style url
            (
                "https://docs.google.com/spreadsheets/d/"
                "1qpyC0X3A0MwQoFDE8p-Bll4hps/edit#gid=0",
                "1qpyC0X3A0MwQoFDE8p-Bll4hps",
            ),
            (
                "https://docs.google.com/spreadsheets/d/"
                "1qpyC0X3A0MwQoFDE8p-Bll4hps/edit",
                "1qpyC0X3A0MwQoFDE8p-Bll4hps",
            ),
            (
                "https://docs.google.com/spreadsheets/d/" "1qpyC0X3A0MwQoFDE8p-Bll4hps",
                "1qpyC0X3A0MwQoFDE8p-Bll4hps",
            ),
            # Old-style url
            (
                "https://docs.google.com/spreadsheet/"
                "ccc?key=1qpyC0X3A0MwQoFDE8p-Bll4hps&usp=drive_web#gid=0",
                "1qpyC0X3A0MwQoFDE8p-Bll4hps",
            ),
        ]

        for url, id in url_id_list:
            self.assertEqual(id, utils.extract_id_from_url(url))

    def test_no_extract_id_from_url(self):
        self.assertRaises(
            gspread.NoValidUrlKeyFound, utils.extract_id_from_url, "http://example.org"
        )

    def test_a1_to_rowcol(self):
        self.assertEqual(utils.a1_to_rowcol("ABC3"), (3, 731))

    def test_rowcol_to_a1(self):
        self.assertEqual(utils.rowcol_to_a1(3, 731), "ABC3")
        self.assertEqual(utils.rowcol_to_a1(1, 104), "CZ1")

    def test_addr_converters(self):
        for row in range(1, 257):
            for col in range(1, 512):
                addr = utils.rowcol_to_a1(row, col)
                r, c = utils.a1_to_rowcol(addr)
                self.assertEqual((row, col), (r, c))

    def test_get_gid(self):
        gid = "od6"
        self.assertEqual(utils.wid_to_gid(gid), "0")
        gid = "osyqnsz"
        self.assertEqual(utils.wid_to_gid(gid), "1751403737")
        gid = "ogsrar0"
        self.assertEqual(utils.wid_to_gid(gid), "1015761654")

    def test_numericise(self):
        self.assertEqual(utils.numericise("faa"), "faa")
        self.assertEqual(utils.numericise("3"), 3)
        self.assertEqual(utils.numericise("3_2"), "3_2")
        self.assertEqual(
            utils.numericise("3_2", allow_underscores_in_numeric_literals=False), "3_2"
        )
        self.assertEqual(
            utils.numericise("3_2", allow_underscores_in_numeric_literals=True), 32
        )
        self.assertEqual(utils.numericise("3.1"), 3.1)
        self.assertEqual(utils.numericise("", empty2zero=True), 0)
        self.assertEqual(utils.numericise("", empty2zero=False), "")
        self.assertEqual(utils.numericise("", default_blank=None), None)
        self.assertEqual(utils.numericise("", default_blank="foo"), "foo")
        self.assertEqual(utils.numericise(""), "")
        self.assertEqual(utils.numericise(None), None)

        # test numericise_all
        inputs = ["1", "2", "3"]
        expected = [1, 2, 3]
        self.assertEqual(utils.numericise_all(inputs), expected)

        # skip non digit values
        inputs + ["a"]
        expected + ["a"]
        self.assertEqual(utils.numericise_all(inputs), expected)

        # skip ignored columns
        inputs + ["5", "5"]
        expected + ["5", 5]
        self.assertEqual(utils.numericise_all(inputs, ignore=[5]), expected)

        # provide explicit `None` as ignored list
        self.assertEqual(utils.numericise_all(inputs, ignore=None), expected)

    def test_a1_to_grid_range_simple(self):
        expected_single_dimension = {
            "startRowIndex": 0,
            "endRowIndex": 10,
            "startColumnIndex": 0,
            "endColumnIndex": 1,
        }
        actual_single_dimension = utils.a1_range_to_grid_range("A1:A10")

        expected_two_dimensional = {
            "startRowIndex": 2,
            "endRowIndex": 4,
            "startColumnIndex": 0,
            "endColumnIndex": 2,
        }
        actual_two_dimensional = utils.a1_range_to_grid_range("A3:B4")

        expected_with_sheet_id = {
            "sheetId": 0,
            "startRowIndex": 0,
            "endRowIndex": 10,
            "startColumnIndex": 0,
            "endColumnIndex": 1,
        }
        actual_with_sheet_id = utils.a1_range_to_grid_range("A1:A10", sheet_id=0)

        self.assertEqual(actual_single_dimension, expected_single_dimension)
        self.assertEqual(actual_two_dimensional, expected_two_dimensional)
        self.assertEqual(actual_with_sheet_id, expected_with_sheet_id)

    def test_a1_to_grid_range_unbounded(self):
        expected_unbounded = {
            "startRowIndex": 4,
            "startColumnIndex": 0,
            "endColumnIndex": 2,
        }
        actual_unbounded = utils.a1_range_to_grid_range("A5:B")

        expected_full_columns = {"startColumnIndex": 0, "endColumnIndex": 2}
        actual_full_columns = utils.a1_range_to_grid_range("A:B")

        expected_with_sheet_id = {
            "sheetId": 0,
            "startRowIndex": 4,
            "startColumnIndex": 0,
            "endColumnIndex": 2,
        }
        actual_with_sheet_id = utils.a1_range_to_grid_range("A5:B", sheet_id=0)

        self.assertEqual(actual_unbounded, expected_unbounded)
        self.assertEqual(actual_full_columns, expected_full_columns)
        self.assertEqual(actual_with_sheet_id, expected_with_sheet_id)

    def test_a1_to_grid_range_improper_range(self):
        expected_single_cell = {
            "startRowIndex": 0,
            "endRowIndex": 1,
            "startColumnIndex": 0,
            "endColumnIndex": 1,
        }
        actual_single_cell = utils.a1_range_to_grid_range("A1")

        expected_single_column = {"startColumnIndex": 0, "endColumnIndex": 1}
        actual_single_column = utils.a1_range_to_grid_range("A")

        expected_single_row = {"startRowIndex": 0, "endRowIndex": 1}
        actual_single_row = utils.a1_range_to_grid_range("1")

        expected_with_sheet = {
            "sheetId": 0,
            "startRowIndex": 0,
            "endRowIndex": 1,
            "startColumnIndex": 0,
            "endColumnIndex": 1,
        }
        actual_with_sheet = utils.a1_range_to_grid_range("A1", sheet_id=0)

        self.assertEqual(actual_single_cell, expected_single_cell)
        self.assertEqual(actual_single_column, expected_single_column)
        self.assertEqual(actual_single_row, expected_single_row)
        self.assertEqual(actual_with_sheet, expected_with_sheet)

    def test_a1_to_grid_range_other_directions(self):
        from_top_left = utils.a1_range_to_grid_range("C2:D4")
        from_bottom_right = utils.a1_range_to_grid_range("D4:C2")
        from_top_right = utils.a1_range_to_grid_range("D2:C4")
        from_bottom_left = utils.a1_range_to_grid_range("C4:D2")

        self.assertEqual(from_top_left, from_bottom_right)
        self.assertEqual(from_top_left, from_bottom_left)
        self.assertEqual(from_top_left, from_top_right)

    def test_column_letter_to_index(self):
        # All the input values to test one after an other
        # [0] input value
        # [1] expected return value
        # [2] expected exception to raise
        inputs = [
            ("", None, gspread.exceptions.InvalidInputValue),
            ("A", 1, None),
            ("Z", 26, None),
            ("AA", 27, None),
            ("AAA", 703, None),
            ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 256094574536617744129141650397448476, None),
            ("!@#$%^&*()", None, gspread.exceptions.InvalidInputValue),
        ]

        for label, expected, exception in inputs:
            if exception is not None:
                # assert the exception is raised
                with self.assertRaises(exception):
                    utils.column_letter_to_index(label)
            else:
                # assert the return values is correct
                result = utils.column_letter_to_index(label)
                self.assertEqual(
                    result,
                    expected,
                    "could not convert column letter '{}' to the right value '{}".format(
                        label, expected
                    ),
                )

    def test_combine_merge_values(self):
        sheet_data = [
            [1, None, None, None],
            [None, None, "title", None],
            [None, None, 2, None],
            ["num", "val", None, 0],
        ]
        sheet_metadata = {
            "properties": {"sheetId": 0},
            "merges": [
                {
                    "startRowIndex": 0,
                    "endRowIndex": 2,
                    "startColumnIndex": 0,
                    "endColumnIndex": 2,
                },
                {
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": 2,
                    "endColumnIndex": 4,
                },
                {
                    "startRowIndex": 2,
                    "endRowIndex": 4,
                    "startColumnIndex": 2,
                    "endColumnIndex": 3,
                },
            ],
        }
        expected_combine = [
            [1, 1, None, None],
            [1, 1, "title", "title"],
            [None, None, 2, None],
            ["num", "val", 2, 0],
        ]

        actual_combine = utils.combined_merge_values(sheet_metadata, sheet_data, 0, 0)

        self.assertEqual(actual_combine, expected_combine)

    def test_convert_colors_to_hex_value(self):
        color = {"red": 1, "green": 0.49803922, "blue": 0}
        expected_hex = "#FF7F00"

        # successful convert from colors
        hex = utils.convert_colors_to_hex_value(**color)
        self.assertEqual(hex, expected_hex)

        # successful convert from partial input
        hex = utils.convert_colors_to_hex_value(green=1)
        self.assertEqual(hex, "#00FF00")

        # throw ValueError on color values out of range (0-1)
        with self.assertRaises(ValueError):
            utils.convert_colors_to_hex_value(1.23, 0, -50)

    def test_combine_merge_values_outside_range(self):
        """Make sure that merges outside the range of the sheet are ignored or partially ignored
        see issue #1298
        """
        sheet_data = [
            [1, None, None, None],
            [None, None, "title", None],
            [None, None, 2, None],
            ["num", "val", None, 0],
        ]
        sheet_metadata = {
            "properties": {"sheetId": 0},
            "merges": [
                {
                    "startRowIndex": 7,
                    "endRowIndex": 9,
                    "startColumnIndex": 7,
                    "endColumnIndex": 9,
                },
                {
                    "startRowIndex": 3,
                    "endRowIndex": 5,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2,
                },
            ],
        }
        expected_combine = [
            [1, None, None, None],
            [None, None, "title", None],
            [None, None, 2, None],
            ["num", "val", None, 0],
        ]

        actual_combine = utils.combined_merge_values(sheet_metadata, sheet_data, 0, 0)

        self.assertEqual(actual_combine, expected_combine)

    def test_combine_merge_values_from_centre_of_sheet(self):
        """Make sure that merges start from the right index when the sheet is not at the top left
        see issue #1330
        """
        sheet_data = [
            [1, None, None, None],
            [None, None, "title", None],
            [None, None, 2, None],
            ["num", "val", None, 0],
        ]
        sheet_metadata = {
            "properties": {"sheetId": 0},
            "merges": [
                {
                    "startRowIndex": 0,
                    "endRowIndex": 2,
                    "startColumnIndex": 0,
                    "endColumnIndex": 2,
                },
                {
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": 2,
                    "endColumnIndex": 4,
                },
                {
                    "startRowIndex": 2,
                    "endRowIndex": 4,
                    "startColumnIndex": 2,
                    "endColumnIndex": 3,
                },
            ],
        }
        sheet_data_cropped = [sheet_data[1:] for sheet_data in sheet_data][1:]
        # [None, "title", None],
        # [None, 2, None],
        # ["val", None, 0]
        expected_combined_cropped = [
            [None, "title", "title"],
            [None, 2, None],
            ["val", 2, 0],
        ]

        actual_combine = utils.combined_merge_values(
            sheet_metadata, sheet_data_cropped, start_row_index=1, start_col_index=1
        )

        self.assertEqual(actual_combine, expected_combined_cropped)

    def test_convert_hex_to_color(self):
        hexcolor = "#FF7F00"
        expected_color = {"red": 1, "green": 0.49803922, "blue": 0}

        # successful convert from hex to color
        rgbcolor = utils.convert_hex_to_colors_dict(hexcolor)
        for key, rgbvalue in rgbcolor.items():
            self.assertAlmostEqual(rgbvalue, expected_color[key])

        # successful ignore alpha
        rgbcolor = utils.convert_hex_to_colors_dict(f"{hexcolor}42")
        for key, rgbvalue in rgbcolor.items():
            self.assertAlmostEqual(rgbvalue, expected_color[key])

        # raise ValueError on invalid hex length
        with self.assertRaises(ValueError):
            utils.convert_hex_to_colors_dict("123456abcdef")

        # raise ValueError on invalid hex characters
        with self.assertRaises(ValueError):
            utils.convert_hex_to_colors_dict("axbcde")

    def test_fill_gaps(self):
        """test fill_gaps function"""
        matrix = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
        ]
        expected = [
            [1, 2, 3, 4, "", ""],
            [5, 6, 7, 8, "", ""],
            ["", "", "", "", "", ""],
        ]
        actual = utils.fill_gaps(matrix, 3, 6)

        self.assertEqual(actual, expected)

    def test_fill_gaps_with_value(self):
        """test fill_gaps function"""
        matrix = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
        ]
        expected = [
            [1, 2, 3, 4, "a", "a"],
            [5, 6, 7, 8, "a", "a"],
            ["a", "a", "a", "a", "a", "a"],
        ]
        actual = utils.fill_gaps(matrix, 3, 6, "a")

        self.assertEqual(actual, expected)

        expected = [
            [1, 2, 3, 4, 3, 3],
            [5, 6, 7, 8, 3, 3],
            [3, 3, 3, 3, 3, 3],
        ]
        actual = utils.fill_gaps(matrix, 3, 6, 3)

        self.assertEqual(actual, expected)

    def test_fill_gaps_with_non_square_array(self):
        """test fill_gaps function"""
        matrix = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9],
        ]
        expected = [
            [1, 2, 3, 4, "", "", ""],
            [5, 6, 7, 8, "", "", ""],
            [9, "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
        ]
        actual = utils.fill_gaps(matrix, 4, 7)

        self.assertEqual(actual, expected)

    def test_is_full_a1_notation(self):
        """test is_full_a1_notation function"""
        self.assertTrue(utils.is_full_a1_notation("A1:B2"))
        self.assertTrue(utils.is_full_a1_notation("Sheet1!A1:B2"))
        self.assertTrue(utils.is_full_a1_notation("AZ1:BBY2"))
        self.assertTrue(utils.is_full_a1_notation("AZ142:BBY122"))

        self.assertFalse(utils.is_full_a1_notation("Sheet1"))
        self.assertFalse(utils.is_full_a1_notation("A:B"))
        self.assertFalse(utils.is_full_a1_notation("1:2"))
        self.assertFalse(utils.is_full_a1_notation("1:"))
        self.assertFalse(utils.is_full_a1_notation("A1"))
        self.assertFalse(utils.is_full_a1_notation("A"))
        self.assertFalse(utils.is_full_a1_notation("1"))
        self.assertFalse(utils.is_full_a1_notation(""))

    def test_extract_title_from_range(self):
        """test extract_title_from_range function"""
        # quoted title with spaces
        self.assertEqual(
            utils.extract_title_from_range("'Sheet Name'!A1:Z100"), "Sheet Name"
        )
        # unquoted title
        self.assertEqual(utils.extract_title_from_range("Sheet1!A1:Z100"), "Sheet1")
        # quoted title without range
        self.assertEqual(utils.extract_title_from_range("'Sheet''1'!A1:B2"), "Sheet'1")
        self.assertEqual(
            utils.extract_title_from_range("'Sheet''''1'!A1:B2"), "Sheet''1"
        )
        # invalid input raises exception
        with self.assertRaises(gspread.exceptions.InvalidInputValue):
            utils.extract_title_from_range("no_exclamation_mark")

    def test_get_a1_from_absolute_range(self):
        """test get_a1_from_absolute_range function"""
        self.assertEqual(utils.get_a1_from_absolute_range("'Sheet1'!A1:B2"), "A1:B2")
        self.assertEqual(utils.get_a1_from_absolute_range("'Sheet1'!A1:B"), "A1:B")
        self.assertEqual(utils.get_a1_from_absolute_range("Sheet1!A1:B2"), "A1:B2")
        self.assertEqual(utils.get_a1_from_absolute_range("A1:B2"), "A1:B2")
        self.assertEqual(utils.get_a1_from_absolute_range("A1:B"), "A1:B")
        self.assertEqual(utils.get_a1_from_absolute_range("2"), "2")

    def test_to_records_empty_args(self):
        """Test to_records with empty args"""

        self.assertListEqual(utils.to_records([], []), [])
        self.assertListEqual(utils.to_records([], [[]]), [{}])
        self.assertListEqual(utils.to_records(["a1", "b2"], []), [])
        self.assertListEqual(utils.to_records(["a1", "b2"], [[]]), [{}])
        self.assertListEqual(utils.to_records([], [["a1"]]), [{}])
        self.assertListEqual(utils.to_records([], [["a1"], ["a2"]]), [{}, {}])
        self.assertListEqual(utils.to_records([], [[], ["a2"]]), [{}, {}])

    def test_to_records(self):
        """Test to_records with values"""

        headers = ["HA", "HB", "HC"]
        values = [["A2", "B2", "C2"], ["A3", "B3"], ["", "B4", "C4"]]

        records = utils.to_records(headers, values)

        self.assertEqual(len(values), len(records))

        for i in range(len(records)):
            record = records[i]
            keys = record.keys()

            # Some rows have shorter values ("A3", "B3")
            # so the list of keys is smaller
            # but never bigger than the list of headers
            self.assertLessEqual(len(keys), len(headers))

            # Each resulting key must be part of the given header
            for key in keys:
                self.assertIn(key, headers)

                # given key are unordered
                # but they must match a value from the given input values
                self.assertIn(record[key], values[i])

    def test_find_table_simple(self):
        """Test find table with basic case"""
        values = [
            ["A1", "B1", "C1", "D1"],
            ["", "B2", "C2", "", "E2"],
            ["", "B3", "C3", "D3", "E3"],
            ["A4", "", "C4", "D4", "E4"],
        ]

        table = utils.find_table(
            values,
            "B2",
            utils.TableDirection.table,
        )

        table_max_row_max_column = utils.find_table(
            values,
            "D3",
            utils.TableDirection.table,
        )
        right = utils.find_table(
            values,
            "B2",
            utils.TableDirection.right,
        )
        down = utils.find_table(
            values,
            "B2",
            utils.TableDirection.down,
        )
        single = utils.find_table(values, "D1", utils.TableDirection.table)
        no_values = utils.find_table(values, "A2", utils.TableDirection.table)

        table_values = [
            ["B2", "C2"],
            ["B3", "C3"],
        ]

        for rowindex, row in enumerate(table_values):
            self.assertListEqual(row, table[rowindex])

        table_max_row_max_column_values = [
            ["D3", "E3"],
            ["D4", "E4"],
        ]

        for rowindex, row in enumerate(table_max_row_max_column):
            self.assertListEqual(row, table_max_row_max_column_values[rowindex])

        right_values = [
            ["B2", "C2"],
        ]
        for rowindex, row in enumerate(right_values):
            self.assertListEqual(row, right[rowindex])

        bottom_values = [
            ["B2"],
            ["B3"],
        ]
        for rowindex, row in enumerate(bottom_values):
            self.assertListEqual(row, down[rowindex])

        self.assertEqual(len(single), 1)
        self.assertEqual(len(single[0]), 1)
        self.assertEqual(single[0][0], "D1")
        self.assertEqual(no_values, [])

    def test_find_table_inner_gap(self):
        """Test find table with gap in header"""
        values = [
            ["A1", "B1", "C1", ""],
            ["A2", "", "C2", ""],
            ["A3", "B3", "C3", ""],
            ["", "", "", ""],
        ]
        expected_table = [
            ["A1", "B1", "C1"],
            ["A2", "", "C2"],
            ["A3", "B3", "C3"],
        ]

        table = utils.find_table(
            values,
            "A1",
            utils.TableDirection.table,
        )

        for rowindex, row in enumerate(expected_table):
            self.assertListEqual(row, table[rowindex])

    def test_find_table_first_row_gap(self):
        """Test find table with first cell empty"""
        values = [
            ["A1", "", "C1", ""],
            ["A2", "B2", "C2", ""],
            ["A3", "B3", "C3", ""],
            ["", "", "", ""],
        ]
        expected_table = [
            ["A1"],
            ["A2"],
            ["A3"],
        ]

        table = utils.find_table(
            values,
            "A1",
            utils.TableDirection.table,
        )

        for rowindex, row in enumerate(expected_table):
            self.assertListEqual(row, table[rowindex])

    def test_find_table_first_column_gap(self):
        """Test find table with a gap in first column"""
        values = [
            ["A1", "B1", "C1", ""],
            ["", "B2", "C2", ""],
            ["A3", "B3", "C3", ""],
            ["", "", "", ""],
        ]
        expected_table = [
            ["A1", "B1", "C1"],
        ]

        table = utils.find_table(
            values,
            "A1",
            utils.TableDirection.table,
        )

        for rowindex, row in enumerate(expected_table):
            self.assertListEqual(row, table[rowindex])

    def test_find_table_last_column_gap(self):
        """Test find table with a gap in last column"""
        values = [
            ["A1", "B1", "C1", ""],
            ["A2", "B2", "", ""],
            ["A3", "B3", "C3", ""],
            ["", "", "", ""],
        ]
        expected_table = [
            ["A1", "B1", "C1"],
            ["A2", "B2", ""],
            ["A3", "B3", "C3"],
        ]

        table = utils.find_table(
            values,
            "A1",
            utils.TableDirection.table,
        )

        for rowindex, row in enumerate(expected_table):
            self.assertListEqual(row, table[rowindex])

    def test_find_table_empty_top_left_corner(self):
        """Test find table with an empty top left cell and empty adjacent cells"""

        values = [
            ["", "", "C1", ""],
            ["", "B2", "C2", ""],
            ["", "B3", "C3", ""],
        ]

        table = utils.find_table(values, "A1", utils.TableDirection.table)

        self.assertListEqual(table, [], "resulting table should be empty")


class FindBoundedTableTest(unittest.TestCase):
    """Tests for utils.find_bounded_table."""

    def test_requires_anchors(self):
        values = [["a", "b"], ["c", "d"]]
        with self.assertRaises(NoFeasibleRegion):
            utils.find_bounded_table(values, "A1:B2", max_blanks=0)

    def test_empty_anchor_is_not_feasible(self):
        values = [["a", ""], ["c", "d"]]
        with self.assertRaises(NoFeasibleRegion):
            utils.find_bounded_table(values, "A1:B2", anchors="B1", max_blanks=5)

    def test_anchor_outside_window(self):
        values = [["a", "b"], ["c", "d"]]
        with self.assertRaises(InvalidInputValue):
            utils.find_bounded_table(values, "A1:B2", anchors="C3")

    def test_invalid_window(self):
        values = [["a", "b"], ["c", "d"]]
        for window in ("A1:H", "", "not-a-range", "A1:B2:C3"):
            with self.assertRaises(InvalidInputValue):
                utils.find_bounded_table(values, window, anchors="A1")

    def test_invalid_max_blanks(self):
        values = [["a", "b"], ["c", "d"]]
        for max_blanks in (-1, True, 1.5, "2"):
            with self.assertRaises(InvalidInputValue):
                utils.find_bounded_table(
                    values, "A1:B2", anchors="A1", max_blanks=max_blanks
                )

    def test_grows_while_within_blank_budget(self):
        """A rectangle may include a few empty cells when the budget allows it."""
        values = [
            ["id", "name", "qty"],
            ["1", "bolt", "4"],
            ["2", "", "7"],
            ["", "", ""],
            ["notes", "", ""],
        ]
        # budget 1: the empty cell inside the detail rows is allowed, but
        # taking the "notes" row would need more empty cells.
        result = utils.find_bounded_table(values, "A1:C5", anchors="A1", max_blanks=1)
        self.assertEqual(result.a1_range, "A1:C3")
        self.assertEqual(
            result.values,
            [["id", "name", "qty"], ["1", "bolt", "4"], ["2", "", "7"]],
        )

    def test_zero_budget_stops_on_empty_cell(self):
        values = [
            ["id", "name", "qty"],
            ["1", "bolt", "4"],
            ["2", "", "7"],
        ]
        result = utils.find_bounded_table(values, "A1:C3", anchors="A1", max_blanks=0)
        self.assertEqual(result.a1_range, "A1:C2")

    def test_none_budget_has_no_limit(self):
        values = [
            ["id", "name", "qty"],
            ["1", "bolt", "4"],
            ["2", "", "7"],
            ["", "", ""],
        ]
        result = utils.find_bounded_table(
            values, "A1:C4", anchors="A1", max_blanks=None
        )
        self.assertEqual(result.a1_range, "A1:C4")

    def test_exclude_range_is_avoided(self):
        values = [
            ["id", "name", "qty", "notes"],
            ["1", "bolt", "4", "restock"],
            ["2", "nut", "7", "ok"],
        ]
        result = utils.find_bounded_table(
            values, "A1:D3", anchors="A1", exclude="D1:D3", max_blanks=None
        )
        self.assertEqual(result.a1_range, "A1:C3")

    def test_exclude_unbounded_range_is_clipped_to_window(self):
        values = [
            ["id", "name", "qty", "notes"],
            ["1", "bolt", "4", "restock"],
            ["2", "nut", "7", "ok"],
        ]
        result = utils.find_bounded_table(
            values, "A1:D3", anchors="A1", exclude="D:D", max_blanks=None
        )
        self.assertEqual(result.a1_range, "A1:C3")

    def test_exclude_outside_window_is_ignored(self):
        values = [["a", "b"], ["c", "d"]]
        result = utils.find_bounded_table(
            values, "A1:B2", anchors="A1", exclude="Z1:Z9", max_blanks=None
        )
        self.assertEqual(result.a1_range, "A1:B2")

    def test_exclude_splits_the_window(self):
        values = [
            ["a", "b", "x", "c", "d"],
            ["a", "b", "x", "c", "d"],
        ]
        result = utils.find_bounded_table(
            values, "A1:E2", anchors="A1", exclude="C1:C2", max_blanks=0
        )
        # the left block is 2x2, the right block is 2x1 -> the left wins
        self.assertEqual(result.a1_range, "A1:B2")

    def test_exclude_containing_anchor_is_not_feasible(self):
        values = [["a", "b"], ["c", "d"]]
        with self.assertRaises(NoFeasibleRegion):
            utils.find_bounded_table(values, "A1:B2", anchors="A1", exclude="A1:A1")

    def test_zero_and_false_count_as_filled(self):
        values = [[0, False], ["", ""]]
        result = utils.find_bounded_table(values, "A1:B2", anchors="A1", max_blanks=1)
        self.assertEqual(result.a1_range, "A1:B1")
        self.assertEqual(result.values, [[0, False]])

    def test_missing_cells_count_as_empty(self):
        values = [["a"], ["b"]]
        result = utils.find_bounded_table(
            values, "A1:C2", anchors="A1", max_blanks=None
        )
        self.assertEqual(result.values, [["a", "", ""], ["b", "", ""]])

    def test_multiple_anchors_must_all_be_included(self):
        values = [
            ["a", "", "b"],
            ["c", "d", "e"],
        ]
        result = utils.find_bounded_table(
            values, "A1:C2", anchors=["A1", "C1"], max_blanks=1
        )
        self.assertEqual(result.a1_range, "A1:C2")
        self.assertEqual(result.values, [["a", "", "b"], ["c", "d", "e"]])

    def test_tie_break_fewest_blanks(self):
        # B2:C3 is excluded, leaving A1:C1 (row, one blank) and A1:A3 (column,
        # no blank). Both have area 3 and both start at the anchor A1; the
        # blank-free one wins even though its bottom edge is later.
        values = [
            ["a", "", "c"],
            ["a", "x", "y"],
            ["a", "z", "w"],
        ]
        result = utils.find_bounded_table(
            values,
            "A1:C3",
            anchors="A1",
            exclude="B2:C3",
            max_blanks=None,
        )
        self.assertEqual(result.area, 3)
        self.assertEqual(result.a1_range, "A1:A3")
        self.assertEqual(result.values, [["a"], ["a"], ["a"]])

    def test_tie_break_earliest_coordinates(self):
        # four disjoint filled blocks of the same size, top-left must win
        values = [
            ["a", "a", "", "b", "b"],
            ["a", "a", "", "b", "b"],
            ["", "", "", "", ""],
            ["c", "c", "", "d", "d"],
            ["c", "c", "", "d", "d"],
        ]
        result = utils.find_bounded_table(values, "A1:E5", anchors=["A1"], max_blanks=0)
        self.assertEqual(result.a1_range, "A1:B2")

    def test_window_offset(self):
        # window starts at B2, so the returned range must use sheet coordinates
        values = [
            ["", "a", "b"],
            ["", "c", "d"],
        ]
        result = utils.find_bounded_table(values, "B2:C3", anchors="C2")
        self.assertEqual(result.a1_range, "C2:C3")
        self.assertEqual(result.values, [["a"], ["c"]])

    def test_absolute_window_with_sheet_name(self):
        values = [["a", "b"], ["c", "d"]]
        result = utils.find_bounded_table(values, "Sheet1!A1:B2", anchors="A1")
        self.assertEqual(result.a1_range, "A1:B2")

    def test_result_supports_named_and_tuple_access(self):
        values = [["a", "b"], ["c", "d"]]
        result = utils.find_bounded_table(values, "A1:B2", anchors="A1")

        self.assertIsInstance(result, utils.BoundedTableResult)
        a1_range, matrix = result
        self.assertEqual(a1_range, "A1:B2")
        self.assertEqual(matrix, values)
        self.assertEqual(result.a1_range, "A1:B2")
        self.assertEqual(result.range, "A1:B2")
        self.assertEqual(result.values, values)
        self.assertEqual(result.matrix, values)
        self.assertEqual(result["range"], "A1:B2")
        self.assertEqual(result["values"], values)
        self.assertEqual(result.area, 4)
        self.assertEqual(result.as_dict(), {"range": "A1:B2", "values": values})

    def test_matches_exhaustive_search(self):
        """Cross-check the search against a brute force over four boundaries."""

        pattern = [
            [True, False, False, True],
            [False, False, True, False],
            [True, False, False, False],
        ]
        excluded = [
            [False, False, False, False],
            [False, True, False, False],
            [False, False, False, True],
        ]
        anchors = [(0, 0), (2, 1)]

        for budget in (None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9):
            found = utils._search_bounded(
                pattern,
                excluded,
                anchors,
                float("inf") if budget is None else budget,
            )
            self.assertEqual(
                found,
                _exhaustive_bounded_search(pattern, excluded, anchors, budget),
            )


def _exhaustive_bounded_search(blank, excluded, anchors, budget):
    """Reference implementation, enumerating all four boundaries.

    Only used to cross-check :func:`gspread.utils._search_bounded`.
    """
    rows, cols = len(blank), len(blank[0])
    best = None
    for top in range(rows):
        for bottom in range(top, rows):
            for left in range(cols):
                for right in range(left, cols):
                    rectangle = _evaluate_rectangle(
                        blank, excluded, anchors, budget, top, bottom, left, right
                    )
                    if rectangle is None:
                        continue
                    key, rect = rectangle
                    if best is None or key < best[0]:
                        best = (key, rect)
    return best[1] if best else None


def _evaluate_rectangle(blank, excluded, anchors, budget, top, bottom, left, right):
    """Score one candidate rectangle, or return ``None`` when it is invalid."""
    cells = [
        (row, col) for row in range(top, bottom + 1) for col in range(left, right + 1)
    ]
    if any(excluded[row][col] for row, col in cells):
        return None
    if any(not (top <= row <= bottom and left <= col <= right) for row, col in anchors):
        return None

    blanks = sum(blank[row][col] for row, col in cells)
    if budget is not None and blanks > budget:
        return None

    area = (bottom - top + 1) * (right - left + 1)
    key = (-area, blanks, top, left, bottom, right)
    return key, (top, left, bottom, right, blanks)
