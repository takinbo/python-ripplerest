"""This is a client for the ripple-rest server

To use it, first instantiate a Client object::

  >>> import ripplerest
  >>> client = ripplerest.Client("localhost:5990")

then submit a request using one of the methods.
For example you can query for account settings::

  >>> client.get_account_settings("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")
  {
  "email_hash": "7EC7606C46A14A7EF514D1F1F9038823",
  "disallow_xrp": false,
  "transfer_rate": 1001000000,
  "url": "example.org",
  "disable_master": false,
  "account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "transaction_sequence": 27660,
  "password_spent": false,
  "require_authorization": false,
  "require_destination_tag": false
  }

You can also make POST requests, like a payment::

  >>> from ripplerest.entities import Amount, Payment
  >>> drop = Amount(1e-6, 'XRP')
  >>> payment = Payment('rSourceAccountAddress', 'rDestinationAddress', drop)
  >>> uuid, url = client.post_payment('sMasterPassword', payment)

All requests are idempotent (from point of view of the Ripple network) except for :func:`ripplerest.Client.post_payment`.
In this case, since there is the risk of accidental double-spending, each
request also includes a UUID (which the client generates randomly when
instantiated).
To submit multiple payments, you have to explicitly reset the UUID
using :func:`ripplerest.Client.set_resource_id` in this way::

  >>> uuid, url = client.post_payment('sMasterPassword', payment)
  >>> uuid, url = client.post_payment('sMasterPassword', payment)
  ripplerest.client.RippleRESTException: A record already exists in the database
  for a payment from this account with the same client_resource_id. Payments
  must be submitted with distinct client_resource_id's to prevent accidental
  double-spending
  >>> client.set_resource_id()
  >>> uuid, url = client.post_payment('sMasterPassword', payment)
"""
import sys

if sys.version_info[0] < 3:
    from urllib2 import Request, urlopen
    from urllib import urlencode
    from urlparse import urlunsplit
    from urllib2 import HTTPError
else:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode, urlunsplit
    from urllib.error import HTTPError

import json
import uuid

from ripplerest.entities import AccountSettings
from ripplerest.entities import Amount
from ripplerest.entities import Balance
from ripplerest.entities import Payment
from ripplerest.entities import Trustline

VERSION = 'v1'

class RippleRESTException(Exception):
  pass

