from kybra import TypedDict,nat,query,update,Record,ic,blob,nat16,nat64,pre_upgrade,post_upgrade,init,opt,Principal,Variant,nat8,nat32,float64,Func,Query,method,Canister,Async,CanisterResult
import math
from typing import TypeAlias

class TraitType(Variant, total=False):
    number: float64
    string: str

class NftMetadata(Record):
    name: str
    description: str
    dynamic_traits_text: list[tuple[str,str]]
    dynamic_traits_number: list[tuple[str,float64]]
    static_traits_text: list[tuple[str,str]]
    static_traits_number: list[tuple[str,float64]]
    rarity_scores: opt[list[tuple[str,float64]]]
    license: str

class UpdateMetadataText(Record):
    nft_index: nat
    trait_type: str # static vs dynamic
    trait_format: str # text vs number
    trait_name: str # trait category name
    trait_value: str # trait value

class UpdateMetadataNumber(Record):
    nft_index: nat
    trait_type: str # static vs dynamic
    trait_format: str # text vs number
    trait_name: str # trait category name
    trait_value: float64 # trait value

class Nft(Record):
    nft_index: nat
    asset_url: str
    thumbnail_url: str
    asset_index: opt[nat]
    asset_type: str
    metadata: NftMetadata

class NftForMinting(Record):
    nft_index: opt[nat]
    asset_url: str
    thumbnail_url: str
    asset_index: opt[nat]
    asset_type: str
    metadata: NftMetadata
    to_address: str

class ManyMintResult(Variant, total=False):
    ok: list[str]
    err: str

class TransferEvent(Record):
    transaction_id: nat
    from_address: str
    to_address: str
    timestamp: nat
    nft_index: nat
    transfer_type: str

### http_request and streaming methods ###
HeaderField = tuple[str, str]

class HttpRequest(Record):
    method: str
    url: str
    headers: list[HeaderField]

class Token(Record):
    arbitrary_data: str

class StreamingCallbackHttpResponse(Record):
    body: blob
    token: opt[Token]

Callback: TypeAlias = Func(Query[[Token], StreamingCallbackHttpResponse])

class CallbackStrategy(Record):
    callback: Callback
    token: Token

class StreamingStrategy(Variant, total=False):
    Callback: CallbackStrategy

class HttpResponse(Record):
    status_code: nat16
    headers: list[HeaderField]
    body: blob
    streaming_strategy: opt[StreamingStrategy]
    upgrade: opt[bool]
### http_request and streaming methods ###

class FunctionCallResult(Variant, total=False):
    ok: str
    err: str

class FunctionCallResultFloat64(Variant, total=False):
    ok: float64
    err: str

class FunctionCallResultNat(Variant, total=False):
    ok: nat
    err: str

class Event(Record):
    event_type: str
    description: str
    timestamp: nat
    actor_principal: str

class CanisterMeta(Record):
    collection_name: str
    creator_royalty: nat
    royalty_address: str
    admin_principals: list[str]
    burn_address: str
    max_number_of_nfts_to_mint: nat
    owner: str
    license: str
    avatar: opt[blob]
    banner: opt[blob]
    blurb: opt[str]
    brief: opt[str]
    collection: opt[blob]
    commission: opt[nat]
    description: opt[str]
    detailpage: opt[str]
    keywords: opt[str]
    twitter: opt[str]
    discord: opt[str]
    distrikt: opt[str]
    dscvr: opt[str]
    web: opt[str]

class SetCanister(Record):
    collection_name: opt[str]
    creator_royalty: opt[nat]
    royalty_address: opt[str]
    max_number_of_nfts_to_mint: opt[nat]
    owner: opt[str]
    license: opt[str]
    avatar: opt[blob]
    banner: opt[blob]
    blurb: opt[str]
    brief: opt[str]
    collection: opt[blob]
    commission: opt[nat]
    description: opt[str]
    detailpage: opt[str]
    keywords: opt[str]
    twitter: opt[str]
    discord: opt[str]
    distrikt: opt[str]
    dscvr: opt[str]
    web: opt[str]

class Asset(Record):
    file_name: str
    asset_bytes: list[blob]
    thumbnail_bytes: blob
    file_type: str

class AssetForUpload(Record):
    file_name: str
    asset_bytes: blob
    thumbnail_bytes: blob
    file_type: str

class EditAsset(Record):
    file_name: opt[str]
    asset_bytes: opt[blob]
    thumbnail_bytes: opt[blob]
    file_type: opt[str]

class ManualCondition(Record):
    display_flag: bool

# class RepeatedTimeCondition(Record):
#     start: nat
#     duration: nat
#     repeat: str

# class DataCondition(Record):
#     transfers: opt[nat]

class SingleTimeCondition(Record):
    change_after: nat

class Conditions(Variant, total=False):
    single_time_condition: SingleTimeCondition
    # repeated_time_condition: RepeatedTimeCondition
    # data_condition: DataCondition
    manual_condition: ManualCondition

class AssetCategory(Record):
    category_type: Conditions
    priority: nat
    asset_category: str

class Database(TypedDict):
    registry: dict[nat, str]
    address_registry: dict[str, list[nat]]
    nfts: dict[nat, Nft]
    transactions: list[TransferEvent]
    events: list[Event]
    assets: dict[nat,dict[str,Asset]]
    all_rarity_scores: dict[str, dict[nat, float64]]
    asset_categories: dict[str, AssetCategory]
    canister_metadata: CanisterMeta

class StableStorage(TypedDict):
    db: str

stable_storage: StableStorage = ic.stable_storage()

db: Database = {
        'registry': {},
        'address_registry': {},
        'nfts':{},
        'transactions':[],
        'events':[],
        'assets':{},
        'all_rarity_scores':{},
        'asset_categories': {},
        'canister_metadata':{
            'collection_name': '',
            'creator_royalty': 0,
            'royalty_address':'',
            'admin_principals': [],
            'burn_address': '0000000000000000000000000000000000000000000000000000000000000001',
            'max_number_of_nfts_to_mint': 0,
            'owner':'',
            'license':'',
            'avatar':None,
            'banner':None,
            'blurb':'',
            'brief':'',
            'collection':None,
            'commission': None,
            'description': '',
            'detailpage':'interactive_nfts_or_videos',
            'keywords':'',
            'twitter':'',
            'discord':'',
            'distrikt':'',
            'dscvr':'',
            'web':''
        }
    }

def new_event(event_type: str, description: str) -> bool:
    """
    Adds a new event to the events table.

	Parameters:
		event_type (str): The category you would like to set for this event. Allows any string.
		description (str): A more detailed description for the event. Often includes data.

	Returns:
		Bool: Indicates whether the event was successfully saved or not.
    """
    timestamp = ic.time()
    actor_principal = str(ic.caller())
    db['events'].append({
        'event_type':event_type,
        'description':description,
        'timestamp':timestamp,
        'actor_principal':actor_principal
    })
    return True

