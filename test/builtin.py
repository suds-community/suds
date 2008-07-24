
def assertEquals(one, two):
    if one != two:
        raise Exception('Assertion Exception!  %s does not equal %s' % (one, two))

from suds.xsd.sxbuiltin import *
import unittest
    
class TestXDate(unittest.TestCase):
    """
    examples
    2002-09-24
    2002-09-24Z
    2002-09-24-06:00
    2002-09-24+06:00
    """
    #fake it out a bit so I can just test what matters
    def fake_init(self):
        pass
    XDate.__init__ = fake_init
    
    def setUp(self):
        pass
        
    def test_should_return_correct_date_object_given_simple_date(self):
        date = XDate().translate("2006-10-10")
        self.assertEqual(date.day, 10)
        self.assertEqual(date.month, 10)
        self.assertEqual(date.year, 2006)
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)
        self.assertEqual(date.hour, 0)
        
    def test_should_return_correct_string_from_date_object_given_simple_date(self):
        date = XDate().translate(XDate().translate("2006-10-10"), False)
        
        self.assertEquals("2006-10-10+06:00", date)
        
    def test_should_return_correct_date_object_given_date_with_timezone(self):
        #from where I am, this is still local time
        date = XDate().translate("1945-08-20+06:00")
        self.assertEqual(date.day, 20)
        self.assertEqual(date.month, 8)
        self.assertEqual(date.year, 1945)
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)
        self.assertEqual(date.hour, 0)
        
    def test_should_return_correct_string_from_date_object_given_date_with_timezone(self):
        date = XDate().translate(XDate().translate("1945-08-20+06:00"), False)
        
        self.assertEquals("1945-08-20+06:00", date)

    def test_should_return_correct_date_object_given_date_with_different_timezone(self):
        #from where I am, this is 3 hours off
        date = XDate().translate("1945-08-20+03:00")
        self.assertEqual(date.day, 19)
        self.assertEqual(date.month, 8)
        self.assertEqual(date.year, 1945)
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)
        self.assertEqual(date.hour, 21)

    def test_should_return_correct_string_from_date_object_given_date_with_timezone(self):
        date = XDate().translate(XDate().translate("1945-08-20+03:00"), False)

        self.assertEquals("1945-08-19+06:00", date)

    def test_should_return_correct_date_object_given_date_with_different_utc(self):
        #from where I am, this is 6 hours off and would become a different day
        date = XDate().translate("1945-08-20Z")
        self.assertEqual(date.day, 19)
        self.assertEqual(date.month, 8)
        self.assertEqual(date.year, 1945)
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)
        self.assertEqual(date.hour, 18)

    def test_should_return_correct_string_from_date_object_given_date_with_utc(self):
        date = XDate().translate(XDate().translate("1945-08-20Z"), False)

        self.assertEquals("1945-08-19+06:00", date)
        
      
class TestXTime(unittest.TestCase):
    """
    09:00:00
    09:30:10.5
    09:30:10Z
    09:30:10-06:00
    09:30:10+06:00
    """
    #fake it out a bit so I can just test what matters
    def fake_init(self):
        pass
    XTime.__init__ = fake_init

    def setUp(self):
        pass

    def test_should_return_correct_time_object_given_simple_time(self):
        date = XTime().translate("09:00:00")
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)
        self.assertEqual(date.hour, 9)

    def test_should_return_correct_string_from_time_object_given_simple_time(self):
        date = XTime().translate(XTime().translate("09:00:00"), False)

        self.assertEquals("09:00:00+06:00", date)
        
    def test_should_return_correct_time_object_given_time_with_microseconds(self):
        time = XTime().translate("09:30:10.5")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 9)
        self.assertEqual(time.microsecond, 500000)

    def test_should_return_correct_string_from_time_object_given_time_with_microseconds(self):
        date = XTime().translate(XTime().translate("09:30:10.5"), False)

        self.assertEquals("09:30:10.5+06:00", date)

    def test_should_return_correct_time_object_given_time_with_utc(self):
        time = XTime().translate("09:30:10Z")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 3)
        self.assertEqual(time.microsecond, 0)

    def test_should_return_correct_string_from_time_object_given_time_with_utc(self):
        date = XTime().translate(XTime().translate("09:30:10Z"), False)

        self.assertEquals("03:30:10+06:00", date)
                
    def test_should_return_correct_time_object_given_complex_time(self):
        time = XTime().translate("09:30:10.525+09:00")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 12)
        self.assertEqual(time.microsecond, 525000)

    def test_should_return_correct_string_from_time_object_given_complex_time(self):
        date = XTime().translate(XTime().translate("09:30:10.525+09:00"), False)

        self.assertEquals("12:30:10.525+06:00", date)
        
    def test_should_wrap_time_correctly(self):
        time = XTime().translate("23:30:10.525+09:00")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 2)
        self.assertEqual(time.microsecond, 525000)
        
        time = XTime().translate("00:30:10.525-03:00")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 15)
        self.assertEqual(time.microsecond, 525000)
        
        time = XTime().translate("05:30:10.525+03:00")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 2)
        self.assertEqual(time.microsecond, 525000)
        
        time = XTime().translate("05:30:10.525-03:00")
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 10)
        self.assertEqual(time.hour, 20)
        self.assertEqual(time.microsecond, 525000)

        
