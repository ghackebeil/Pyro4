"""
Tests for the utility functions.

Pyro - Python Remote Objects.  Copyright by Irmen de Jong (irmen@razorvine.net).
"""

import sys
import os
import Pyro4.util
from testsupport import *


# noinspection PyUnusedLocal
def crash(arg=100):
    pre1 = "black"
    pre2 = 999

    # noinspection PyUnusedLocal
    def nest(p1, p2):
        q = "white" + pre1
        x = pre2
        y = arg // 2
        p3 = p1 // p2
        return p3

    a = 10
    b = 0
    s = "hello"
    c = nest(a, b)
    return c


class TestUtils(unittest.TestCase):
    def testFormatTracebackNormal(self):
        try:
            crash()
            self.fail("must crash with ZeroDivisionError")
        except ZeroDivisionError:
            tb = "".join(Pyro4.util.formatTraceback(detailed=False))
            self.assertTrue("p3 = p1 // p2" in tb)
            self.assertTrue("ZeroDivisionError" in tb)
            self.assertFalse(" a = 10" in tb)
            self.assertFalse(" s = 'whiteblack'" in tb)
            self.assertFalse(" pre2 = 999" in tb)
            self.assertFalse(" x = 999" in tb)

    def testFormatTracebackDetail(self):
        try:
            crash()
            self.fail("must crash with ZeroDivisionError")
        except ZeroDivisionError:
            tb = "".join(Pyro4.util.formatTraceback(detailed=True))
            self.assertTrue("p3 = p1 // p2" in tb)
            self.assertTrue("ZeroDivisionError" in tb)
            if sys.platform != "cli":
                self.assertTrue(" a = 10" in tb)
                self.assertTrue(" q = 'whiteblack'" in tb)
                self.assertTrue(" pre2 = 999" in tb)
                self.assertTrue(" x = 999" in tb)

    def testPyroTraceback(self):
        try:
            crash()
            self.fail("must crash with ZeroDivisionError")
        except ZeroDivisionError:
            pyro_tb = Pyro4.util.formatTraceback(detailed=True)
            if sys.platform != "cli":
                self.assertTrue(" Extended stacktrace follows (most recent call last)\n" in pyro_tb)
        try:
            crash("stringvalue")
            self.fail("must crash with TypeError")
        except TypeError:
            x = sys.exc_info()[1]
            x._pyroTraceback = pyro_tb  # set the remote traceback info
            pyrotb = "".join(Pyro4.util.getPyroTraceback())
            self.assertTrue("Remote traceback" in pyrotb)
            self.assertTrue("crash(\"stringvalue\")" in pyrotb)
            self.assertTrue("TypeError:" in pyrotb)
            self.assertTrue("ZeroDivisionError" in pyrotb)
            del x._pyroTraceback
            pyrotb = "".join(Pyro4.util.getPyroTraceback())
            self.assertFalse("Remote traceback" in pyrotb)
            self.assertFalse("ZeroDivisionError" in pyrotb)
            self.assertTrue("crash(\"stringvalue\")" in pyrotb)
            self.assertTrue("TypeError:" in pyrotb)

    def testPyroTracebackArgs(self):
        try:
            crash()
            self.fail("must crash with ZeroDivisionError")
        except ZeroDivisionError:
            ex_type, ex_value, ex_tb = sys.exc_info()
            x = ex_value
            tb1 = Pyro4.util.getPyroTraceback()
            tb2 = Pyro4.util.getPyroTraceback(ex_type, ex_value, ex_tb)
            self.assertEqual(tb1, tb2)
            tb1 = Pyro4.util.formatTraceback()
            tb2 = Pyro4.util.formatTraceback(ex_type, ex_value, ex_tb)
            self.assertEqual(tb1, tb2)
            tb2 = Pyro4.util.formatTraceback(detailed=True)
            if sys.platform != "cli":
                self.assertNotEqual(tb1, tb2)
            # old call syntax, should get an error now:
            self.assertRaises(TypeError, Pyro4.util.getPyroTraceback, x)
            self.assertRaises(TypeError, Pyro4.util.formatTraceback, x)

    def testExcepthook(self):
        # simply test the excepthook by calling it the way Python would
        try:
            crash()
            self.fail("must crash with ZeroDivisionError")
        except ZeroDivisionError:
            pyro_tb = Pyro4.util.formatTraceback()
        try:
            crash("stringvalue")
            self.fail("must crash with TypeError")
        except TypeError:
            ex_type, ex_value, ex_tb = sys.exc_info()
            ex_value._pyroTraceback = pyro_tb  # set the remote traceback info
            oldstderr = sys.stderr
            try:
                sys.stderr = StringIO()
                Pyro4.util.excepthook(ex_type, ex_value, ex_tb)
                output = sys.stderr.getvalue()
                self.assertTrue("Remote traceback" in output)
                self.assertTrue("crash(\"stringvalue\")" in output)
                self.assertTrue("TypeError:" in output)
                self.assertTrue("ZeroDivisionError" in output)
            finally:
                sys.stderr = oldstderr

    def clearEnv(self):
        if "PYRO_HOST" in os.environ:
            del os.environ["PYRO_HOST"]
        if "PYRO_NS_PORT" in os.environ:
            del os.environ["PYRO_NS_PORT"]
        if "PYRO_COMPRESSION" in os.environ:
            del os.environ["PYRO_COMPRESSION"]
        Pyro4.config.reset()

    def testConfig(self):
        self.clearEnv()
        try:
            self.assertEqual(9090, Pyro4.config.NS_PORT)
            self.assertEqual("localhost", Pyro4.config.HOST)
            self.assertEqual(False, Pyro4.config.COMPRESSION)
            os.environ["NS_PORT"] = "4444"
            Pyro4.config.reset()
            self.assertEqual(9090, Pyro4.config.NS_PORT)
            os.environ["PYRO_NS_PORT"] = "4444"
            os.environ["PYRO_HOST"] = "something.com"
            os.environ["PYRO_COMPRESSION"] = "OFF"
            Pyro4.config.reset()
            self.assertEqual(4444, Pyro4.config.NS_PORT)
            self.assertEqual("something.com", Pyro4.config.HOST)
            self.assertEqual(False, Pyro4.config.COMPRESSION)
        finally:
            self.clearEnv()
            self.assertEqual(9090, Pyro4.config.NS_PORT)
            self.assertEqual("localhost", Pyro4.config.HOST)
            self.assertEqual(False, Pyro4.config.COMPRESSION)

    def testConfigReset(self):
        try:
            Pyro4.config.reset()
            self.assertEqual("localhost", Pyro4.config.HOST)
            Pyro4.config.HOST = "foobar"
            self.assertEqual("foobar", Pyro4.config.HOST)
            Pyro4.config.reset()
            self.assertEqual("localhost", Pyro4.config.HOST)
            os.environ["PYRO_HOST"] = "foobar"
            Pyro4.config.reset()
            self.assertEqual("foobar", Pyro4.config.HOST)
            del os.environ["PYRO_HOST"]
            Pyro4.config.reset()
            self.assertEqual("localhost", Pyro4.config.HOST)
        finally:
            self.clearEnv()

    def testResolveAttr(self):
        class Test(object):
            def __init__(self, value):
                self.value = value

            def __str__(self):
                return "<%s>" % self.value

            def _p(self):
                return "should not be allowed"

            def __p__(self):
                return "should not be allowed"

        obj = Test("obj")
        obj.a = Test("a")
        obj.a.b = Test("b")
        obj.a.b.c = Test("c")
        obj.a._p = Test("p1")
        obj.a._p.q = Test("q1")
        obj.a.__p = Test("p2")
        obj.a.__p.q = Test("q2")
        # check the method with dotted disabled
        self.assertEqual("<a>", str(Pyro4.util.resolveDottedAttribute(obj, "a", False)))
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "_p", False)  # private
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "__p__", False)  # private
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a.b", False)
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a.b.c", False)
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a.b.c.d", False)
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a._p", False)
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a._p.q", False)
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a.__p.q", False)
        # now with dotted enabled
        self.assertEqual("<a>", str(Pyro4.util.resolveDottedAttribute(obj, "a", True)))
        self.assertEqual("<b>", str(Pyro4.util.resolveDottedAttribute(obj, "a.b", True)))
        self.assertEqual("<c>", str(Pyro4.util.resolveDottedAttribute(obj, "a.b.c", True)))
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a.b.c.d", True)  # doesn't exist
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "_p", True)  # private
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "__p__", True)  # private
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a._p", True)  # private
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a._p.q", True)  # private
        self.assertRaises(AttributeError, Pyro4.util.resolveDottedAttribute, obj, "a.__p.q", True)  # private

    @unittest.skipUnless(sys.version_info >= (2, 6, 5), "unicode kwargs needs 2.6.5 or newer")
    def testUnicodeKwargs(self):
        # test the way the interpreter deals with unicode function kwargs
        # those are supported by Python after 2.6.5
        def function(*args, **kwargs):
            return args, kwargs

        processed_args = function(*(1, 2, 3), **{unichr(65): 42})
        self.assertEqual(((1, 2, 3), {unichr(65): 42}), processed_args)
        processed_args = function(*(1, 2, 3), **{unichr(0x20ac): 42})
        key = list(processed_args[1].keys())[0]
        self.assertTrue(type(key) is unicode)
        self.assertEqual(key, unichr(0x20ac))
        self.assertEqual(((1, 2, 3), {unichr(0x20ac): 42}), processed_args)