def new_transfer_event(from_address: str, to_address: str, nft_index: nat, transfer_type: str) -> bool:
    '''
    Adds a new transaction to the transactions table. All NFT txns of any kind should show up here.
    '''
    timestamp = ic.time()
    db['transactions'].append({
        'transaction_id':len(db['transactions']),
        'from_address':from_address,
        'to_address':to_address,
        'timestamp':timestamp,
        'transfer_type':transfer_type,
        'nft_index':nft_index,
    })
    return True
                        
@init
def init_():
    '''
    This only runs once the first time you deploy the canister. We set db in stable storage and initialize a few events.
    '''
    ic.print('init')
    stable_storage['db'] = str(db)

    new_event('Canister Created','New canister deployed.')
    new_event('Add Admin',f'Initial admin list set to {db["canister_metadata"]["admin_principals"]}')
    new_event('Set Burn Address',f'Initial burn address set to {db["canister_metadata"]["burn_address"]}')

@pre_upgrade
def pre_upgrade_():
    '''
    This runs before every upgrade. We serialize our entire database as a string for now. This won't work with Principal or other custom types.
    '''
    ic.print('pre_upgrade')
    stable_storage['db'] = str(db)

@post_upgrade
def post_upgrade_():
    '''
    This runs after every upgrade, re-initializing our database in db.
    '''
    global db
    ic.print('post_upgrade')
    db = eval(stable_storage['db'])
    new_event('Upgrade','Canister was upgraded')

@query
def get_asset_categories() -> list[tuple[str, AssetCategory]]:
    return list(db['asset_categories'].items())

@update
def trigger_reveal_on(asset_category_name: str) -> FunctionCallResult:
    condition = db['asset_categories'][asset_category_name]['category_type']
    if 'manual_condition' in condition:
        condition['manual_condition']['display_flag'] = True
        return {'ok':f'Display for {asset_category_name} was successfully switched to True.'}
    else:
        return {'err':f'Sorry, {asset_category_name} is not a manually triggered condition and cannot be switched to True.'}

def trigger_reveal_off(asset_category_name: str) -> FunctionCallResult:
    condition = db['asset_categories'][asset_category_name]['category_type']
    if 'manual_condition' in condition:
        condition['manual_condition']['display_flag'] = False
        return {'ok':f'Display for {asset_category_name} was successfully switched to True.'}
    else:
        return {'err':f'Sorry, {asset_category_name} is not a manually triggered condition and cannot be switched to False.'}

def determine_asset_category() -> str:
    all_matching_conditions: list[tuple[str,nat]] = []
    current_timestamp = ic.time()
    for asset_category_name,asset_category in db['asset_categories'].items():
        condition = asset_category['category_type']
        if 'manual_condition' in condition:
            if condition['manual_condition']['display_flag']:
                all_matching_conditions.append((asset_category_name,db['asset_categories'][asset_category_name]['priority']))
        if 'single_time_condition' in condition:
            if current_timestamp > condition['single_time_condition']['change_after']:
                all_matching_conditions.append((asset_category_name,db['asset_categories'][asset_category_name]['priority']))
    if len(all_matching_conditions) > 0:
        final_condition = max(all_matching_conditions,key=lambda item:item[1])
        return final_condition[0]
    else:
        return 'start'

def sanitize_address(address: str) -> str:
    '''
    Cleans up a user principal, canister, or address with spaces and returns a normal address.
    Removes extra spaces, checks for Principal or canister, uses default sub-account, and returns final address
    '''
    address = address.strip()
    if (len(address) == 63 or len(address) == 27) and '-' in address:
        final_address = str(Principal.from_str(address).to_account_id())[2:]
    else:
        final_address = str(address)
    return final_address

@query
def who_am_i() -> str:
    '''
    Returns the principal currently calling this function. Convenient at times as a sanity check.
    '''
    return str(ic.caller())

@query
def get_cycles() -> nat64:
    '''
    Returns the raw cycles left in the canister.
    '''
    return ic.canister_balance()

@query
def get_events() -> list[Event]:
    '''
    Returns a list of all events
    '''
    return db['events']

@query
def get_assets(asset_category: opt[str]) -> list[tuple[str,str]]:
    '''
    Returns a list of all assets. Assets are added when they are uploaded to the canister for the first time.
    '''
    if asset_category is None:
        asset_category = 'start'
    all_asset_categories = [(str(x[0]),x[1][asset_category]['file_name']) for x in db['assets'].items()]
    return all_asset_categories

@query
def get_transactions() -> list[TransferEvent]:
    '''
    Returns a list of transactions. Txns are fired on any NFT event for perfect provenance tracking.
    '''
    return db['transactions']

@query
def get_registry() -> list[tuple[nat, str]]:
    '''
    Returns the index-based NFT registry.
    '''
    return list(db['registry'].items())

@query
def get_nft(nft_index: nat) -> opt[Nft]:
    '''
    Returns a single NFT based on the NFT index.
    '''
    if nft_index in db['nfts']:
        return db['nfts'][nft_index]
    else:
        return None

@query
def get_all_nfts() -> list[tuple[nat, Nft]]:
    '''
    Returns a list of all NFTs.
    '''
    return list(db['nfts'].items())

@query
def get_owner(nft_index: nat) -> FunctionCallResult:
    '''
    Returns the owner address based on NFT index.
    '''
    if nft_index in db['registry']:
        return {'ok':db['registry'][nft_index]}
    else:
        return {'err':'Owner not found'}

@query
def get_tokens(address: str) -> list[nat]:
    '''
    Returns an array of NFT indexes owned by the address.
    '''
    if address in db['address_registry']:
        return db['address_registry'][address]
    else:
        return []

@update
def set_text_trait(update_metadata_text: UpdateMetadataText) -> FunctionCallResult:
    '''
    Set a static or dynamic "text" trait by name for a specific NFT index.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['nfts'][update_metadata_text['nft_index']]['metadata'][f"{update_metadata_text['trait_type']}_traits_{update_metadata_text['trait_format']}"][update_metadata_text['trait_name']] = update_metadata_text['trait_value']
        new_event('Set NFT trait',f"NFT {update_metadata_text['nft_index']} trait {update_metadata_text['trait_name']} was updated to {update_metadata_text['trait_value']}")
        return {'ok':f"{update_metadata_text['trait_name']} was successfully updated for index {update_metadata_text['nft_index']}."}
    else:
        return {'err':'You must be admin to call update nft trait.'}
    
@update
def set_number_trait(update_metadata_number: UpdateMetadataNumber) -> FunctionCallResult:
    '''
    Set a static or dynamic "number" trait by name for a specific NFT index.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['nfts'][update_metadata_number['nft_index']]['metadata'][f"{update_metadata_number['trait_type']}_traits_{update_metadata_number['trait_format']}"][update_metadata_number['trait_name']] = update_metadata_number['trait_value']
        new_event('Set NFT trait',f"NFT {update_metadata_number['nft_index']} trait {update_metadata_number['trait_name']} was updated to {update_metadata_number['trait_value']}")
        return {'ok':f"{update_metadata_number['trait_name']} was successfully updated for index {update_metadata_number['nft_index']}."}
    else:
        return {'err':'You must be admin to call update nft trait.'}

