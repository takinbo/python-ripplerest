import unittest
from ripplerest import Client

class Constructor(unittest.TestCase):
	def setUp(self):
		import uuid
		self.uuid = str(uuid.uuid4())
		self.netloc = 'example.com:2334'
		self.client = Client(resource_id=self.uuid, netloc=self.netloc)
	
	def test_specify_uuid(self):
		self.assertEqual(self.client._resource_id, self.uuid)
	
	def test_specify_host(self):
		self.assertEqual(self.client.netloc, self.netloc)
