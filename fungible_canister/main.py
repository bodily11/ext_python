from kybra import TypedDict,nat,ic,Variant,Record,init,pre_upgrade,post_upgrade,blob,nat16,nat64,query,update,Principal,opt,nat8

class FunctionCallResult(Variant, total=False):
    ok: str
    err: str

class Event(Record):
    event_type: str
    description: str
    timestamp: nat
    actor_principal: str

class TransferEvent(Record):
    transaction_id: nat
    from_address: str
    to_address: str
    timestamp: nat
    token_amount: nat
    transfer_type: str

class HttpRequest(Record):
    method: str
    url: str
    headers: list[tuple[str,str]]
    body: blob

class HttpResponse(Record):
    status_code: nat16
    headers: list[tuple[str,str]]
    body: blob

class Canister(Record):
    name: str
    description: str
    logo: str
    symbol: str
    decimals: nat8
    fee_amount: nat
    burn_amount: nat
    fee_address: str
    admin_principals: list[str]
    burn_address: str
    max_token_supply: nat
    minted_tokens: nat
    owner: str

class Database(TypedDict):
    registry: dict[str, nat]
    events: list[Event]
    transactions: list[TransferEvent]
    canister_metadata: Canister

def big(number: int) -> nat:
    return int(number * 1E8)

def small(number: nat) -> float:
    return float(float(number) / 1e8)

db: Database = {
        'registry': {},
        'events':[],
        'transactions':[],
        'canister_metadata':{
            'name':'',
            'description': '',
            'logo':'',
            'symbol':'',
            'decimals':8,
            'fee_amount':big(1),
            'burn_amount':big(1),
            'fee_address':'',
            'burn_address': '0000000000000000000000000000000000000000000000000000000000000001',
            'admin_principals': [],
            'max_token_supply': big(10_000_000),
            'minted_tokens':0,
            'owner':''
        }
    }

class StableStorage(TypedDict):
    db: str

stable_storage: StableStorage = ic.stable_storage()

def new_event(event_type: str, description: str) -> bool:
    timestamp = ic.time()
    actor_principal = str(ic.caller())
    db['events'].append({
        'event_type':event_type,
        'description':description,
        'timestamp':timestamp,
        'actor_principal':actor_principal
    })
    return True

def new_transfer_event(from_address: str, to_address: str, token_amount: nat, transfer_type: str) -> bool:
    timestamp = ic.time()
    db['transactions'].append({
        'transaction_id':len(db['transactions']),
        'from_address':from_address,
        'to_address':to_address,
        'timestamp':timestamp,
        'transfer_type':transfer_type,
        'token_amount':token_amount,
    })
    return True

@init
def init_():
    global db
    ic.print('init')
    
    db['registry'][db['canister_metadata']['burn_address']] = 0
    db['registry'][db['canister_metadata']['fee_address']] = 0

    stable_storage['db'] = str(db)

    new_event('Canister Created','New canister deployed.')
    new_event('Metadata',f"Token name set to {db['canister_metadata']['name']}")
    new_event('Metadata',f"Token description set to {db['canister_metadata']['description']}")
    new_event('Metadata',f"Logo set to {db['canister_metadata']['logo']}")
    new_event('Metadata',f"Symbol set to {db['canister_metadata']['symbol']}")
    new_event('Metadata',f"Decimals set to {db['canister_metadata']['decimals']}")
    new_event('Metadata',f"Fee amount set to {db['canister_metadata']['fee_amount']}")
    new_event('Metadata',f"Fee address set to {db['canister_metadata']['fee_address']}")
    new_event('Metadata',f"Admin principals set to {', '.join(db['canister_metadata']['admin_principals'])}")
    new_event('Metadata',f"Burn address set to {db['canister_metadata']['burn_address']}")
    new_event('Metadata',f"Max token supply set to {db['canister_metadata']['max_token_supply']}")
    new_event('Metadata',f"Minted tokens set to {db['canister_metadata']['minted_tokens']}")
    new_event('Metadata',f"Owner set to {db['canister_metadata']['owner']}")

@pre_upgrade
def pre_upgrade_():
    ic.print('pre_upgrade')
    stable_storage['db'] = str(db)