@query
def get_dynamic_traits_text(nft_index: nat, attribute_name: str) -> FunctionCallResult:
    '''
    Get a dynamic "text" trait by name for a specific NFT index.
    '''
    trait_attribute = [x[1] for x in db['nfts'][nft_index]['metadata']['dynamic_traits_text'] if x[0] == attribute_name]
    if len(trait_attribute) > 0:
        return {'ok':trait_attribute[0]}
    else:
        return {'err':'Dynamic trait not found.'}

@query
def get_dynamic_traits_number(nft_index: nat, attribute_name: str) -> FunctionCallResultFloat64:
    '''
    Get a dynamic "number" trait by name for a specific NFT index.
    '''
    trait_attribute = [x[1] for x in db['nfts'][nft_index]['metadata']['dynamic_traits_number'] if x[0] == attribute_name]
    if len(trait_attribute) > 0:
        return {'ok':trait_attribute[0]}
    else:
        return {'err':'Dynamic trait not found.'}

@query
def get_static_traits_text(nft_index: nat, attribute_name: str) -> FunctionCallResult:
    '''
    Get a static "text" trait by name for a specific NFT index.
    '''
    trait_attribute = [x[1] for x in db['nfts'][nft_index]['metadata']['static_traits_text'] if x[0] == attribute_name]
    if len(trait_attribute) > 0:
        return {'ok':trait_attribute[0]}
    else:
        return {'err':'Static trait not found.'}

@query
def get_static_traits_number(nft_index: nat, attribute_name: str) -> FunctionCallResultFloat64:
    '''
    Get a static "number" trait by name for a specific NFT index.
    '''
    trait_attribute = [x[1] for x in db['nfts'][nft_index]['metadata']['static_traits_number'] if x[0] == attribute_name]
    if len(trait_attribute) > 0:
        return {'ok':trait_attribute[0]}
    else:
        return {'err':'Static trait not found.'}

@query
def get_rarity_score(nft_index: nat, attribute_name: str) -> FunctionCallResultFloat64:
    '''
    Get a rarity score by name for a specific NFT index.
    '''
    if 'metadata' in db['nfts'][nft_index]:
        rarity_scores = db['nfts'][nft_index]['metadata']['rarity_scores']
        if rarity_scores: 
            trait_attribute = [x[1] for x in rarity_scores if x[0] == attribute_name]
            if len(trait_attribute) > 0:
                return {'ok':trait_attribute[0]}
            else:
                return {'err':'Rarity score not found.'}
        else:
            return {'err':'Rarity scores not found.'}
    else: return {'err':'Rarity scores not found.'}

@update
def compute_rarity() -> FunctionCallResult:
    '''
    Use static text and static number traits to create multiple rarity scores, saved in the NFT and separately in arrays.
    '''
    total_nfts = len(db['nfts'])
    final_sorted_scores: dict[str,list[float]] = {'information_score':[], 'probability_score':[],'expected_value':[],'open_rarity_score':[]}
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        trait_category_text_counts: dict[str, dict[str,int]] = {}
        trait_category_number_arrays: dict[str, list[float]] = {}

        for single_nft in db['nfts'].values():
            for trait_category,trait_value in single_nft['metadata']['static_traits_text']:
                if trait_category not in trait_category_text_counts:
                    trait_category_text_counts[trait_category] = {}
                if trait_value not in trait_category_text_counts[trait_category]:
                    trait_category_text_counts[trait_category][trait_value] = 0

                trait_category_text_counts[trait_category][trait_value] += 1

            for trait_category,trait_value in single_nft['metadata']['static_traits_number']:
                if trait_category not in trait_category_number_arrays:
                    trait_category_number_arrays[trait_category] = []

                trait_category_number_arrays[trait_category].append(trait_value)

        expected_value_sum = 0
        for single_nft in db['nfts'].values():
            information_bit_total = 0
            final_trait_probability = 1
            for trait_category,trait_value in single_nft['metadata']['static_traits_text']:
                trait_count = trait_category_text_counts[trait_category][trait_value]

                trait_probability = trait_count / total_nfts
                information_bit = -1 * math.log2(trait_probability)

                information_bit_total += information_bit
                final_trait_probability = final_trait_probability * trait_probability

            for trait_category,trait_value in single_nft['metadata']['static_traits_number']:
                number_array = sorted(trait_category_number_arrays[trait_category])
                trait_category_percentiles: dict[float, float] = {}
                for number in number_array:
                    percentile = number_array.index(number) / len(number_array)
                    trait_category_percentiles[trait_value] = percentile

                trait_probability = 1 - trait_category_percentiles[trait_value]
                information_bit = -1 * math.log2(trait_probability)

                information_bit_total += information_bit
                final_trait_probability = final_trait_probability * trait_probability

            # information_bit_total is total information from the NFT
            # final_trait_probability is product of all probabilities
            # now compute expected value for the denominator
            expected_value = information_bit_total * final_trait_probability

            new_rarity_data: list[tuple[str,float64]] = []
            new_rarity_data.append(('information_score', information_bit_total))
            new_rarity_data.append(('probability_score', final_trait_probability))
            new_rarity_data.append(('expected_value', expected_value))
            db['nfts'][single_nft['nft_index']]['metadata']['rarity_scores'] = new_rarity_data
            
            final_sorted_scores['information_score'].append(information_bit_total)
            final_sorted_scores['probability_score'].append(final_trait_probability)
            final_sorted_scores['expected_value'].append(expected_value)

            # we need this summed across NFTs for standardization purposes
            expected_value_sum += expected_value

        for single_nft in db['nfts'].values():
            rarity_scores = db['nfts'][single_nft['nft_index']]['metadata']['rarity_scores']
            if rarity_scores is not None:
                open_rarity_score = [x[1] for x in rarity_scores if x[0] == 'information_score'][0] / expected_value_sum
                rarity_scores.append(('open_rarity_score', open_rarity_score))
                final_sorted_scores['open_rarity_score'].append(open_rarity_score)

        final_sorted_scores['information_score'] = sorted(final_sorted_scores['information_score'])
        final_sorted_scores['probability_score'] = sorted(final_sorted_scores['probability_score'])
        final_sorted_scores['expected_value'] = sorted(final_sorted_scores['expected_value'])
        final_sorted_scores['open_rarity_score'] = sorted(final_sorted_scores['open_rarity_score'])

        information_percentiles: dict[float, float] = {}
        probability_percentiles: dict[float, float] = {}
        expected_value_percentiles: dict[float, float] = {}
        open_rarity_percentiles: dict[float, float] = {}

        for single_nft in db['nfts'].values():
            number_array = final_sorted_scores['information_score']
            for number in number_array:
                percentile = number_array.index(number) / len(number_array)
                information_percentiles[number] = 1 - percentile

            number_array = final_sorted_scores['probability_score']
            for number in number_array:
                percentile = number_array.index(number) / len(number_array)
                probability_percentiles[number] = percentile

            number_array = final_sorted_scores['expected_value']
            for number in number_array:
                percentile = number_array.index(number) / len(number_array)
                expected_value_percentiles[number] = 1 - percentile

            number_array = final_sorted_scores['open_rarity_score']
            for number in number_array:
                percentile = number_array.index(number) / len(number_array)
                open_rarity_percentiles[number] = 1 - percentile

        db['all_rarity_scores']['information'] = {}
        db['all_rarity_scores']['probability'] = {}
        db['all_rarity_scores']['expected_value'] = {}
        db['all_rarity_scores']['open_rarity'] = {}

        for single_nft in db['nfts'].values():
            rarity_scores = db['nfts'][single_nft['nft_index']]['metadata']['rarity_scores']
            if rarity_scores:
                score = [x[1] for x in rarity_scores if x[0] == 'information_score'][0]
                rarity_scores.append(('information_percentile', information_percentiles[score]))
                db['all_rarity_scores']['information'][single_nft['nft_index']] = information_percentiles[score]

                score = [x[1] for x in rarity_scores if x[0] == 'probability_score'][0]
                rarity_scores.append(('probability_percentile', probability_percentiles[score]))
                db['all_rarity_scores']['probability'][single_nft['nft_index']] = probability_percentiles[score]

                score = [x[1] for x in rarity_scores if x[0] == 'expected_value'][0]
                rarity_scores.append(('expected_value_percentile', expected_value_percentiles[score]))
                db['all_rarity_scores']['expected_value'][single_nft['nft_index']] = expected_value_percentiles[score]

                score = [x[1] for x in rarity_scores if x[0] == 'open_rarity_score'][0]
                rarity_scores.append(('open_rarity_percentile', open_rarity_percentiles[score]))
                db['all_rarity_scores']['open_rarity'][single_nft['nft_index']] = open_rarity_percentiles[score]
            
        return {'ok':'Open rarity, information, probability, and expected value scores and percentiles have been successfully computed for your NFTs.'}
    else:
        return {'err':'Sorry, you have to be admin to run compute rarity.'}

