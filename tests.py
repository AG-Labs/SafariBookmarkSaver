import unittest
import testData
import SafariBookmarkSaver
import testData
from unittest.mock import patch, call
import os
import xmlrunner


class TestMethods(unittest.TestCase):
    def test_sortFunction(self):
        result = SafariBookmarkSaver.sort_func(testData.arepas, testData.chickpeaOmelete)
        result2 = SafariBookmarkSaver.sort_func(testData.chickpeaOmelete, testData.arepas)
        result3 = SafariBookmarkSaver.sort_func(testData.arepas, testData.arepas)

        self.assertEqual(result, 1)
        self.assertEqual(result2, -1)
        self.assertEqual(result3, 0)

    def test_full_sort(self):
        sorted_output = SafariBookmarkSaver.sort_output(testData.unsortedData)
        self.assertEqual(sorted_output, testData.sortedData)

    def test_get_json(self):
        json_dict = []
        json_ised_data = SafariBookmarkSaver.get_json(testData.bookmarkData, json_dict)
        self.assertEqual(json_ised_data, testData.bookmarkAsJson)

    def test_recursive_search(self):
        out_dict = {}
        SafariBookmarkSaver.recursive_search(testData.bookmarkData, 'tempString', out_dict)
        self.assertEqual(out_dict, testData.recursiveSearched)

    def test_flatten_dictionary(self):
        out_dict = SafariBookmarkSaver.flatten_dictionary(testData.sortedData)
        self.assertEqual(out_dict, testData.flattened)

    @patch('SafariBookmarkSaver.sample')
    def test_selection(self, mock_sample):
        mock_sample.side_effect = [[{'name': '8 Healthy Salad Dressing Recipes You Should Make at Home', 'url': 'https://wholefully.com/healthy-salad-dressing-recipes/', 'notes': '', 'active': False, 'toggled': True}], [{'name': 'Vegan Chickpea Omelet', 'url': 'https://www.forkandbeans.com/2015/01/15/vegan-chickpea-omelet/', 'notes': '', 'active': False, 'toggled': True}]]

        selected = SafariBookmarkSaver.selection(testData.sortedData, 2, "", 50)

        mock_sample.assert_any_call(unittest.mock.ANY, 1)

        self.assertEqual(mock_sample.call_count, 2)
        self.assertEqual(selected, testData.selected)

    @patch('SafariBookmarkSaver.os.walk')
    def test_folder_search(self, mock_walk):

        mock_walk.return_value = [
            ('/Users', ('andrewgodley',), ()),
            ('/Users/andrewgodley', ('OneDrive', ), ()),
            ('/Users/andrewgodley/OneDrive', ('Food Save', ), ()),
            ('/Users/andrewgodley/OneDrive/Food Save', ('Cooking', ), ()),
            ('/Users/andrewgodley/OneDrive/Food Save/Cooking', ('Tested', ), ()),
            ('/Users/andrewgodley/OneDrive/Food Save/Cooking/Tested', ('Beef', ), ()),
            ('/Users/andrewgodley/OneDrive/Food Save/Cooking/Tested/Beef', (), ('Beef orange stirfry recipe  BBC Good Food-full.png', 'Red Wine Cheeseburgers Jennifer Meyering-full.png', 'Beef Curry Udon Recipe-full.png', 'Beef bulgogi stirfry recipe-full.png', 'Greekstyle stuffed peppers with beef-full.png', 'Chilli con carne-full.png'))
        ]

        folder_items = SafariBookmarkSaver.folder_search(os.path.expanduser("~/OneDrive/Food Save/Cooking/Tested/Beef/"))
        self.assertEqual(folder_items, testData.searchedFolder)

    def test_reduce_dictionary(self):
        reduced_dictionary = SafariBookmarkSaver.reduce_dictionary(testData.recursiveSearched, testData.reduceFiles)
        self.assertEqual(len(reduced_dictionary), len(testData.recursiveSearched) - 2)

    @patch('SafariBookmarkSaver.os.remove')
    def test_deleted_bookmarks(self, mock_remove):
        SafariBookmarkSaver.identify_deleted_bookmarks(testData.recursiveSearched, testData.deletedFiles)
        self.assertEqual(mock_remove.call_count, 2)
        mock_remove.assert_has_calls([call('/tempString/file/iNeedAnotherFile-full.png'), call('/tempString/file/andAnother-full.png')])

    @patch('SafariBookmarkSaver.sys')
    @patch('SafariBookmarkSaver.os')
    @patch('SafariBookmarkSaver.copy')
    def test_moved_bookmarks(self, mock_sys, mock_os, mock_copy):

        mock_os.path.isdir.side_effect = [True, False]

        moved_bookmarks = SafariBookmarkSaver.moved_bookmarks(testData.recursiveSearched, testData.movedFiles)
        self.assertEqual(mock_os.mkdir.call_count, 1)
        self.assertEqual(len(testData.recursiveSearched), len(moved_bookmarks) + 2)


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