@post_upgrade
def post_upgrade_():
    global db
    ic.print('post_upgrade')
    db = eval(stable_storage['db'])
    new_event('Upgrade',f"Canister was upgraded")

@query
def get_cycles() -> nat64:
    return ic.canister_balance()

@query
def get_events() -> list[Event]:
    return db['events']

@query
def get_transactions() -> list[TransferEvent]:
    return db['transactions']

@query
def get_registry() -> list[tuple[str, nat]]:
    return list(db['registry'].items())

@query
def get_metadata() -> Canister:
    return db['canister_metadata']

@update
def set_token_name(name: str) -> FunctionCallResult:
    db['canister_metadata']['name'] = name
    return {'ok':'Token name set successfully.'}

@update
def set_token_description(description: str) -> FunctionCallResult:
    db['canister_metadata']['description'] = description
    return {'ok':'Token description set successfully.'}

@update
def set_token_logo(logo: str) -> FunctionCallResult:
    db['canister_metadata']['logo'] = 'data:image/png;base64,' + logo
    return {'ok':'Token logo set successfully.'}

@update
def set_token_symbol(symbol: str) -> FunctionCallResult:
    db['canister_metadata']['symbol'] = symbol
    return {'ok':'Token symbol set successfully.'}

@update
def set_token_decimals(decimals: nat) -> FunctionCallResult:
    db['canister_metadata']['decimals'] = decimals
    return {'ok':'Token decimals set successfully.'}

@update
def set_token_fee_amount(fee_amount: nat) -> FunctionCallResult:
    db['canister_metadata']['fee_amount'] = fee_amount
    return {'ok':'Token fee amount set successfully.'}

@update
def set_token_fee_address(fee_address: str) -> FunctionCallResult:
    db['canister_metadata']['fee_address'] = fee_address
    return {'ok':'Token fee address set successfully.'}

@update
def set_token_burn_address(burn_address: str) -> FunctionCallResult:
    db['canister_metadata']['burn_address'] = burn_address
    return {'ok':'Token burn address set successfully.'}

@update
def set_token_max_token_supply(max_token_supply: nat) -> FunctionCallResult:
    db['canister_metadata']['max_token_supply'] = max_token_supply
    return {'ok':'Token max token supply set successfully.'}

@update
def set_token_owner(owner: str) -> FunctionCallResult:
    db['canister_metadata']['owner'] = owner
    return {'ok':'Token owner set successfully.'}

@update
def add_admin(admin_principal: str) -> FunctionCallResult:
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['admin_principals'].append(admin_principal)
        new_event('Add Admin',f'New principal {admin_principal} added as admin')
        return {'ok':'New admin added successfully.'}
    else:
        return {'err':'Only admin can call add admin.'}

@update
def remove_admin(admin_principal: str) -> FunctionCallResult:
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['admin_principals'].remove(admin_principal)
        new_event('Remove Admin',f'Admin principal {admin_principal} has been removed as admin')
        return {'ok':"Removing admin was successful."}
    else:
        return {'err':'Only admin can call remove admin'}

@query
def get_balance(address: str) -> nat:
    if address in db['registry']:
        return db['registry'][address]
    else:
        return 0

def sanitize_address(address: str) -> str:
    address = address.strip()
    if (len(address) == 63 or len(address) == 27) and '-' in address:
        final_address = str(Principal.from_str(address).to_account_id())[2:]
    else:
        final_address = str(address)
    return final_address

@update
def mint_token(token_amount: nat, to_address: str) -> FunctionCallResult:
    caller = str(ic.caller())
    to_address = sanitize_address(to_address)
    token_amount = big(token_amount)
    if caller in db['canister_metadata']['admin_principals']:
        if db['canister_metadata']['minted_tokens'] + token_amount <= db['canister_metadata']['max_token_supply']:
            if to_address not in db['registry']:
                db['registry'][to_address] = token_amount
            else:
                db['registry'][to_address] += token_amount
            
            db['canister_metadata']['minted_tokens'] += token_amount

            new_event('Token minted',f'{token_amount} was minted to {to_address}')
            new_transfer_event('',to_address,token_amount,'Minted')

            return {'ok': 'Token successfully minted.'}
        else:
            return {'err': 'Sorry, minting these tokens would put the supply over the stated maximum token supply.'}
    else:
        return {'err': 'You must be admin to call mint_token'}