class Client:
  """The ripple-rest client

  In the client the server address and a unique client UUID are stored
  A Client can be used only for a single payment, unless its UUID is reset

  :param netloc: The hostname of the ripple rest server
  :param secure: If the connection to the server should be encripted
  :param resource_id: The UUID to be used for the requests
  """
  def set_resource_id(self, resource_id=None):
    """Set the local UUID

    :param resource_id: The UUID to be used. Defaults to a random one
    """
    self.uuid = resource_id or str(uuid.uuid4())

  def __init__(self, netloc, secure=False,
    resource_id=None):
    self.netloc = netloc
    self.scheme = 'https' if secure else 'http'
    self.set_resource_id(resource_id=resource_id)

  def _request(self, path, parameters=None, data=None, secret=None,
    complete_path=False):
    """Make an HTTP request to the server

    Encode the query parameters and the form data and make the GET or POST
    request

    :param path: The path of the HTTP resource
    :param parameters: The query parameters
    :param data: The data to be sent in JSON format
    :param secret: The secret key, which will be added to the data
    :param complete_path: Do not prepend the common path

    :returns: The response, stripped of the 'success' field

    :raises RippleRESTException: An error returned by the rest server
    """
    if not complete_path:
      path = '/{version}/{path}'.format(version=VERSION, path=path)
    if parameters:
      parameters = {k:v for k,v in parameters.items() if v is not None}
      for k, v in parameters.items():
        if type(v) is bool:
          parameters[k] = 'true' if v else 'false'
      parameters = urlencode(parameters)
    pieces = (self.scheme, self.netloc, path, parameters, None)
    url = urlunsplit(pieces)
    req = Request(url)
    if data is not None:
      req.add_header("Content-Type","application/json;charset=utf-8")
      data['client_resource_id'] = self.uuid
      data['secret'] = secret
      data = json.dumps(data).encode('utf-8')
    try:
      response = urlopen(req, data)
      response = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
      error_object = json.loads(e.read().decode('utf-8'))['message']
      raise RippleRESTException(error_object)
    if response['success']:
      del response['success']
      return response
    else:
      raise RippleRESTException(response['message'])

  def get_balances(self, address, **kwargs):
    """Get the balances of an account

    :param address: The account to be queried
    :param currency: The currency to limit the query to
    :param counterparty: The issuer of the IOU

    :returns: A generator of balances
    """
    url = 'accounts/{address}/balances'
    url = url.format(address=address)
    response = self._request(url, kwargs)
    for balance in response['balances']:
      yield Balance(issuer=address, **balance)

  def get_account_settings(self, address, **kwargs):
    """Get the settings of the specified account

    :param address: The account to be queried

    :return: The requested settings
    :rtype: AccountSettings
    """
    url = 'accounts/{address}/settings'
    url = url.format(address=address)
    response = self._request(url)
    return AccountSettings(**response['settings'])

  def post_account_settings(self, address, secret, **kwargs):
    """Set the account settings

    One or more parameters can be specified at one time.

    :param secret: The key that will be used to sign the transaction
    :param address: The Ripple address of the account in question
    :param bool disable_master:
    :param bool disallow_xrp:
    :param bool password_spent:
    :param bool require_authorization:
    :param bool require_destination_tag:
    :param transaction_sequence:
    :param email_hash:
    :param wallet_locator:
    :param message_key:
    :param url:
    :param transfer_rate:
    :param signers:

    :return: The settings of the account after the change
    """
    url = 'accounts/{address}/settings'
    url = url.format(address=address)
    response = self._request(url, data=kwargs, secret=secret)
    return response['ledger'], response['hash'], response['settings']

  def post_payment(self, secret, payment):
    """Send a payment

    To prevent double-spends, only one payment is possible with the same UUID.
    A second payment is possible if the UUID is reset using set_resource_id()

    :param secret: The key that will be used to sign the transaction
    :param payment: The proposed payment that will be sent to the network

    :return: The UUID used for this payment and the URL of the payment
    :rtype: (uuid, url)
    """
    url = 'payments'
    response = self._request(url, data={'payment': payment}, secret=secret)
    return response['client_resource_id'], response['status_url']

  def get_paths(self, address, destination_account, value, currency,
    issuer=None, source_currencies=None):
    """Query for possible payment paths

    :param address: The source account
    :param destination_account: The destination account
    :param float value: The value of the payment
    :param currency: The currency of the payment
    :param issuer: The issuer of the IOU. If not specified, paths
        will be returned for all of the issuers from whom the
        destination_account accepts the given currency
    :param list source_currencies: Currencies in the form
        (currency_code, [issuer]). If no issuer is specified for a currency
        other than XRP, the results will be limited to the specified currencies
        but any issuer for that currency will do

    :return: A generator of possible payments, ready to be submitted
    """
    elements = filter(bool, (value, currency, issuer))
    destination_amount = '+'.join(map(str, elements))
    if source_currencies:
      source_currencies = join(' '.join(curr) for curr in source_currencies)
      parameters = {'source_currencies': source_currencies}
    else:
      parameters = None
    url = 'accounts/{source}/payments/paths/{target}/{amount}'
    url = url.format(
      source=address,
      target=destination_account,
      amount=destination_amount,
    )
    response = self._request(url, parameters)
    for payment in response['payments']:
      yield Payment(**payment)

  def get_payment(self, address, hash_or_uuid):
    """Get payment

    Retrieve the details of one or more payments from the rippled server or,
    if the transaction failled off-network or is still pending,
    from the ripple-rest instance's local database

    :param address: A ripple account
    :param hash_or_uuid: The identifier of the payment

    :return: The requested payment
    """
    url = 'accounts/{address}/payments/{hash_or_uuid}'
    url = url.format(
      address=address,
      hash_or_uuid=hash_or_uuid
    )
    response = self._request(url)
    return Payment(**response['payment'])

  def get_payments(self, address, **kwargs):
    """Retrieve historical payments

    :param address: A ripple account
    :param source_account: Limit the results to payments initiated
        by a particular account
    :param destination_account: Limit the results to payments made
        to a particular account
    :param bool exclude_failed: Return only payment that were successfully
        validated and written into the Ripple Ledger
    :param int start_ledger: If earliest_first is set to true this will be the
        index number of the earliest ledger queried, or the most recent one
        if earliest_first is set to false. Defaults to the first ledger the
        rippled has in its complete ledger
    :param int end_ledger: If earliest_first is set to true this will be the index
        number of the most recent ledger queried, or the earliest one if
        earliest_first is set to false. Defaults to the last ledger the rippled
        has in its complete ledger
    :param bool earliest_first: Determines the order in which the results should
        be displayed. Defaults to True
    :param int results_per_page: Limits the number of payments displayed per page
        Defaults to 20
    :param int page: The page to be displayed. If there are fewer payments than
        results_per_page number displayed, this indicates that this is
        the last page

    :returns: A generator of pairs of payments and corresponding UUIDs.
      The UUIDs can be blank if the the payment was not submitted using
      the current rest server
    """
    url = 'accounts/{address}/payments'
    url = url.format(address=address)
    response = self._request(url, kwargs)
    for payment in response['payments']:
      yield Payment(**payment['payment']), payment['client_resource_id']

  def get_trustlines(self, address, **kwargs):
    """Get an account's existing trustlines

    :param address: The account to be queried
    :param currency: Limit the search to this currency
    :param counterparty: Limit the search to this counterparty

    :return: A generator of trustlines
    """
    url = 'accounts/{address}/trustlines'.format(address=address)
    response = self._request(url, kwargs)
    for trustline in response['trustlines']:
      yield Trustline(**trustline)

  def post_trustline(self, address, secret, trustline, **kwargs):
    """Add or modify trustline

    :params address: The ripple account that will be modified
    :param secret: The key that will be used to sign the transaction
    :param trustline: The new trustline
    :param bool allow_rippling: Enable rippling. Defaults to True

    :return: The modified trustline, the transaction hash and the ledger number
    :rtype: (Trustline, hash, int)
    """
    url = 'accounts/{address}/trustlines'
    url = url.format(address=address)
    response = self._request(url, data={'trustline': trustline}, secret=secret)
    return (
      Trustline(**response['trustline']),
      response['hash'],
      int(response['ledger']),
    )

  def get_notification(self, address, hash, **kwargs):
    """Retrieve a notification corresponding to a transaction

    The notification is retrieved from either rippled's historical database
    or ripple-rest's local database if the transaction was submitted
    through this instance of ripple-rest

    :param address: A Ripple account
    :param hash: Transaction identifier

    :return: The requested notification
    """
    url = 'accounts/{address}/notifications/{hash}'
    url = url.format(address=address, hash=hash)
    response = self._request(url, parameters=kwargs)
    return response['notification']

  def get_connection_status(self):
    """Return the rippled connection status

    :return: If the connection is active
    :rtype: bool
    """
    return self._request('server/connected')['connected']

  def get_server_info(self):
    """Get the ripple-rest and rippled information

    :return: A dictionary with multiple pieces of information
    """
    return self._request('server')


  def get_uuid(self):
    """Ask the rest server for a random UUID

    :return: uuid (uuid): The UUID provided by the server
    """
    return self._request('uuid')

  def get_transaction(self, hash):
    """Get a transaction by hash

    :return: The requested transaction
    """
    url = 'transactions/{hash}'
    url = url.format(hash=hash)
    response = self._request(url)
    return response['transaction']