class MyThing(object):
    c_attr = "hi"
    propvalue = 42
    _private_attr1 = "hi"
    __private_attr2 = "hi"

    def method(self, arg, default=99, **kwargs):
        pass

    @staticmethod
    def staticmethod(arg):
        pass

    @classmethod
    def classmethod(cls, arg):
        pass

    def __private__(self):
        pass

    def __private(self):
        pass

    def _private(self):
        pass

    def __init__(self, name):
        self.name = name

    @property
    def prop1(self):
        return self.propvalue

    @property
    def prop2(self):
        return self.propvalue

    @prop2.setter
    def prop2(self, value):
        self.propvalue = value

    @Pyro4.oneway
    def oneway(self, arg):
        pass

    @Pyro4.expose
    def exposed(self):
        pass


@Pyro4.expose
class MyThingExposed(object):
    blurp = 99   # won't be exposed, because it is a class attribute and not a property

    def __init__(self, name):
        self.name = name

    def foo(self, arg):
        return arg

    @classmethod
    def classmethod(cls, arg):
        return arg

    @staticmethod
    def staticmethod(arg):
        return arg

    @property
    def name(self):
        return "thing"

    @name.setter
    def name(self, value):
        pass

    @Pyro4.oneway
    def remotemethod(self, arg):
        return arg

    def _p(self):
        pass

    def __private__(self):
        pass


