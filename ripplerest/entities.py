"""These are the ripple REST objects as defined in `the official schemata <https://github.com/ripple/ripple-rest/tree/develop/schemas>`_.

All classes are dictionaries, so if you want to change their attributes you
have to access the corresponding dictionary values instead of the members.

At this time there is no validation of the fields.
"""

class AccountSettings(dict):
  """Account Settings
  
  :var account: The Ripple address of the account in question
  :var regular_key: The hash of an optional additional public key
    that can be used for signing and verifying transactions
  :var url: The domain associated with this account. The ripple.txt file can
    be looked up to verify this information
  :var email_hash: The MD5 128-bit hash of the account owner's email address
  :var message_key: An optional public key, represented as hex, that can be set
    to allow others to send encrypted messages to the account owner
  :var transfer_rate: A number representation of the rate charged each time a
    holder of currency issued by this account transfers it. By default the rate
    is 100. A rate of 101 is a 1% charge on top of the amount being
    transferred. Up to nine decimal places are supported
  :var require_destination_tag: If set to true incoming payments will only be
    validated if they include a destination_tag. This may be used primarily by
    gateways that operate exclusively with hosted wallets",
  :var require_authorization: If set to true incoming trustlines will only be
    validated if this account first creates a trustline to the counterparty
    with the authorized flag set to true. This may be used by gateways to
    prevent accounts unknown to them from holding currencies they issue
  :var disallow_xrp: If set to true incoming XRP payments will be allowed
  :var transaction_sequence: A string representation of the last sequence
    number of a validated transaction created by this account
  :var trustline_count: The number of trustlines owned by this account.
    This value does not include incoming trustlines where this account has not
    explicitly reciprocated trust
  :var ledger: The string representation of the index number of the ledger
    containing these account settings or, in the case of historical queries,
    of the transaction that modified these settings
  :var hash: If this object was returned by a historical query this value will
    be the hash of the transaction that modified these settings.
  """
  def __init__(self, account, **kwargs):
    self.update(kwargs)
    self['account'] = RippleAddress(account)

class Amount(dict):
  """An Amount on the Ripple Protocol, used for IOUs and XRP
  
  :var value: The quantity of the currency, denoted as a string to retain
    floating point precision
  :var currency: The currency expressed as a three-character code
  :var issuer: The Ripple account address of the currency's issuer or gateway,
    or an empty string if the currency is XRP
  :var counterparty: The Ripple account address of the currency's issuer or
    gateway, or an empty string if the currency is XRP
  """
  def __init__(self, value, currency, issuer=None, counterparty=None,
    **kwargs):
    self.update(kwargs)
    self['value'] = str(value)
    self['currency'] = Currency(currency)
    if issuer: self['issuer'] = RippleAddress(issuer)
    if counterparty: self['counterparty'] = RippleAddress(counterparty)

class Balance(dict):
  """A simplified representation of an account Balance
  
  :var value: The quantity of the currency, denoted as a string to retain
    floating point precision
  :var currency: The currency expressed as a three-character code
  :var counterparty: The Ripple account address of the currency's issuer or
    gateway, or an empty string if the currency is XRP
  """
  def __init__(self, value, currency, issuer=None, counterparty=None,
    **kwargs):
    self.update(kwargs)
    self['value'] = value
    self['currency'] = Currency(currency)
    self['issuer'] = RippleAddress(issuer) if issuer else None
    self['counterparty'] = RippleAddress(counterparty) if counterparty else None

class Currency(str):
  """A three letter code which represent a currency.
  
  It is an alias for a str object and is the three-character code or hex string
  used to denote currencies
  """
  pass
  
class Notification(dict):
  """Notification of a transaction
  
  :var account: The Ripple address of the account to which the notification
    pertains
  :var type: The resource type this notification corresponds to. Possible
    values are "payment", "order", "trustline", "accountsettings"
  :var direction: The direction of the transaction, from the perspective of
    the account being queried. Possible values are "incoming", "outgoing", and
    "passthrough"
  :var state: The state of the transaction from the perspective of the Ripple
    Ledger. Possible values are "validated" and "failed"
  :var result: The rippled code indicating the success or failure type of the
    transaction. The code "tesSUCCESS" indicates that the transaction was
    successfully validated and written into the Ripple Ledger. All other codes
    will begin with the following prefixes: "tec", "tef", "tel", or "tej"
  :var ledger: The string representation of the index number of the ledger
    containing the validated or failed transaction. Failed payments will only
    be written into the Ripple Ledger if they fail after submission to a
    rippled and a Ripple Network fee is claimed
  :var hash: The 256-bit hash of the transaction. This is used throughout the
    Ripple protocol as the unique identifier for the transaction
  :var timestamp: The timestamp representing when the transaction was validated
    and written into the Ripple ledger
  :var transaction_url: A URL that can be used to fetch the full resource this
    notification corresponds to
  :var previous_notification_url: A URL that can be used to fetch the
    notification that preceded this one chronologically
  :var next_notification_url: A URL that can be used to fetch the notification
    that followed this one chronologically
  """
  def __init__(self, **kwargs):
    self.update(kwargs)