def _transfer(from_address: str, to_address: str, token_amount: nat) -> FunctionCallResult:
    fee_address = sanitize_address(db['canister_metadata']['fee_address'])
    fee_amount = db['canister_metadata']['fee_amount']
    burn_address = sanitize_address(db['canister_metadata']['burn_address'])
    burn_amount = db['canister_metadata']['burn_amount']
    total_amount = token_amount + fee_amount + burn_amount
    
    if from_address in db['registry']:
        if db['registry'][from_address] >= total_amount:
            if len(to_address) == 64:
                if to_address not in db['registry']:
                    db['registry'][to_address] = 0
                
                db['registry'][from_address] -= total_amount
                db['registry'][to_address] += token_amount
                db['registry'][fee_address] += fee_amount
                db['registry'][burn_address] += burn_amount
                new_transfer_event(from_address,to_address,token_amount,'Transfer')
                new_transfer_event(from_address,fee_address,fee_amount,'Fee')
                new_transfer_event(from_address,burn_address,burn_amount,'Burn')
                return {'ok':'Token transferred successfully'}
            else:
                return {'err':f'The to_address is length {len(to_address)} when it should be length 64'}
        else:
            return {'err':'You do not have enough tokens to make this transfer'}
    else:
        return {'err':'You do not own any of this token'}

@update
def admin_transfer(from_address: str, to_address: str, token_amount: nat) -> FunctionCallResult:
    to_address = sanitize_address(to_address)
    from_address = sanitize_address(from_address)
    fee_address = sanitize_address(db['canister_metadata']['fee_address'])
    fee_amount = db['canister_metadata']['fee_amount']
    burn_address = sanitize_address(db['canister_metadata']['burn_address'])
    burn_amount = db['canister_metadata']['burn_amount']
    token_amount = big(token_amount)
    total_amount = token_amount + fee_amount + burn_amount
    caller = str(ic.caller())
    if caller in db['canister_metadata']['admin_principals']:
        if from_address in db['registry']:
            if db['registry'][from_address] >= total_amount:
                if len(to_address) == 64:
                    if to_address not in db['registry']:
                        db['registry'][to_address] = 0

                    db['registry'][from_address] -= total_amount
                    db['registry'][to_address] += token_amount
                    db['registry'][fee_address] += fee_amount
                    db['registry'][burn_address] += burn_amount
                    
                    new_event('Admin Transfer',f'{token_amount} transferred from {from_address} to {to_address}')
                    new_transfer_event(from_address,to_address,token_amount,'Admin Transfer')
                    new_transfer_event(from_address,fee_address,fee_amount,'Fee')
                    new_transfer_event(from_address,burn_address,burn_amount,'Burn')
                    return {'ok':'Token transferred successfully.'}
                else:
                    return {'err':f'The to_address is length {len(to_address)} when it should be length 64.'}
            else:
                return {'err':'You do not have enough token to make this transfer.'}
        else:
            return {'err':'You do not own any of this token.'}
    else:
        return {'err':'You must be admin in order to call admin transfer.'}

@update
def burn(token_amount: nat) -> FunctionCallResult:
    fee_address = sanitize_address(db['canister_metadata']['fee_address'])
    fee_amount = db['canister_metadata']['fee_amount']
    burn_address = sanitize_address(db['canister_metadata']['burn_address'])
    burn_amount = db['canister_metadata']['burn_amount']
    token_amount = big(token_amount)
    total_amount = token_amount + fee_amount + burn_amount
    caller_address = str(ic.caller().to_account_id())[2:]

    if caller_address in db['registry']:
        if db['registry'][caller_address] >= total_amount:
            db['registry'][caller_address] -= total_amount
            db['registry'][burn_address] += token_amount + burn_amount
            db['registry'][fee_address] += fee_amount
            new_transfer_event(caller_address, burn_address, token_amount, 'Burn')
            new_transfer_event(caller_address, fee_address, token_amount, 'Fee')
            return {'ok':'Successfully burned the token'}
        else:
            return {'err':'Sorry you do not own that many tokens.'}
    else:
        return {'err':'Sorry you do not own any tokens.'}

