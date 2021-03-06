# To use this, you need to put your AWS API credentials into /etc/boto.cfg
# Access these under "Security Credentials" >> "Users" >> "Create Access Key"
# [Credentials]
# aws_access_key_id = <access_key>
# aws_secret_access_key = <secret_key>

# Also make sure for FTP that you open 21 and 50000-51000 to TCP.


from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed, AuthorizerError
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import boto
from boto.ec2.connection import EC2Connection
from boto.dynamodb2.table import Table
import hashlib
import os
import urllib2


"""usertable = Table("ec2.clive.io-subdomains")"""
class UserAuthError(Exception):
  """Exception for bad users"""

"""
class User:
  def __init__(self, username):
    try:
      self.item = usertable.get_item(username = username)
    except boto.dynamodb.exceptions.DynamoDBKeyNotFoundError:
      raise UserAuthError
  def val(self, username, password):
    try:
"""

class DBAuthorizer(DummyAuthorizer):
  def __init__(self):
    self.user_db = Table("ec2.clive.io-subdomains")
    self.user_table = {}
  def add_user(self, username, password, homedir, perm='elr', msg_login="Login successful.", msg_quit="Goodbye."):
    if self.user_table != {}:
      raise AuthorizerError("Already logged in!")
    DummyAuthorizer.add_user(self,username,password,homedir,perm,msg_login,msg_quit)
  def add_anonymous(self, homedir, **kwargs):
    raise AuthorizerError("Adding anonymous users not allowed.")
  def remove_user(self, username):
    self.user_table = {}
  def validate_authentication(self, username, password, handler):
    if username in self.user_table:
      return None
    if not username.isalnum():
      raise AuthenticationFailed("Authentication Failed.")
    try:
      item = self.user_db.get_item(username=username)
    except:
      raise AuthenticationFailed("Authentication failed.")
    if item['passhash'] != hashlib.sha1(password + item['passsalt']).hexdigest():
      raise AuthenticationFailed("Authentication failed.")
    self.add_user(username, None, os.path.join(os.path.dirname(__file__),"serverfiles",username), perm="elradfmw")

authorizer = DBAuthorizer()

handler = FTPHandler
handler.authorizer = authorizer
handler.masquerade_address = urllib2.urlopen("http://instance-data/latest/meta-data/public-ipv4").read()
handler.passive_ports = [50000, 51000]

server = FTPServer(('', 21), handler)
server.serve_forever()