class TestMeta(unittest.TestCase):
    def testBasic(self):
        o = MyThing("irmen")
        m1 = Pyro4.util.get_exposed_members(o)
        m2 = Pyro4.util.get_exposed_members(MyThing)
        self.assertEqual(m1, m2)
        keys = m1.keys()
        self.assertEqual(3, len(keys))
        self.assertIn("methods", keys)
        self.assertIn("attrs", keys)
        self.assertIn("oneway", keys)

    def testPrivate(self):
        o = MyThing("irmen")
        m = Pyro4.util.get_exposed_members(o)
        for p in ["_private_attr1", "__private_attr2", "__private__", "__private", "_private", "__init__"]:
            self.assertNotIn(p, m["methods"])
            self.assertNotIn(p, m["attrs"])
            self.assertNotIn(p, m["oneway"])

    def testNotOnlyExposed(self):
        o = MyThing("irmen")
        m = Pyro4.util.get_exposed_members(o, only_exposed=False)
        self.assertEqual(set(["prop1", "prop2"]), m["attrs"])
        self.assertEqual(set(["oneway"]), m["oneway"])
        self.assertEqual(set(["classmethod", "oneway", "method", "staticmethod", "exposed"]), m["methods"])

    def testOnlyExposed(self):
        o = MyThing("irmen")
        m = Pyro4.util.get_exposed_members(o)
        self.assertEqual(set(), m["attrs"])
        self.assertEqual(set(), m["oneway"])
        self.assertEqual(set(["exposed"]), m["methods"])

    def testExposedClass(self):
        o = MyThingExposed("irmen")
        m = Pyro4.util.get_exposed_members(o)
        self.assertEqual(set(["name"]), m["attrs"])
        self.assertEqual(set(["remotemethod"]), m["oneway"])
        self.assertEqual(set(["classmethod", "foo", "staticmethod", "remotemethod"]), m["methods"])

    def testExposePrivateFails(self):
        with self.assertRaises(AttributeError):
            class Test1(object):
                @Pyro4.expose
                def _private(self):
                    pass
        with self.assertRaises(AttributeError):
            class Test2(object):
                @Pyro4.expose
                def __private__(self):
                    pass
        with self.assertRaises(AttributeError):
            @Pyro4.expose
            class _Test3(object):
                pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
