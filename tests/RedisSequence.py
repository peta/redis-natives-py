'''
Created on 21.06.2010

@author: Peter Geil
'''
import unittest

from redis import Redis

from redis_natives.datatypes import Sequence


class SequenceTest(unittest.TestCase):
    
    def setUp(self):
        self.client = Redis(db=4)
        self.client.flushdb()
        self.testKey = "testKey"
        self.multiple = 50
        self.testElements = ["testEl1", "testEl2", "testEl3"]
        self.nonOverlappingSets = [set([1, 2]), set([3, 4]), set([5, 6])]
        self.overlappingSets = [set([1, 2]), set([2, 3]), set([3, 4])]

    def tearDown(self):
        self.client.flushdb()
        del self.client

    def testNew(self):
        rl = Sequence(self.testKey, self.client)
        self.assertEqual(0, len(self.client.keys("*")),
                         "Created db-keys although created without initial values")
        
    def testNewWithReset(self):
        self.client.lpush(self.testKey, "foo")
        rl = Sequence(self.testKey, self.client, reset=True)
        self.assertEqual(0, len(self.client.keys("*")),
                         "Created db-keys although created without initial values")
    
    def testReversed(self):
        rl = Sequence(self.testKey, self.client)        
        map(rl.push_tail, self.testElements)
        
        revRl, revTest = rl.__reversed__(), self.testElements.__reversed__()        
        for i in range(len(self.testElements)):
            eRl, eTest = revRl.next(), revTest.next()
            self.assertEqual(eRl, eTest, "Elements should appear in the same order")
        self.assertRaises(StopIteration, revRl.next)

    def testPushHead(self):
        rl = Sequence(self.testKey, self.client)
         
        for el in self.testElements:
            rl.push_head(el)
            self.assertTrue( (el in rl), "Should contain all test elements")
            self.assertEqual(1, rl.count(el), "Each test element should appear only once")
            self.assertEqual(el, rl[0], "Element at index '0' should be equal the one pushed to head lastly")
        
    def testPushTail(self):
        rl = Sequence(self.testKey, self.client)
         
        for idx, el in enumerate(self.testElements):
            rl.push_tail(el)
            self.assertEqual(el, rl[idx], "Elements should appear in the order they were rpushed by __init__")
            self.assertTrue( (el in rl), "Should contain all test elements")
            self.assertEqual(self.testElements.index(el), rl.index(el), "Elements should appear in the order they were rpushed")
            self.assertEqual(1, rl.count(el), "Each test element should appear only once")
        
    def testPopTailPushHead(self):
        rl = Sequence(self.testKey, self.client)        
        dst = Sequence("foo", self.client)
        map(rl.push_tail, self.testElements)
        
        for el in self.testElements:
            rl.push_tail(el)
            rl.pop_tail_push_head(dst.key)
            self.assertEqual(el, dst[0], "first elem in dst should be the one ptph'd last")
         
         
         
         
         

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()