@query
def http_request(request: HttpRequest) -> HttpResponse:
    burn_address = sanitize_address(db['canister_metadata']['burn_address'])
    minted_tokens = db['canister_metadata']['minted_tokens']
    if burn_address in db['registry']:
        burned_tokens_count = db['registry'][burn_address]
    else:
        burned_tokens_count = 0
    current_supply = sum(db["registry"].values())
    unique_holders = len(db['registry'])
    admin = ', '.join(db['canister_metadata']['admin_principals'])
    http_response_body = bytes(f'''
        <!DOCTYPE html>
        <html>
            <body>
                <div>
                    <table style="border-collapse:collapse; margin: 25px 0; min-width: 400px;">
                        <tr style="border-bottom: 1px solid #dddddd">
                            <th style="padding: 12px 15px;">Parameter</th>
                            <th style="padding: 12px 15px;">Value</th>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Token Name</td>
                            <td style="padding: 12px 15px;">{db['canister_metadata']['name']}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Description</td>
                            <td style="padding: 12px 15px;">{db['canister_metadata']['description']}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Logo</td>
                            <td style="padding: 12px 15px;">{db['canister_metadata']["logo"]}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Symbol</td>
                            <td style="padding: 12px 15px;">{db['canister_metadata']["symbol"]}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Decimals</td>
                            <td style="padding: 12px 15px;">{db['canister_metadata']["decimals"]}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Fee Amount (per txn)</td>
                            <td style="padding: 12px 15px;">{small(db['canister_metadata']["fee_amount"])}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Burn Amount (per txn)</td>
                            <td style="padding: 12px 15px;">{small(db['canister_metadata']["burn_amount"])}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Fee Address</td>
                            <td style="padding: 12px 15px;">{sanitize_address(db['canister_metadata']["fee_address"])}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Owner</td>
                            <td style="padding: 12px 15px;">{db['canister_metadata']["owner"]}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">List of Admins</td>
                            <td style="padding: 12px 15px;">{admin}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Burn Address</td>
                            <td style="padding: 12px 15px;">{sanitize_address(burn_address)}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Max Token Supply</td>
                            <td style="padding: 12px 15px;">{small(db['canister_metadata']["max_token_supply"])}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Minted token total</td>
                            <td style="padding: 12px 15px;">{small(minted_tokens)}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Burned token total</td>
                            <td style="padding: 12px 15px;">{small(burned_tokens_count)}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Current Supply</td>
                            <td style="padding: 12px 15px;">{small(current_supply)}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dddddd">
                            <td style="padding: 12px 15px;">Unique Holders</td>
                            <td style="padding: 12px 15px;">{unique_holders}</td>
                        </tr>
                    </table>
                </div>
                <div>
                    <table style="border-collapse:collapse; margin: 25px 0; min-width: 400px;">
                        <tr style="border-bottom: 1px solid #dddddd">
                            <th style="padding: 12px 15px;">Event Type</th>
                            <th style="padding: 12px 15px;">Timestamp</th>
                            <th style="padding: 12px 15px;">Description</th>
                        </tr>
                        {''.join(['<tr style="border-bottom: 1px solid #dddddd"><td style="padding: 12px 15px;">' + x['event_type'] + '</td><td style="padding: 12px 15px;">' + str(x['timestamp']) + '</td><td style="padding: 12px 15px;">' + x['description'] + '</td></tr>' for x in db['events']])}
                    </table>
                </div>
            </body>
        </html>
    ''',encoding='utf-8')

    return {
        'status_code':200,
        'headers':[('content-type','text/html')],
        'body':http_response_body
    }

###
# SUPPORTING EXT
###

# ext_transfer
class User(Variant, total=False):
    address: str
    principal: Principal