@query
def get_rarity_data(rarity_category: str) -> list[tuple[nat, float64]]:
    '''
    Get all rarity data across all NFTs for a particular rarity score category.
    '''
    if rarity_category in db['all_rarity_scores']:
        return list(db['all_rarity_scores'][rarity_category].items())
    else:
        return list()

@query
def get_canister_metadata() -> CanisterMeta:
    return db['canister_metadata']

@update
def set_canister_metadata(canister_data: SetCanister) -> FunctionCallResult:
    for key in canister_data.keys():
        if canister_data[key] is not None:
            db['canister_metadata'][key] = canister_data[key]
    return {'ok':'Successfully set canister metadata.'}

@update
def set_max_number_of_nfts_to_mint(new_max_number_of_nfts_to_mint: nat) -> FunctionCallResult:
    '''
    Set a new maximum number of NFTs to mint.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['max_number_of_nfts_to_mint'] = int(new_max_number_of_nfts_to_mint)
        new_event('Change Number of NFTs to Mint',f"Number of NFTs to mint changed from {db['canister_metadata']['max_number_of_nfts_to_mint']} to {new_max_number_of_nfts_to_mint}")
        return {'ok':'New max number of NFTs set successfully.'}
    else:
        return {'err':'Only admin can call set max number of NFTs.'}

@update
def set_collection_name(new_collection_name: str) -> FunctionCallResult:
    '''
    Set a new name for the NFT collection.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['collection_name'] = str(new_collection_name)
        new_event('Edit Collection Metadata',f"Collection name changed from {db['canister_metadata']['collection_name']} to {new_collection_name}")
        return {'ok':'Collection name set successfully.'}
    else:
        return {'err':'Only admin can call set collection name.'}
    
@update
def set_burn_address(burn_address: str) -> FunctionCallResult:
    '''
    Set a new burn address.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['collection_name'] = str(burn_address)
        new_event('Edit Collection Metadata',f"Burn address changed from {db['canister_metadata']['burn_address']} to {burn_address}")
        return {'ok':'Collection burn address set successfully.'}
    else:
        return {'err':'Only admin can call set burn address.'}

@update
def set_creator_royalty(creator_royalty: nat) -> FunctionCallResult:
    '''
    Set a new royalty amount (1_000 = 1%) to be paid to the creator royalty address.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['creator_royalty'] = nat(creator_royalty)
        new_event('Edit Collection Metadata',f"Creator royalty changed from {db['canister_metadata']['creator_royalty']} to {creator_royalty}")
        return {'ok':'Creator royalty set successfully.'}
    else:
        return {'err':'Only admin can call set creator royalty.'}

@update
def set_collection_owner(collection_owner: str) -> FunctionCallResult:
    '''
    Set a new collection owner. Not used anywhere except should be used as the creator royalty address.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['owner'] = str(collection_owner)
        new_event('Edit Collection Metadata',f"Collection name changed from {db['canister_metadata']['owner']} to {collection_owner}")
        return {'ok':'Collection owner set successfully.'}
    else:
        return {'err':'Only admin can call set collection owner.'}

@update
def set_license(license: str) -> FunctionCallResult:
    '''
    Set a generic license for NFT owners of this collection.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['license'] = str(license)
        new_event('Edit Collection Metadata',f"Collection generic license was changed from {db['canister_metadata']['license']} to {license}.")
        return {'ok':'Collection default license set successfully.'}
    else:
        return {'err':'Only admin can call set license.'}

@update
def admin_add(admin_principal: str) -> FunctionCallResult:
    '''
    Adds a new admin to the admin principal array. Grants access to all admin gated functions.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if (len(admin_principal) == 63 or len(admin_principal) == 27) & ('-' in admin_principal):
            db['canister_metadata']['admin_principals'].append(admin_principal)
            new_event('Add Admin',f'New principal {admin_principal} added as admin')
            return {'ok':'New admin added successfully.'}
        else:
            return {'err':'Sorry, your principal is not the correct length for a user principal or canister principal.'}
    else:
        return {'err':'Only admin can call add admin.'}

@update
def admin_remove(admin_principal: str) -> FunctionCallResult:
    '''
    Removes an admin from the admin principal array.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        db['canister_metadata']['admin_principals'].remove(admin_principal)
        new_event('Remove Admin',f'Admin principal {admin_principal} has been removed as admin')
        return {'ok':"Removing admin was successful."}
    else:
        return {'err':'Only admin can call remove admin'}

