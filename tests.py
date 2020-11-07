import unittest
import testData
import SafariBookmarkSaver
import testData


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


if __name__ == '__main__':
    unittest.main()

    # folderSearch       -   requires os
    # reduceDictionary
    # movedBookmarks
    # identifyDeletedBookmarks
    # saveSiteAsPicture
    # writeTesterToFil
    # checkSavedBookmarks
    # loopAndSaveBookmarks
