import unittest
import testData
import SafariBookmarkSaver
import testData

class TestMethods(unittest.TestCase):

    def test_sortFunction(self):
        result = SafariBookmarkSaver.sortFunc(testData.arepas, testData.chickpeaOmelete)
        result2 = SafariBookmarkSaver.sortFunc(testData.chickpeaOmelete, testData.arepas)
        result3 = SafariBookmarkSaver.sortFunc(testData.arepas, testData.arepas)

        self.assertEqual(result, 1)
        self.assertEqual(result2, -1)
        self.assertEqual(result3, 0)

    def test_full_sort(self):
        sortedOutput = SafariBookmarkSaver.sortOutput(testData.unsortedData)
        self.assertEqual(sortedOutput, testData.sortedData)


if __name__ == '__main__':
    unittest.main()