@update
def upload_asset(asset: AssetForUpload, chunk: opt[nat], asset_index: opt[nat], asset_category: opt[str]) -> FunctionCallResultNat:
    '''
    Uploads a base64 string raw asset to the assets table.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if asset_category is None:
            asset_category = 'start'
        if chunk == 0 or chunk is None:
            if asset_index is None:
                asset_index = len(db['assets'])
            db['assets'][asset_index][asset_category] = {
                'file_name':asset['file_name'],
                'asset_bytes':[asset['asset_bytes']],
                'thumbnail_bytes':asset['thumbnail_bytes'],
                'file_type':asset['file_type']
            }
            new_event('Raw asset was uploaded',f"Raw asset {asset_index} was uploaded.")
            return {'ok':asset_index}
        else:
            if asset_index is not None:
                db['assets'][asset_index][asset_category]['asset_bytes'].append(asset['asset_bytes'])
                return {'ok':chunk}
            else:
                return {'err':'When passing a chunk greater than 0 you must pass in an asset index'}
    else:
        return {'err':'Only admin can call upload raw asset.'}

@update
def edit_asset(asset: EditAsset, chunk: opt[nat], asset_index: nat, asset_category: opt[str]) -> FunctionCallResult:
    '''
    Edits an existing raw asset in the raw assets table.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if asset_category is None:
            asset_category = 'start'
        if chunk == 0 or chunk is None:
            existing_asset = db['assets'][asset_index][asset_category]

            if asset['asset_bytes']:
                existing_asset['asset_bytes'] = [asset['asset_bytes']]
                new_event('Edit Raw Asset',f"Raw asset {asset_index} was changed.")

            if asset['thumbnail_bytes']:
                existing_asset['thumbnail_bytes'] = asset['thumbnail_bytes']
                new_event('Edit Raw Thumbnail',f"Raw asset thumbnail {asset_index} was changed.")
                    
            if asset['file_name']:
                existing_asset['file_name'] = asset['file_name']
                new_event('Edit Raw Asset Filename',f"Raw asset {asset_index} filename was changed from '{db['assets'][asset_index]['file_name']}' to '{asset['file_name']}'.")

            if asset['file_type']:
                existing_asset['file_type'] = asset['file_type']
                new_event('Edit Raw Asset File Type',f"Raw asset {asset_index} file_type was changed from '{db['assets'][asset_index]['file_type']}' to '{asset['file_type']}'.")
        
            db['assets'][asset_index][asset_category] = existing_asset
            return {'ok':'Asset successfully updated'}
        else:
            if asset['asset_bytes']:
                db['assets'][asset_index][asset_category]['asset_bytes'].append(asset['asset_bytes'])
                return {'ok':'You successfully added an asset chunk to your existing asset.'}
            else:
                return {'err':'If you supply a chunk you must also supply an asset_base64_str chunk.'}
    else:
        return {'err':'Only admin can call edit raw asset.'}

@update
def remove_asset(asset_index: nat, asset_category: opt[str]) -> FunctionCallResult:
    '''
    Removes a raw asset from the raw_assets table. This removes the index from the raw assets array which cannot be replaced.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if asset_index in db['assets']:
            if asset_category is None:
                asset_category = 'start'
            del db['assets'][asset_index][asset_category]
            new_event('Remove Asset',f"Asset {asset_index} from {asset_category} was removed.")
            
            return {'ok':'Raw asset successfully deleted.'}
        else:
            return {'err':'Sorry that asset index does not exist.'}
    else:
        return {'err':'You must be an admin to call remove raw asset.'}

@update
def mint_many_NFTs(nft_objects: list[NftForMinting]) -> ManyMintResult:
    '''
    Mints many NFTs in a single update call for more efficient minting. Can likely handle up to 1000 mints at a time.
    '''
    error_messages: list[str] = []
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if len(db['registry']) + len(nft_objects) < db['canister_metadata']['max_number_of_nfts_to_mint']:
            for nft_object in nft_objects:
                nft_index = nft_object['nft_index']
                asset_url = nft_object['asset_url']
                thumbnail_url = nft_object['thumbnail_url']
                asset_index = nft_object['asset_index']
                asset_type = nft_object['asset_type']
                metadata = nft_object['metadata']
                to_address = sanitize_address(nft_object['to_address'])
                
                if not nft_index:
                    nft_index = len(db['registry'])
                
                if nft_index not in db['registry']:
                    if len(db['registry']) < db['canister_metadata']['max_number_of_nfts_to_mint']:
                        if len(to_address) == 64:
                            db['registry'][nft_index] = to_address

                            if to_address not in db['address_registry']:
                                db['address_registry'][to_address] = []
                            db['address_registry'][to_address].append(nft_index)

                            db['nfts'][nft_index] = {
                                'nft_index': nft_index,
                                'asset_url': asset_url,
                                'thumbnail_url': thumbnail_url,
                                'asset_index': asset_index,
                                'asset_type': asset_type,
                                'metadata': metadata,
                            }
                            new_transfer_event('',to_address,nft_index,'Minted')
                        else:
                            error_messages.append(f"NFT index {nft_index} failed, address wrong length")
                    else:
                        error_messages.append(f"NFT index {nft_index} would put the canister above the max mint limit.")
                else:
                    error_messages.append(f'NFT index {nft_index} already exists.')
            new_event('Mint New NFT',f"{len(nft_objects)} NFTs were just minted.")

            return {'ok':error_messages}
        else:
            return {'err':'Minting this many NFTs would put the canister above the max mint limit.'}
    else:
        return {'err':'Sorry you must be admin to call mint many NFTs.'}

@update
def mint_nft(nft_object: NftForMinting) -> FunctionCallResult:
    '''
    Mints a single NFT.
    Requires uploading an asset using upload_raw_asset to get an asset_index if using that parameter.
    Otherwise, can use asset and thumbnail URLs directly.
    '''
    nft_index = nft_object['nft_index']
    asset_url = nft_object['asset_url']
    thumbnail_url = nft_object['thumbnail_url']
    asset_index = nft_object['asset_index']
    asset_type = nft_object['asset_type']
    metadata = nft_object['metadata']
    to_address = sanitize_address(nft_object['to_address'])
    
    if not nft_index:
        nft_index = len(db['registry'])
    
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if nft_index not in db['registry']:
            if len(db['registry']) < db['canister_metadata']['max_number_of_nfts_to_mint']:
                if len(to_address) == 64:
                    db['registry'][nft_index] = to_address

                    if to_address not in db['address_registry']:
                        db['address_registry'][to_address] = []
                    db['address_registry'][to_address].append(nft_index)

                    db['nfts'][nft_index] = {
                        'nft_index': nft_index,
                        'asset_url': asset_url,
                        'thumbnail_url': thumbnail_url,
                        'asset_index': asset_index,
                        'asset_type': asset_type,
                        'metadata': metadata,
                    }

                    new_event('Mint New NFT',f"NFT {nft_index} was minted with asset_url {asset_url} thumbnail_url {thumbnail_url} asset_type {asset_type} metadata {metadata}")
                    new_transfer_event('',to_address,nft_index,'Minted')

                    return {'ok':'Mint successful.'}
                else:
                    return {'err':f'Length of to address is {len(to_address)} when it should be 64'}
            else:
                return {'err':'Sorry, you cannot mint more NFTs than the originally listed maximum'}
        else:
            return {'err':'This index has already been minted.'}
    else:
        return {'err':'Sorry, only admin can call mint NFT.'}

@update
def edit_nft(nft_object: Nft) -> FunctionCallResult:
    '''
    Allows editing any portion of an existing NFT except for the NFT index.
    '''
    nft_index = nft_object['nft_index']
    asset_url = nft_object['asset_url']
    thumbnail_url = nft_object['thumbnail_url']
    asset_type = nft_object['asset_type']
    asset_index = nft_object['asset_index']
    metadata = nft_object['metadata']

    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if nft_index in db['registry']:
            current_nft = db['nfts'][nft_index]
            if asset_url:
                current_nft['asset_url'] = asset_url
                new_event('Edit NFT Asset URL',f"NFT {nft_index} asset_url was changed from '{db['nfts'][nft_index]['asset_url']}' to '{asset_url}'.")
                    
            if thumbnail_url:
                current_nft['thumbnail_url'] = thumbnail_url
                new_event('Edit NFT Thumbnail URL',f"NFT {nft_index} thumbnail_url was changed from '{db['nfts'][nft_index]['thumbnail_url']}' to '{thumbnail_url}'.")

            if asset_index is not None:
                current_nft['asset_index'] = asset_index
                new_event('Edit Asset Index',f"Asset {asset_index} was changed from '{db['nfts'][nft_index]['asset_index']}' to '{asset_index}'.")
            
            if asset_type:
                current_nft['asset_type'] = asset_type
                new_event('Edit NFT Asset Type',f"NFT {nft_index} asset_type was changed from '{db['nfts'][nft_index]['asset_type']}' to '{asset_type}'.")

            if metadata:
                current_nft['metadata'] = metadata
                new_event('Edit NFT Metadata',f"NFT {nft_index} metadata was changed from '{db['nfts'][nft_index]['metadata']}' to '{metadata}'.")

            db['nfts'][nft_index] = current_nft
            
            return {'ok':'NFT edited successfully.'}
        else:
            return {'err':'This NFT does not exist'}
    else:
        return {'err':'Sorry, only admin can call edit asset'}

@update
def unmint_nft(nft_index: nat) -> FunctionCallResult:
    '''
    Completely removes an NFT from existence. Deletes from registry, address_registry, and nfts tables.
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        if nft_index in db['registry']:
            current_owner = db['registry'][nft_index]
            
            del db['registry'][nft_index]
            db['address_registry'][current_owner].remove(nft_index)
            del db['nfts'][nft_index]

            new_event('Unmint NFT',f"NFT {nft_index} has been unminted and completely removed from the canister")
            new_transfer_event(current_owner,'',nft_index,'Unminted')
            return {'ok':'NFT successfully unminted.'}
        else:
            return {'err':'NFT does not exist yet.'}
    else:
        return {'err':'Only admin can call unmint NFT'}