class TestXDateTime(unittest.TestCase):
    """
    2002-05-30T09:00:00
    2002-05-30T09:30:10.5
    """
    #fake it out a bit so I can just test what matters
    def fake_init(self):
        pass
    XDateTime.__init__ = fake_init

    def setUp(self):
        pass

    def test_should_return_correct_time_object_given_simple_time(self):
        date = XDateTime().translate("2002-05-30T09:00:00")
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)
        self.assertEqual(date.microsecond, 0)
        self.assertEqual(date.hour, 9)
        self.assertEqual(date.day, 30)
        self.assertEqual(date.year, 2002)
        self.assertEqual(date.month, 5)

    def test_should_return_correct_string_from_time_object_given_simple_time(self):
        date = XDateTime().translate(XDateTime().translate("2002-05-30T09:00:00"), False)

        self.assertEquals("2002-05-30T09:00:00+06:00", date)
        
    def test_should_return_correct_time_object_given_simple_time(self):
        date = XDateTime().translate("2002-05-30T09:30:10.5")
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 10)
        self.assertEqual(date.microsecond, 500000)
        self.assertEqual(date.hour, 9)
        self.assertEqual(date.day, 30)
        self.assertEqual(date.year, 2002)
        self.assertEqual(date.month, 5)

    def test_should_return_correct_string_from_time_object_given_simple_time(self):
        date = XDateTime().translate(XDateTime().translate("2002-05-30T09:30:10.5"), False)

        self.assertEquals("2002-05-30T09:30:10.5+06:00", date)
        
    def test_should_wrap_time_correctly(self):
        date = XDateTime().translate("2002-05-30T23:30:10.525+09:00")
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 10)
        self.assertEqual(date.hour, 2)
        self.assertEqual(date.microsecond, 525000)
        self.assertEqual(date.day, 31)
        self.assertEqual(date.year, 2002)
        self.assertEqual(date.month, 5)

        date = XDateTime().translate("2002-05-30T00:30:10.525-03:00")
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 10)
        self.assertEqual(date.hour, 15)
        self.assertEqual(date.microsecond, 525000)
        self.assertEqual(date.day, 29)
        self.assertEqual(date.year, 2002)
        self.assertEqual(date.month, 5)

        date = XDateTime().translate("2002-05-30T05:30:10.525+03:00")
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 10)
        self.assertEqual(date.hour, 2)
        self.assertEqual(date.microsecond, 525000)
        self.assertEqual(date.day, 30)
        self.assertEqual(date.year, 2002)
        self.assertEqual(date.month, 5)

        date = XDateTime().translate("2002-05-30T05:30:10.525-03:00")
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 10)
        self.assertEqual(date.hour, 20)
        self.assertEqual(date.microsecond, 525000)
        self.assertEqual(date.day, 29)
        self.assertEqual(date.year, 2002)
        self.assertEqual(date.month, 5)
        
if __name__ == '__main__':
    unittest.main()