class Payment(dict):
  """A flattened Payment object
  
  :var source_slippage: An optional cushion for the source_amount to increase
    the likelihood that the payment will succeed. The source_account will never
    be charged more than source_amount.value + source_slippage
  :var partial_payment: A boolean that, if set to true, indicates that this
    payment should go through even if the whole amount cannot be delivered
    because of a lack of liquidity or funds in the source_account account
  :var timestamp: The timestamp representing when the payment was validated and
    written into the Ripple ledger
  :var destination_tag: A string representing an unsigned 32-bit integer most
    commonly used to refer to a receiver's hosted account at a Ripple gateway
  :var destination_account:
  :var source_tag: A string representing an unsigned 32-bit integer most 
    commonly used to refer to a sender's hosted account at a Ripple gateway
  :var result: The rippled code indicating the success or failure type of the
    payment. The code "tesSUCCESS" indicates that the payment was successfully
    validated and written into the Ripple Ledger. All other codes will begin
    with the following prefixes: "tec", "tef", "tel", or "tej"
  :var source_amount: An optional amount that can be specified to constrain
    cross-currency payments
  :var destination_balance_changes: Parsed from the validated transaction
    metadata, this array represents the changes to balances held by the
    destination_account. For those receiving payments this is important to
    check because if the partial_payment flag is set this value may be less
    than the destination_amount
  :var source_balance_changes: Parsed from the validated transaction metadata,
    this array represents all of the changes to balances held by the
    source_account. Most often this will have one amount representing the
    Ripple Network fee and, if the source_amount was not XRP, one amount
    representing the actual source_amount that was sent
  :var hash: The 256-bit hash of the payment. This is used throughout the
    Ripple protocol as the unique identifier for the transaction
  :var destination_amount: The amount the destination_account will receive
  :var state: The state of the payment from the perspective of the Ripple
    Ledger. Possible values are "validated" and "failed" and "new" if the
    payment has not been submitted yet
  :var paths: A "stringified" version of the Ripple PathSet structure that
    users should treat as opaque
  :var no_direct_ripple: A boolean that can be set to true if paths are
    specified and the sender would like the Ripple Network to disregard any
    direct paths from the source_account to the destination_account. This may
    be used to take advantage of an arbitrage opportunity or by gateways
    wishing to issue balances from a hot wallet to a user who has mistakenly
    set a trustline directly to the hot wallet
  :var ledger: The string representation of the index number of the ledger
    containing the validated or failed payment. Failed payments will only be
    written into the Ripple Ledger if they fail after submission to a rippled
    and a Ripple Network fee is claimed
  :var direction: The direction of the payment, from the perspective of the
    account being queried. Possible values are "incoming", "outgoing", and
    "passthrough"
  :var source_account: The Ripple account address of the Payment sender
  :var fee: The Ripple Network transaction fee, represented in whole XRP
    (NOT "drops", or millionths of an XRP, which is used elsewhere in the
    Ripple protocol)
  :var invoice_id: A 256-bit hash that can be used to identify a particular
    payment
  """
  def __init__(self, source_account, destination_account, destination_amount,
    **kwargs):
    self.update(kwargs)
    self['source_account'] = RippleAddress(source_account)
    self['destination_account'] = RippleAddress(destination_account)
    self['destination_amount'] = Amount(**destination_amount)

class RippleAddress(str):
  """A Ripple account address
  """
  pass

class Trustline(dict):
  """A simplified Trustline object
  
  :var authorized_by_counterparty: Set to true if the counterparty has
    explicitly authorized the account to hold currency it issues. This is only
    necessary if the counterparty's settings include
    require_authorization_for_incoming_trustlines
  :var limit: The maximum value of the currency that the account may hold
    issued by the counterparty
  :var reciprocated_limit: The maximum value of the currency that the
    counterparty may hold issued by the account
  :var authorized_by_account: Set to true if the account has explicitly
    authorized the counterparty to hold currency it issues. This is only
    necessary if the account's settings include
    require_authorization_for_incoming_trustlines
  :var counterparty_allows_rippling: If true it indicates that the counterparty
    allows pairwise rippling out through this trustline
  :var account_allows_rippling: If true it indicates that the account allows
    pairwise rippling out through this trustline
  :var hash: If this object was returned by a historical query this value will
    be the hash of the transaction that modified this Trustline. The
    transaction hash is used throughout the Ripple Protocol to uniquely
    identify a particular transaction
  :var counterparty: The other party in this trustline
  :var previous: If the trustline was changed this will be a full Trustline
    object representing the previous values. If the previous object also had a
    previous object that will be removed to reduce data complexity. Trustline
    changes can be walked backwards by querying the API for previous.hash
    repeatedly
  :var currency: The code of the currency in which this trustline denotes trust
  :var ledger: The string representation of the index number of the ledger
    containing this trustline or, in the case of historical queries, of the
    transaction that modified this Trustline
  :var account: The account from whose perspective this trustline is being
    viewed
  """
  def __init__(self, account, counterparty, limit, currency, **kwargs):
    self.update(kwargs)
    self['account'] = RippleAddress(account)
    self['counterparty'] = RippleAddress(counterparty)
    self['limit'] = str(limit)
    self['currency'] = Currency(currency)