@update
def burn_nft(nft_index: nat) -> FunctionCallResult:
    '''
    Burns an NFT, which means send it to an address that noone has control over.
    Note that until you blackhole this canister and remove all admins, burned NFTs can always be recovered.
    '''
    burn_address = sanitize_address(db['canister_metadata']['burn_address'])
    if nft_index in db['registry']:
        owner_address = db['registry'][nft_index]
        caller_address = str(ic.caller().to_account_id())[2:]
        if caller_address == owner_address:
            db['registry'][nft_index] = burn_address
            
            db['address_registry'][owner_address].remove(nft_index)
            db['address_registry'][burn_address].append(nft_index)
            new_transfer_event(caller_address,burn_address,nft_index,'Burned')
            return {'ok':'NFT burned successfully.'}
        else:
            return {'err':'Sorry, you do not own this NFT.'}
    else:
        return {'err':'Sorry, this NFT does not exist.'}

def _transfer(nft_index: nat, from_address: str, to_address: str) -> FunctionCallResult:
    '''
    An internal transfer function that handles everything to do with a transfer. 
    EXT transfer (and any other implemented) is a wrapper around this transfer.
    '''
    if nft_index in db['registry']:
        owner_address = db['registry'][nft_index]
        if from_address == owner_address:
            if len(to_address) == 64:
                
                db['registry'][nft_index] = to_address
                db['address_registry'][owner_address].remove(nft_index)

                if to_address not in db['address_registry']:
                    db['address_registry'][to_address] = []
                db['address_registry'][to_address].append(nft_index)
                new_transfer_event(from_address,to_address,nft_index,'Transfer')

                return {'ok':'Transfer successful.'}
            else:
                return {'err':'Incorrect length for to address.'}
        else:
            return {'err':"Sorry, you do not own this NFT."}
    else:
        return {'err':"Sorry, that NFT does not exist."}

class ManagementCanister(Canister):
    @method
    def raw_rand(self) -> blob: ...

def get_randomness_directly() -> Async[blob]:
    management_canister = ManagementCanister(Principal.from_str('aaaaa-aa'))
    randomness_result: CanisterResult[blob] = yield management_canister.raw_rand()
    if randomness_result.err is not None:
        return bytes()
    return randomness_result.ok

@update
def airdrop(to_addresses: list[str], nft_indexes: opt[list[nat]]) -> Async[FunctionCallResult]:
    '''
    Allows an admin to airdrop NFTs in the "0000" address to a list of addresses. 
    '''
    if str(ic.caller()) in db['canister_metadata']['admin_principals']:
        available_tokens = db['address_registry']['0000']
        if nft_indexes is not None:
            if len(to_addresses) == len(nft_indexes):
                if set(nft_indexes).issubset(set(available_tokens)):
                    for to_address,nft_index in zip(to_addresses,nft_indexes):
                        to_address = sanitize_address(to_address)
                        
                        db['registry'][nft_index] = to_address
                        db['address_registry']['0000'].remove(nft_index)

                        if to_address not in db['address_registry']:
                            db['address_registry'][to_address] = []
                        db['address_registry'][to_address].append(nft_index)

                        new_transfer_event("0000",to_address,nft_index,'Admin Airdrop')
                    return {'ok':'Admin airdrop successful.'}
                else:
                    return {'err':'Sorry, you have selected an NFT index that is not available in the "0000" address.'}
            else:
                return {'err':'If you supply NFT indexes you must supply an NFT index for every to address.'}
        else:
            randomness: blob = yield get_randomness_directly()
            if len(randomness) == 0:
                return {'err':'Randomness call failed, please wait until we can get randomness to do a fair airdrop.'}
            
            list_a: list[str] = []
            list_b: list[str] = []
            for count,to_address in enumerate(sorted(to_addresses)):
                random_byte = randomness[count % 32]
                if random_byte > 128:
                    list_a.append(to_address)
                else:
                    list_b.append(to_address)
            final_to_addresses = list_b + list_a

            if len(to_addresses) <= len(available_tokens):
                for to_address in final_to_addresses:
                    to_address = sanitize_address(to_address)
                    nft_index = available_tokens.pop(0)
                    db['registry'][nft_index] = to_address

                    db['address_registry']['0000'].remove(nft_index)

                    if to_address not in db['address_registry']:
                        db['address_registry'][to_address] = []
                    db['address_registry'][to_address].append(nft_index)

                    new_transfer_event("0000",to_address,nft_index,'Admin Airdrop')

                new_event('NFT airdropped',f"Admin airdropped {len(to_addresses)} NFTs from '0000'")
                return {'ok':'Admin airdrop successful.'}
            else:
                return {'err':f'Sorry, you only have {len(available_tokens)} NFTs available in "0000" but you uploaded {len(to_addresses)} addresses.'}
    else:
        return {'err':"Sorry, only admin can call admin transfer."}