# ext_transfer
class TransferRequest(Record):
    from_ : User
    to : User
    token : str
    amount : nat
    memo : blob
    nonce: opt[nat]
    notify : bool
    subaccount : opt[list[nat8]]

# ext_transfer
class TransferError(Variant, total=False):
    CannotNotify: str
    InsufficientAllowance: str
    InsufficientBalance: str
    InvalidToken: str
    Other: str
    Rejected: str
    Unauthorized: str

# ext_transfer
class TransferResponse(Variant, total=False):
    ok: nat
    err: TransferError

# ext_transfer
@update
def transfer(transfer_request: TransferRequest) -> TransferResponse:
    if transfer_request['subaccount']:
        sub_account_num = int.from_bytes(bytes(transfer_request['subaccount']),'big')
    else:
        sub_account_num = 0

    if 'address' in transfer_request['from_']:
        from_address = transfer_request['from_']['address']
    elif 'principal' in transfer_request['from_']:
        from_address = str(transfer_request['from_']['principal'].to_account_id(sub_account_num))[2:]
    else:
        return {'err':{'Other':'Invalid from parameter, should be address or principal.'}}
    
    if 'address' in transfer_request['to']:
        to_address = transfer_request['to']['address']
    elif 'principal' in transfer_request['to']:
        to_address = str(transfer_request['to']['principal'].to_account_id())[2:]
    else:
        return {'err':{'Other':'Invalid from parameter, should be address or principal.'}}
    
    result = _transfer(from_address,to_address,transfer_request['amount'])

    if 'ok' in result:
        return {'ok': 1}
    elif 'err' in result:
        return {'err':{'Other':result['err']}}
    else:
        return {'err':{'Other':'Unknown result, please contact token owners.'}}

# ext_balance
class BalanceRequest(Record):
    token: opt[str]
    user: User

# ext_balance
class CommonError(Variant, total=False):
   InsufficientBalance: str
   InvalidToken: str
   Other: str
   Unauthorized: str

# ext_balance
class BalanceResponse(Variant, total=False):
    ok: nat
    err: CommonError

# ext_balance
@query
def balance(balance_request: BalanceRequest) -> BalanceResponse:
    if 'address' in balance_request['user']:
        user_address = balance_request['user']['address']
    elif 'principal' in balance_request['user']:
        user_address = str(balance_request['user']['principal'].to_account_id())[2:]
    else:
        return {'err':{'Other':'Sorry, invalid entry. Requires address or principal.'}}
    
    if user_address in db['registry']:
        balance = db['registry'][user_address]
    else:
        balance = 0
    return {'ok':balance}

# ext_metadata
class MetadataRecord(Record):
    name: str
    symbol: str
    decimals: nat8
    metadata: opt[list[nat8]]
    ownerAccount: str

# ext_metadata
class MetadataNonfungible(Record):
    metadata: opt[blob]

# ext_metadata
class Metadata(Variant, total=False):
    fungible: MetadataRecord
    nonfungible: MetadataNonfungible

# ext_metadata
class MetadataResponse(Variant, total=False):
    ok: Metadata
    err: CommonError

# ext_metadata
@query
def metadata() -> MetadataResponse:
    return {
        'ok':{
            'fungible':{
                'name':db['canister_metadata']['name'],
                'symbol':db['canister_metadata']['symbol'],
                'decimals':db['canister_metadata']['decimals'],
                'metadata':None,
                'ownerAccount':db['canister_metadata']['owner']
            }
        }
    }

# ext_supply
class NatResponse(Variant, total=False):
    ok: nat
    err: CommonError

# ext_supply
@query
def supply() -> NatResponse:
    return {'ok':sum(db["registry"].values())}

# ext_get_fee
@query
def getFee() -> NatResponse:
    return {'ok':db['canister_metadata']['fee_amount']}

###
# ICRC-1 Support
###

# icrc1_name

# icrc1_symbol

# icrc1_decimals

# icrc1_fee

# icrc1_metadata

# icrc1_total_supply

# icrc1_minting_account

# icrc_balance_of

# icrc1_transfer

# icrc1_supported_standards

###
# ICRC-2 Support
###

# icrc2_approve

# icrc2_transfer_from

# icrc2_allowance