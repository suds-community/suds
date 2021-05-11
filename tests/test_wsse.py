import pytest
from six import b, itervalues, next

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())
from testutils.compare_sax import CompareSAX

from suds.wsse import Security, UsernameToken

class TestUsernameToken:

    def test_wsse_username_token(self):
        security = Security()
        token = UsernameToken("username", "password")
        security.tokens.append(token)
        expected = """<wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" mustUnderstand="true">
   <wsse:UsernameToken>
      <wsse:Username>username</wsse:Username>
      <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">password</wsse:Password>
   </wsse:UsernameToken>
</wsse:Security>"""
        assert expected == str(security.xml())

    def test_wsse_username_nonce(self):
        security = Security()
        token = UsernameToken("username", "password")
        token.setnonce()
        token.setcreated()
        token.setnonceencoding(True)
        token.setpassworddigest("digest")
        security.tokens.append(token)
        assert "<wsu:Created" in str(security.xml())