@update
def admin_transfer(nft_index: nat, to_address: str) -> FunctionCallResult:
    '''
    Allows an admin to forcibly remove any NFT from anyone and reassign it to anyone else. 
    Helpful for rescuing lost NFTs, but dangerous as you must trust admin.
    '''
    to_address = sanitize_address(to_address)
    if nft_index in db['registry']:
        if str(ic.caller()) in db['canister_metadata']['admin_principals']:
            if len(to_address) == 64:
                current_owner = db['registry'][nft_index]
                
                db['registry'][nft_index] = to_address
                
                db['address_registry'][current_owner].remove(nft_index)

                if to_address not in db['address_registry']:
                    db['address_registry'][to_address] = []
                db['address_registry'][to_address].append(nft_index)

                new_event('Admin transfer',f"Admin transferred {nft_index} from {current_owner} to {to_address}")
                new_transfer_event(current_owner,to_address,nft_index,'Admin Transfer')
                
                return {'ok':'Admin transfer successful.'}
            else:
                return {'err':'Incorrect length for to address.'}
        else:
            return {'err':"Sorry, only admin can call admin transfer."}
    else:
        return {'err':"Sorry, that NFT does not exist."}

def get_unique_holders() -> nat:
    '''
    An internal function that eturns the number of unique NFT holders.
    '''
    unique_holders = len(db['address_registry'])
    return unique_holders

def get_index_from_token_id(tokenid: str) -> nat:
    '''
    An internal function that converts an EXT token identifier to an NFT index.
    '''
    return int.from_bytes(Principal.from_str(tokenid).bytes[-4:],'big')

@query
def get_token_id(nft_index: nat) -> FunctionCallResult:
    '''
    Converts an NFT index and the current canister to return a globally unique EXT token identifier.
    '''
    token_id = Principal(bytes('\x0Atid','utf-8') + ic.id().bytes + int(nft_index).to_bytes(4,'big')).to_str()
    return {'ok':token_id}

def get_request_params(request_url: str) -> dict[str,str]:
    '''
    An internal function used to get request params from an http request to the NFT canister.
    '''
    query_string = request_url.split('?')[-1]
    params  = dict(param.split('=') for param in query_string.split('&'))
    return params

@query
def http_request_streaming_callback(token: Token) -> StreamingCallbackHttpResponse:
    """
    To return assets bigger than the 2MB message limit, you have to chunk assets and iteratively return them.
    """
    asset_category = str(token['arbitrary_data'].split(':')[0])
    asset_index = int(token['arbitrary_data'].split(':')[1])
    chunk_num = int(token['arbitrary_data'].split(':')[2])
    if len(db['assets'][asset_index]['asset_bytes']) - 1 > chunk_num:
        return {
            'body':db['assets'][asset_index][asset_category]['asset_bytes'][chunk_num],
            'token':{'arbitrary_data':f'{asset_index}:{chunk_num + 1}'}
        }
    # this is the final condition, token = None means we don't have any more chunks
    else:
        return {
            'body':db['assets'][asset_index][asset_category]['asset_bytes'][chunk_num],
            'token':None
        }

def return_thumbnail_bytes(thumbnail_bytes: blob) -> HttpResponse:
    '''
    An internal function that returns an SVG wrapper for base64 images.
    '''
    return {
        'status_code':200,
        'headers':[
            ('Content-Type','image/png')
        ],
        'body':thumbnail_bytes,
        'streaming_strategy': None,
        'upgrade': False
    }

def return_image_html(img_url: opt[str]) -> HttpResponse:
    '''
    An internal function that returns an SVG wrapper for base64 images.
    '''
    if img_url:
        width = 800
        height = 800
        
        img_url = img_url.replace('&', '&amp;')
        http_response_body = bytes(f'''
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="width: {width}px;height: {height}px;" version="1.1" id="generated" x="0px" y="0px" viewBox="0 0 {width} {height}" xml:space="preserve">
                <g>
                    <image href="{img_url}"/>
                </g>
            </svg>
        ''',encoding='utf-8')
        return {
            'status_code':200,
            'headers':[
                ('Content-Type','image/svg+xml'),
                ('Content-Length',str(len(http_response_body)))
            ],
            'body':http_response_body,
            'streaming_strategy': None,
            'upgrade': False
        }
    else:
        return {
            'status_code':400,
            'headers':[('Content-Type','text/html')],
            'body':bytes('NFT image not found','utf-8'),
            'streaming_strategy': None,
            'upgrade': False
        }

def return_multipart_image_html(asset_index: opt[nat], image_bytes: opt[blob], asset_category: str) -> HttpResponse:
    '''
    An internal function that returns an SVG wrapper for base64 images.
    '''
    if image_bytes:
        if asset_index is not None:
            if len(db['assets'][asset_index][asset_category]['asset_bytes']) > 1:
                # we have more than one chunk, so use http_request_streaming_callback
                return {
                    'status_code':200,
                    'headers':[
                        ('Content-Type','image/png'),
                        ('Transfer-Encoding', 'chunked')
                    ],
                    'body':image_bytes,
                    'streaming_strategy': {
                        'Callback':{
                            'token':{'arbitrary_data':f'{asset_category}:{asset_index}:1'}, #chunk num is 1 for the 2nd param
                            'callback':(ic.id(), 'http_request_streaming_callback')
                        }
                    },
                    'upgrade': False
                }
            else:
                # we only have a single chunk, so no streaming callback needed
                return {
                    'status_code':200,
                    'headers':[
                        ('Content-Type','image/png'),
                    ],
                    'body':image_bytes,
                    'streaming_strategy': None,
                    'upgrade': False
                }
        else:
            return {
            'status_code':400,
            'headers':[('Content-Type','text/html')],
            'body':bytes('NFT image not found','utf-8'),
            'streaming_strategy': None,
            'upgrade': False
        } 
    else:
        return {
            'status_code':400,
            'headers':[('Content-Type','text/html')],
            'body':bytes('NFT image not found','utf-8'),
            'streaming_strategy': None,
            'upgrade': False
        } 

@query
def http_request(request: HttpRequest) -> HttpResponse:
    '''
    The standard http_request method following the standard specified in the IC spec.
    Handles all branching logic needed to handle NFT indexes, EXT token identifiers, thumbnails, and raw assets.
    '''
    request_url = request['url']
    asset_category = determine_asset_category()

    if 'index' in request_url and 'thumbnail' not in request_url:
        params = get_request_params(request_url)
        nft_index = int(params['index'])
        asset_url = db["nfts"][nft_index]["asset_url"]
        if asset_url:
            return return_image_html(asset_url)
        else:
            return return_image_html(None)
    
    elif 'index' in request_url and 'thumbnail' in request_url:
        params = get_request_params(request_url)
        nft_index = int(params['index'])
        asset_index = db['nfts'][nft_index]['asset_index']    
        if asset_index is not None:
            thumbnail_bytes = db['assets'][asset_index][asset_category]['thumbnail_bytes']
            return return_thumbnail_bytes(thumbnail_bytes)
        else:
            return return_image_html(None)

    elif 'tokenid' in request_url and 'thumbnail' not in request_url:
        params = get_request_params(request_url)
        tokenid = str(params['tokenid'])
        nft_index = get_index_from_token_id(tokenid)
        asset_url = db["nfts"][nft_index]["asset_url"]
        if asset_url:
            return return_image_html(asset_url)
        else:
            return return_image_html(None)
    
    elif 'tokenid' in request_url and 'thumbnail' in request_url:
        params = get_request_params(request_url)
        tokenid = str(params['tokenid'])
        nft_index = get_index_from_token_id(tokenid)
        asset_index = db['nfts'][nft_index]['asset_index']
        if asset_index is not None:
            thumbnail_bytes = db['assets'][asset_index][asset_category]['thumbnail_bytes']
            return return_thumbnail_bytes(thumbnail_bytes)
        else:
            return return_image_html(None)
    
    elif 'asset' in request_url and 'thumbnail' not in request_url:
        params = get_request_params(request_url)
        asset_index = int(params['asset'])
        image_bytes = db['assets'][asset_index][asset_category]['asset_bytes'][0]
        return return_multipart_image_html(asset_index, image_bytes, asset_category)
    
    elif 'asset' in request_url and 'thumbnail' in request_url:
        params = get_request_params(request_url)
        asset_index = int(params['asset'])
        thumbnail_bytes = db['assets'][asset_index][asset_category]['thumbnail_bytes']
        return return_thumbnail_bytes(thumbnail_bytes)
    
    else:
        burn_address = db['canister_metadata']['burn_address']
        minted_nfts_count = len(db["registry"])
        if burn_address in db['address_registry']:
            burned_nfts_count = len(db['address_registry'][burn_address])
        else:
            burned_nfts_count = 0
        current_supply = minted_nfts_count - burned_nfts_count
        unique_holders = get_unique_holders()
        admin = ','.join(db['canister_metadata']['admin_principals'])
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
                                <td style="padding: 12px 15px;">Collection Name</td>
                                <td style="padding: 12px 15px;">{db['canister_metadata']['collection_name']}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #dddddd">
                                <td style="padding: 12px 15px;">List of Admins</td>
                                <td style="padding: 12px 15px;">{admin}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #dddddd">
                                <td style="padding: 12px 15px;">Burn Address</td>
                                <td style="padding: 12px 15px;">{burn_address}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #dddddd">
                                <td style="padding: 12px 15px;"># of Minted NFTs</td>
                                <td style="padding: 12px 15px;">{minted_nfts_count}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #dddddd">
                                <td style="padding: 12px 15px;"># of Burned NFTs</td>
                                <td style="padding: 12px 15px;">{burned_nfts_count}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #dddddd">
                                <td style="padding: 12px 15px;">Current Supply</td>
                                <td style="padding: 12px 15px;">{current_supply}</td>
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
            'body':http_response_body,
            'streaming_strategy': None,
            'upgrade': False
        }

###
# SUPPORTING EXT
# Allows adding to Stoic
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
    '''
    The EXT transfer method. Handles principal, sub-accounts, and addresses. Calls the internal transfer method.
    '''

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
    
    from_address_from_caller = str(ic.caller().to_account_id(sub_account_num))[2:]
    if from_address == from_address_from_caller:

        if 'address' in transfer_request['to']:
            to_address = transfer_request['to']['address']
        elif 'principal' in transfer_request['to']:
            to_address = str(transfer_request['to']['principal'].to_account_id())[2:]
        else:
            return {'err':{'Other':'Invalid from parameter, should be address or principal.'}}
        
        nft_index = get_index_from_token_id(transfer_request['token'])
        result = _transfer(nft_index,from_address,to_address)
        if 'ok' in result:
            return {'ok':1}
        elif 'err' in result:
            return {'err':{'Other':result['err']}}
        else:
            return {'err':{'Other':'Unknown result, please contact token owners.'}}
    else:
        return {'err':{'Other':'Sorry, the from address and caller address do not match.'}}

# ext_metadata
class MetadataRecord(Record):
    name: str
    symbol: str
    decimals: nat8
    metadata: opt[list[nat8]]
    ownerAccount: str

# ext_metadata
class MetadataNonfungible(Record):
    metadata: opt[str]

# ext_metadata
class Metadata(Variant, total=False):
    fungible: MetadataRecord
    nonfungible: MetadataNonfungible

# ext_metadata
class CommonError(Variant, total=False):
   InsufficientBalance: str
   InvalidToken: str
   Other: str
   Unauthorized: str

# ext_metadata
class MetadataResponse(Variant, total=False):
    ok: Metadata
    err: CommonError

# ext_metadata
@query
def metadata(token_identifier: str) -> MetadataResponse:
    '''
    The EXT metadata method, and returns NFT metadata for a specific NFT index.
    '''
    nft_index = get_index_from_token_id(token_identifier)
    return {
        'ok':{
            'nonfungible':{
                'metadata':str(db['nfts'][nft_index]['metadata']),
            }
        }
    }

# ext_tokens_ext
class Listing(Record):
    locked: opt[int]
    price: nat64
    seller: Principal
    
# ext_tokens_ext
class TokensExtResult(Variant, total=False):
    ok: list[tuple[nat32, opt[Listing], opt[blob]]]
    err: CommonError

# ext_tokens_ext
@query
def tokens_ext(address: str) -> TokensExtResult:
    '''
    The EXT method to know which tokens are owned by a specific address. Used by Stoic to determine NFT ownership.
    '''
    address = sanitize_address(address)
    if address in db['address_registry']:
        return {'ok':[(x,None,None) for x in db['address_registry'][address]]}
    else:
        return {'err':{'Other':'Sorry, address not found'}}

# ext_getTokens
@query
def getTokens() -> list[tuple[nat32,Metadata]]:
    '''
    Returns an array of NFT indexes owned by the address.
    '''
    return [(x['nft_index'],{'nonfungible':{'metadata':None}}) for x in db['nfts'].values()]

# ext_listings (required for now to show up in Entrepot)
@query
def listings() -> list[str]:
    return []