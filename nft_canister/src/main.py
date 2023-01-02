from kybra import StableBTreeMap,Canister,CanisterResult,ic,nat,nat8,nat16,nat32,nat64,blob,opt,float64,Principal,Variant,Record,Async,pre_upgrade,post_upgrade,init,query,update,method
from twister_random import MersenneTwister #type: ignore
import rarity_computation
from main_types import Asset,NftMetadata,DisplayToRawAsset,RevealCondition,DisplayToRevealCategories,tupleType,CanisterImage,Token,StreamingCallbackHttpResponse,Nft,TransferEvent,Event,AssetView,RevealCategory,CanisterMeta,FunctionCallResult,FunctionCallResultNat,UpdateMetadataNumber,UpdateMetadataText,SetCanister,RawAssetForUpload,AssetDisplayForUpload,EditRawAsset,NftForMinting,ManyMintResult,HttpRequest,FunctionCallResultFloat64,HttpResponse
from nft_home_page_html import get_home_page_html

# SIZING GUIDE
# Nat64: 7 + 8 bytes, max value is 1.84E19
# Nat32: 7 + 4 bytes, max value is 4294967295
# Nat16: 7 + 2 bytes, max value is 65535
# Nat8: 7 + 1 byte, max value is 256
# str: 8 + 1 byte per character
# list of Nats: 10 bytes + (actual_nat)*n
# record: 9 + 6*num_keys + actual_values
# variant: 10 + 6*num_keys (include all keys) + actual_value selected
# list in record: 3 + (actual_nat)*n
# string in record: 1 + 1 byte per character
# opt adds 3 bytes
# tuple adds 6 bytes + values within
# bool is 1 byte solo, don't know by itself yet

registry = StableBTreeMap[nat16, str](memory_id=0, max_key_size=9, max_value_size=72) # nft_index, wallet_address
address_registry = StableBTreeMap[str, list[nat16]](memory_id=1, max_key_size=72, max_value_size=20010) # wallet_address, list[nft_index] - will handle 10k NFTs
raw_assets = StableBTreeMap[nat16, Asset](memory_id=2, max_key_size=15, max_value_size=3_985_305) # raw_asset_index, actual_asset - will handle 2MB thumbs and 2 MB assets
nfts = StableBTreeMap[nat16, Nft](memory_id=3, max_key_size=9, max_value_size=573) # nft_index, nft_object - will handle 10k NFTs
nft_metadata = StableBTreeMap[nat16, NftMetadata](memory_id=4, max_key_size=9, max_value_size=573) # will handle 10k NFTs
transactions = StableBTreeMap[nat64, TransferEvent](memory_id=5, max_key_size=15, max_value_size=255) # transaction_id, actual_transaction - will handle 10k NFTs                    
events = StableBTreeMap[nat64, Event](memory_id=6, max_key_size=15, max_value_size=452) # event_id, actual_event - will handle 10k NFTs
display_to_raw_asset = StableBTreeMap[DisplayToRawAsset, nat16](memory_id=7, max_key_size=173, max_value_size=9) # a 3-primary-key composite index, raw_asset_index
asset_views = StableBTreeMap[str, AssetView](memory_id=8, max_key_size=72, max_value_size=175)
reveal_categories = StableBTreeMap[str, RevealCategory](memory_id=9, max_key_size=72, max_value_size=175) # reveal_category_name, actual_reveal_category_object
reveal_conditions = StableBTreeMap[nat16, RevealCondition](memory_id=10, max_key_size=9, max_value_size=24) # reveal_condition_index, actual_reveal_condition_object
display_to_reveal_categories = StableBTreeMap[DisplayToRevealCategories, list[str]](memory_id=11, max_key_size=102, max_value_size=3210) # reveal_category_name, actual_reveal_category_object
nft_rarity_scores = StableBTreeMap[str, list[tupleType]](memory_id=12, max_key_size=72, max_value_size=80024) # nft_index, rarity_score_object
canister_metadata = StableBTreeMap[nat8, CanisterMeta](memory_id=13, max_key_size=15, max_value_size=4416) # will_always_be_0, canister_meta_object
canister_images = StableBTreeMap[nat8, CanisterImage](memory_id=14, max_key_size=15, max_value_size=5_976_909) # will_always_be_0, canister_image_meta_object
max_of_arrays = StableBTreeMap[str, nat16](memory_id=15, max_key_size=72, max_value_size=9)
categories = StableBTreeMap[str,list[str]](memory_id=16, max_key_size=72, max_value_size=3610)


# DISPLAY INDEX, ASSET VIEWS, REVEAL CATEGORIES, RAW ASSET INDEX
# categories: use key and then append to array to keep track of all keys since no keys() in stable structures yet
# max_of_arrays: use to keep track of maxes for creation purposes
# display_to_reveal_category_details: use to keep track of reveal category information
# display_to_view_details: use to keep track of asset view information, priority, status, etc.
# display_to_raw_asset: use display index, asset view, and reveal category to get asset index

# MINTING NFTs
# 1. Create an asset view -> 'image' or 'video' or 'html'
# 2. Create some reveal categories -> 'start' or 'post-launch' or 'dead-version'
# 3. Upload some assets. -> all raw assets, upload them all as a blob
# 4. Associate display index, asset view, and array of reveal categories, i.e. add 'post-launch' to a display index and asset view
# 5. Associate display index, asset view, reveal category, and specific asset index


def new_event(event_type: str, description: str) -> bool:
    '''
    Inserts a new event into the event array.
    '''
    timestamp = ic.time()
    actor_principal = str(ic.caller())
    event_length = events.len()
    events.insert(event_length,{
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
    transaction_length = transactions.len()
    transactions.insert(transaction_length,{
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
    This only runs once the first time you deploy the canister.
    '''
    ic.print('init')
    
    canister_metadata_for_insert: CanisterMeta = {
        'collection_name': 'Initial Collection Name CHANGE ME',
        'royalty': [],
        'super_admin': ['2sr56-kadmk-wfai7-753z7-yo6rd-a4d2f-ghedf-wrkvd-rav3s-2vcfm-wae'],
        'owners': [],
        'collaborators': [],
        'burn_address': '0000000000000000000000000000000000000000000000000000000000000001',
        'max_number_of_nfts_to_mint': 10000,
        'license': '',
        'blurb': None,
        'brief': None,
        'description': None,
        'detailpage': None,
        'keywords': None,
        'twitter': None,
        'discord': None,
        'distrikt': None,
        'dscvr': None,
        'web': None,
    }
    
    canister_metadata.insert(0,canister_metadata_for_insert)
    
    new_event('Canister Created','New canister deployed.')
    new_event('Add Super Admin',f'Initial super admin list set to {canister_metadata_for_insert["super_admin"]}')
    new_event('Add Owners',f'Initial owner list set to {canister_metadata_for_insert["owners"]}')
    new_event('Add Collaborators',f'Initial collaborator list set to {canister_metadata_for_insert["collaborators"]}')
    new_event('Set Burn Address',f'Initial burn address set to {canister_metadata_for_insert["burn_address"]}')

@pre_upgrade
def pre_upgrade_():
    '''
    This runs before every upgrade.
    '''
    ic.print('pre_upgrade')

@post_upgrade
def post_upgrade_():
    '''
    This runs after every upgrade.
    '''
    ic.print('post_upgrade')
    new_event('Upgrade','Canister was upgraded')

@query
def get_reveal_category_names() -> opt[list[str]]:
    '''
    Returns all reveal categories that have been created.
    '''
    return categories.get('reveal_categories')

@query
def get_asset_view_names() -> opt[list[str]]:
    '''
    Returns all asset views that have been created.
    '''
    return categories.get('asset_views')

@update
def create_reveal_category(reveal_category: RevealCategory) -> FunctionCallResult:
    '''
    Creates a reveal category that can then be used to dynamically change your asset.
    '''
    category_name = reveal_category['category_name']
    reveal_categories.insert(category_name,{
        'condition_index': reveal_category['condition_index'],
        'priority': reveal_category['priority'],
        'category_name': category_name,
    })
    category_list_opt = categories.get('reveal_categories')
    if category_list_opt:
        category_list_opt.append(category_name)
        categories.insert('reveal_categories',category_list_opt)
        return {'ok':f'You successfully added the new reveal category "{category_name}".'}
    else:
        return {'err':'Could not find the reveal categories key in the categories table.'}

@update
def trigger_reveal_on(reveal_category_name: str) -> FunctionCallResult:
    '''
    Manually triggers reveal on for a specific reveal category name (the name is the index for reveal categories)
    '''
    reveal_category_opt = reveal_categories.get(reveal_category_name)
    if reveal_category_opt:
        condition_index = reveal_category_opt['condition_index']
        reveal_condition_opt = reveal_conditions.get(condition_index)
        if reveal_condition_opt:
            if 'manual_condition' in reveal_condition_opt:
                reveal_condition_opt['manual_condition'] = True
                return {'ok':f'Display for "{reveal_category_name}" was successfully switched to True.'}
            else:
                return {'err':f'Sorry, "{reveal_category_name}" is not a manually triggered condition and cannot be switched to True.'}
        else:
            return {'err':'The condition index associated with that reveal category does not exist.'}
    else:
        return {'err':'Sorry, that reveal category cannot be found.'}

@update
def trigger_reveal_off(reveal_category_name: str) -> FunctionCallResult:
    '''
    Manually triggers reveal off for a specific reveal category name (the name is the index for reveal categories)
    '''
    reveal_category_opt = reveal_categories.get(reveal_category_name)
    if reveal_category_opt:
        condition_index = reveal_category_opt['condition_index']
        reveal_condition_opt = reveal_conditions.get(condition_index)
        if reveal_condition_opt:
            if 'manual_condition' in reveal_condition_opt:
                reveal_condition_opt['manual_condition'] = False
                return {'ok':f'Display for "{reveal_category_name}" was successfully switched to False.'}
            else:
                return {'err':f'Sorry, "{reveal_category_name}" is not a manually triggered condition and cannot be switched to False.'}
        else:
            return {'err':'The condition index associated with that reveal category does not exist.'}
    else:
        return {'err':'Sorry, that reveal category cannot be found.'}

@update
def create_new_asset_view(asset_view: AssetView) -> FunctionCallResult:
    '''
    Creates a new asset view which allows you to then upload assets to that asset view.
    '''
    view_name = asset_view['view_name']
    asset_views.insert(view_name, asset_view)
    return {'ok':f'Asset view {view_name} successfully created.'}

@update
def remove_asset_view(view_name: str) -> FunctionCallResult:
    '''
    Deletes an asset view from the asset views array.
    '''
    asset_views.remove(view_name)
    return {'ok':f'Asset view {view_name} successfully deleted.'}

def determine_reveal_category(display_index: nat16, asset_view: str) -> str:
    '''
    Loops through all reveal categories for an asset and determines (across manual, single time, etc.) which
    reveal categories apply, and then uses priority to determine which to use.
    '''
    all_matching_conditions: list[tuple[str,nat]] = []
    current_timestamp = ic.time()
    reveal_categories_opt = display_to_reveal_categories.get({'display_index':display_index,'asset_view':asset_view})
    if reveal_categories_opt:
        for reveal_category_name in reveal_categories_opt:
            reveal_category_opt = reveal_categories.get(reveal_category_name)
            if reveal_category_opt:
                condition_index = reveal_category_opt['condition_index']
                reveal_condition_opt = reveal_conditions.get(condition_index)
                if reveal_condition_opt:
                    if 'manual_condition' in reveal_condition_opt:
                        if reveal_condition_opt['manual_condition']:
                            all_matching_conditions.append((reveal_category_name,reveal_category_opt['priority']))
                    if 'single_time_condition' in reveal_condition_opt:
                        if current_timestamp > reveal_condition_opt['single_time_condition']:
                            all_matching_conditions.append((reveal_category_name,reveal_category_opt['priority']))
                if len(all_matching_conditions) > 0:
                    final_condition = max(all_matching_conditions,key=lambda item:item[1])
                    return final_condition[0]
                else:
                    return 'start'
            else:
                return 'start'
        return 'start'
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

class SendCyclesResult(Variant, total=False):
    ok: nat64
    err: str

class InstallationCanister(Canister):
    @method
    def receive_cycles(self) -> nat64: ...

@update
def send_cycles(cycles_to_send: nat64) -> Async[SendCyclesResult]:
    '''
    Send cycles back to the installation canister to reclaim cycles.
    '''
    if str(ic.caller()) in get_permissions('level_1'):
        installation_canister = InstallationCanister(Principal.from_str('5bgk3-4yaaa-aaaam-aayrq-cai'))
        result: CanisterResult[nat64] = yield installation_canister.receive_cycles().with_cycles(cycles_to_send)

        if result.err is not None:
            return {
                'err': result.err
            }

        return {
            'ok': ic.msg_cycles_refunded()
        }
    else:
        return {'err':'Sorry, you must be admin to send cycles back to factory canister.'}

@query
def get_event(event_index: nat64) -> opt[Event]:
    '''
    Returns an individual event based on the event index.
    '''
    event_opt = events.get(event_index)
    return event_opt

@query
def get_raw_asset_index(display_index: nat, asset_view: str, reveal_category: str) -> FunctionCallResultNat:
    '''
    Returns a raw asset index based on display index, asset view, and reveal category.
    '''
    if asset_view is None:
        asset_view = 'image'
    if reveal_category is None:
        reveal_category = 'start'
    asset_opt = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
    if asset_opt:
        return {'ok':asset_opt}
    else:
        return {'err':'Sorry, an asset index was not found from that display index, asset view, and reveal category.'}

@query
def get_transaction(transaction_id: nat64) -> opt[TransferEvent]:
    '''
    Returns an individual transaction based on the transaction index.
    '''
    transaction_opt = transactions.get(transaction_id)
    return transaction_opt

def get_registry_items() -> list[tuple[nat16,str]]:
    '''
    A helper function to get registry items since ".items()" is not allowed on stable structures yet.
    '''
    final_registry: list[tuple[nat16,str]] = []
    for nft_index in range(registry.len()):
        registry_opt = registry.get(nft_index)
        registry_value = registry_opt if registry_opt is not None else ''
        final_registry.append((nft_index,registry_value))
    return final_registry

@query
def get_registry() -> list[tuple[nat, str]]:
    '''
    Return the registry for the collection.
    '''
    return get_registry_items()

@query
def get_nft(nft_index: nat) -> opt[Nft]:
    '''
    Get metadata for a specific NFT.
    '''
    nft_opt = nfts.get(nft_index)
    return nft_opt

def get_nfts_items() -> list[tuple[nat16,opt[Nft]]]:
    '''
    A helper function to return items for NFTs since ".items()" is not allowed on stablebtree yet.
    '''
    final_nfts: list[tuple[nat16,opt[Nft]]] = []
    for nft_index in range(nfts.len()):
        nft_opt = nfts.get(nft_index)
        final_nfts.append((nft_index,nft_opt))
    return final_nfts

@query
def get_all_nfts() -> list[tuple[nat, opt[Nft]]]:
    '''
    Returns all NFTs.
    '''
    return get_nfts_items()

@query
def get_owner(nft_index: nat) -> opt[str]:
    '''
    Returns the wallet address which owns a particulat NFT index.
    '''
    return registry.get(nft_index)

@query
def get_tokens(address: str) -> opt[list[nat]]:
    '''
    Returns an array of tokens owned by a particular wallet address.
    '''
    return address_registry.get(address)

def get_permissions(permission_type: str) -> list[str]:
    '''
    A helper function that determines permissions. Level 1 is least secure. Level 3 is most secure.
    '''
    canister_opt = canister_metadata.get(0)
    if canister_opt:
        if permission_type == 'level_1':
            return canister_opt['super_admin'] + canister_opt['owners'] + canister_opt['collaborators']
        elif permission_type == 'level_2':
            return canister_opt['super_admin'] + canister_opt['owners']
        elif permission_type == 'level_3':
            return canister_opt['super_admin']
        else:
            return []
    else:
        return []

@update
def set_text_trait(update_metadata_text: UpdateMetadataText) -> FunctionCallResult:
    '''
    Function to set a text trait for an NFT.
    '''
    if str(ic.caller()) in get_permissions('level_1'):
        nft_index = update_metadata_text['nft_index']
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            metadata_index = nft_opt['metadata_index']
            metadata_opt = nft_metadata.get(metadata_index)
            if metadata_opt:
                metadata_opt[f"{update_metadata_text['trait_type']}_traits_{update_metadata_text['trait_format']}"][update_metadata_text['trait_name']] = update_metadata_text['trait_value']
                nft_metadata.insert(metadata_index,metadata_opt)
                new_event('Set NFT trait',f"NFT {update_metadata_text['nft_index']} trait {update_metadata_text['trait_name']} was updated to {update_metadata_text['trait_value']}")
                return {'ok':f"{update_metadata_text['trait_name']} was successfully updated for index {update_metadata_text['nft_index']}."}
            else:
                return {'err':'No metadata index found as listed in the NFT.'}
        else:
            return {'err':'NFT index not found.'}
    else:
        return {'err':'You must be admin to call update nft trait.'}
    
@update
def set_number_trait(update_metadata_number: UpdateMetadataNumber) -> FunctionCallResult:
    '''
    Function to set a number trait for an NFT.
    '''
    if str(ic.caller()) in get_permissions('level_1'):
        nft_index = update_metadata_number['nft_index']
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            metadata_index = nft_opt['metadata_index']
            metadata_opt = nft_metadata.get(metadata_index)
            if metadata_opt:
                metadata_opt[f"{update_metadata_number['trait_type']}_traits_{update_metadata_number['trait_format']}"][update_metadata_number['trait_name']] = update_metadata_number['trait_value']
                new_event('Set NFT trait',f"NFT {update_metadata_number['nft_index']} trait {update_metadata_number['trait_name']} was updated to {update_metadata_number['trait_value']}")
                return {'ok':f"{update_metadata_number['trait_name']} was successfully updated for index {update_metadata_number['nft_index']}."}
            else:
                return {'err':'No metadata index found as listed in the NFT.'}
        else:
            return {'err':'NFT index not found.'}
    else:
        return {'err':'You must be admin to call update nft trait.'}

@query
def get_dynamic_traits_text(nft_index: nat, attribute_name: str) -> FunctionCallResult:
    '''
    Returns the dynamic trait value for a particular NFT index and attribute name.
    '''
    nft_opt = nfts.get(nft_index)
    if nft_opt:
        metadata_index = nft_opt['metadata_index']
        metadata_opt = nft_metadata.get(metadata_index)
        if metadata_opt:
            dynamic_traits_text = metadata_opt['dynamic_traits_text']
            trait_attribute = [x[1] for x in dynamic_traits_text if x[0] == attribute_name]
            if len(trait_attribute) > 0:
                return {'ok':trait_attribute[0]}
            else:
                return {'err':'Dynamic trait not found.'}
        return {'err':'Metadata index incorrectly configured on NFT.'}
    return {'err':'NFT index not found.'}

@query
def get_dynamic_traits_number(nft_index: nat, attribute_name: str) -> FunctionCallResultFloat64:
    '''
    Returns the dynamic traits number for a particular NFT index and attribute name.
    '''
    nft_opt = nfts.get(nft_index)
    if nft_opt:
        metadata_index = nft_opt['metadata_index']
        metadata_opt = nft_metadata.get(metadata_index)
        if metadata_opt:
            dynamic_traits_number = metadata_opt['dynamic_traits_number']
            trait_attribute = [x[1] for x in dynamic_traits_number if x[0] == attribute_name]
            if len(trait_attribute) > 0:
                return {'ok':trait_attribute[0]}
            else:
                return {'err':'Dynamic trait not found.'}
        return {'err':'Metadata index incorrectly configured on NFT.'}
    return {'err':'NFT index not found.'}

@query
def get_static_traits_text(nft_index: nat, attribute_name: str) -> FunctionCallResult:
    '''
    Returns the static traits text for a particular NFT index and attribute name.
    '''
    nft_opt = nfts.get(nft_index)
    if nft_opt:
        metadata_index = nft_opt['metadata_index']
        metadata_opt = nft_metadata.get(metadata_index)
        if metadata_opt:
            static_traits_text = metadata_opt['static_traits_text']
            trait_attribute = [x[1] for x in static_traits_text if x[0] == attribute_name]
            if len(trait_attribute) > 0:
                return {'ok':trait_attribute[0]}
            else:
                return {'err':'Static trait not found.'}
        return {'err':'Metadata index incorrectly configured on NFT.'}
    return {'err':'NFT index not found.'}

@query
def get_static_traits_number(nft_index: nat, attribute_name: str) -> FunctionCallResultFloat64:
    '''
    Returns the static traits number for a particular NFT index and attribute name.
    '''
    nft_opt = nfts.get(nft_index)
    if nft_opt:
        metadata_index = nft_opt['metadata_index']
        metadata_opt = nft_metadata.get(metadata_index)
        if metadata_opt:
            static_traits_number = metadata_opt['static_traits_number']
            trait_attribute = [x[1] for x in static_traits_number if x[0] == attribute_name]
            if len(trait_attribute) > 0:
                return {'ok':trait_attribute[0]}
            else:
                return {'err':'Static trait not found.'}
        return {'err':'Metadata index incorrectly configured on NFT.'}
    return {'err':'NFT index not found.'}

@query
def get_rarity_score(nft_index: nat, attribute_name: str) -> FunctionCallResultFloat64:
    '''
    Returns the rarity scores for a specific NFT index and score type.
    '''
    nft_opt = nfts.get(nft_index)
    if nft_opt:
        metadata_index = nft_opt['metadata_index']
        metadata_opt = nft_metadata.get(metadata_index)
        if metadata_opt:
            rarity_scores = metadata_opt['rarity_scores']
            if rarity_scores:
                trait_attribute = [x[1] for x in rarity_scores if x[0] == attribute_name]
                if len(trait_attribute) > 0:
                    return {'ok':trait_attribute[0]}
                else:
                    return {'err':'Rarity score not found.'}
            return {'err':'No rarity scores found.'}
        else:
            return {'err':'Metadata not present for selected NFT index.'}
    else: return {'err':'NFT index not found.'}

@update
def compute_rarity() -> FunctionCallResult:
    '''
    Use static text and static number traits (dynamic traits should not be included) to create multiple rarity scores, saved in the NFT and separately in arrays.
    '''
    return rarity_computation.run_rarity_calcs(canister_metadata, nfts, registry, nft_metadata, nft_rarity_scores, str(ic.caller()))

@query
def get_rarity_data(rarity_category: str) -> list[tuple[nat16, float64]]:
    '''
    Get all rarity data across all NFTs for a particular rarity score category.
    '''
    rarity_opt = nft_rarity_scores.get(rarity_category)
    if rarity_opt:
        return rarity_opt
    return []

@query
def get_canister_metadata() -> opt[CanisterMeta]:
    '''
    Returns all canister metadata.
    '''
    return canister_metadata.get(0)

@update
def set_canister_metadata(canister_data: SetCanister) -> FunctionCallResult:
    '''
    Set any canister metadata value using SetCanister.
    '''
    if str(ic.caller()) in get_permissions('level_1'):
        for key in canister_data.keys():
            canister_opt = canister_metadata.get(0)
            if canister_opt:
                canister_opt[key] = canister_data[key]
                canister_metadata.insert(0,canister_opt)
            else:
                return {'err':'Sorry, canister metadata has not been set.'}
        return {'ok':'Successfully set canister metadata.'}
    else:
        return {'err':'Sorry, only admin can call set canister metadata.'}

@update
def set_max_number_of_nfts_to_mint(new_max_number_of_nfts_to_mint: nat) -> FunctionCallResult:
    '''
    Sets the max number of NFTs to mint.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            canister_opt['max_number_of_nfts_to_mint'] = new_max_number_of_nfts_to_mint
            canister_metadata.insert(0,canister_opt)
            new_event('Change Number of NFTs to Mint',f"Number of NFTs to mint changed to {new_max_number_of_nfts_to_mint}")
            return {'ok':'New max number of NFTs set successfully.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call set max number of NFTs.'}

@update
def set_collection_name(new_collection_name: str) -> FunctionCallResult:
    '''
    Sets the collection name.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            canister_opt['collection_name'] = new_collection_name
            canister_metadata.insert(0,canister_opt)
            new_event('Edit Collection Meta',f"Collection name was changed to {new_collection_name}")
            return {'ok':'New collection name set successfully.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call set collection name.'}
    
@update
def set_burn_address(new_burn_address: str) -> FunctionCallResult:
    '''
    Sets the burn address
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            canister_opt['burn_address'] = new_burn_address
            canister_metadata.insert(0,canister_opt)
            new_event('Edit Collection Metadata',f"Burn address changed to {new_burn_address}")
            return {'ok':'Collection burn address set successfully.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call set burn address.'}

@update
def set_new_creator_royalty(royalty_array: list[tuple[str, nat]]) -> FunctionCallResult:
    '''
    Sets new creator royalty. This overrides any defaults.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            canister_opt['royalty'] = royalty_array
            canister_metadata.insert(0,canister_opt)
            new_event('Edit Collection Metadata',f"Creator royalty changed to {royalty_array}")
            return {'ok':'Creator royalty set successfully.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call set creator royalty.'}

@update
def remove_royalty_address(royalty_address: str) -> FunctionCallResult:
    '''
    Removes a royalty address.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        address = sanitize_address(royalty_address)
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            royalty_array = canister_opt['royalty']
            if len(address) == 64:
                for royalty in list(royalty_array):
                    if royalty[0] == address:
                        royalty_array.remove(royalty)
                        canister_opt['royalty'] = royalty_array
                        canister_metadata.insert(0,canister_opt)
                        return {'ok':f'Royalty address {address} successfully removed.'}
                else:
                    return {'err':'Sorry, this address was not found in the royalty array.'}
            else:
                return {'err':f'Sorry, this address is length {len(address)} when it should be length 64.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Sorry, only super admin or owner can call remove royalty address.'}

@update
def add_royalty_address(royalty_info: tuple[str, nat]) -> FunctionCallResult:
    '''
    Adds a new royalty address to the existing array.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        address = sanitize_address(royalty_info[0])
        if len(address) == 64:
            if royalty_info[1] > 500 and royalty_info[1] < 50000:
                canister_opt = canister_metadata.get(0)
                if canister_opt:
                    royalty_array = canister_opt['royalty']
                    royalty_array.append((address, royalty_info[1]))
                    canister_opt['royalty'] = royalty_array
                    canister_metadata.insert(0,canister_opt)
                    return {'ok':f'Royalty address {royalty_info[0]} successfully added.'}
                else:
                    return {'err':'Sorry, metadata has not been set on this canister yet.'}
            else:
                return {'err':'Sorry, your royalty percentage does not fall within 500 (0.5%) and 50k (50%).'}
        else:
            return {'err':f'Sorry, this address is not the correct length of 64. It is {len(address)}.'}
    else:
        return {'err':'Sorry, only super admin or owners can call add royalty address.'}

@query
def get_royalty_addresses() -> list[tuple[str, nat]]:
    '''
    Returns the royalty address array showing wallet address and amount.
    '''
    canister_opt = canister_metadata.get(0)
    if canister_opt:
        return canister_opt['royalty']
    else:
        return []

@update
def add_collection_super_admin(super_admin: str) -> FunctionCallResult:
    '''
    Add new super admin.
    '''
    if str(ic.caller()) in get_permissions('level_3'):
        super_admin = super_admin.strip()
        if len(super_admin) == 27 or len(super_admin) == 63:
            canister_opt = canister_metadata.get(0)
            if canister_opt:
                super_admin_array = canister_opt['super_admin']
                super_admin_array.append(super_admin)
                canister_opt['super_admin'] = super_admin_array
                canister_metadata.insert(0,canister_opt)
                new_event('Add Super Admin',f"New collection owner added {super_admin}.")
                return {'ok':f'Collection super admin {super_admin} added successfully.'}
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
        return {'err':'The principal you are trying to add is not the correct length.'}
    else:
        return {'err':'Only super admin can call add collection super admin.'}

@update
def remove_collection_super_admin(super_admin: str) -> FunctionCallResult:
    '''
    Remove super admin.
    '''
    if str(ic.caller()) in get_permissions('level_3'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            super_admin_array = canister_opt['super_admin']
            if super_admin in super_admin_array:
                super_admin_array.remove(super_admin)
                canister_opt['super_admin'] = super_admin_array
                canister_metadata.insert(0,canister_opt)
                new_event('Remove Super Admin',f"Collection super admin {super_admin} removed from super admin array.")
                return {'ok':f'Collection super admin {super_admin} removed successfully.'}
            else:
                return {'err':'Sorry, that principal is not listed as a current super admin.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Sorry, only super admin can call remove super admin.'}

@query
def get_collection_super_admin() -> list[str]:
    '''
    Returns current super admin.
    '''
    canister_opt = canister_metadata.get(0)
    if canister_opt:
        return canister_opt['super_admin']
    else:
        return []

@update
def add_collection_owner(collection_owner: str) -> FunctionCallResult:
    '''
    Add new collection owner.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        collection_owner = collection_owner.strip()
        if len(collection_owner) == 27 or len(collection_owner) == 63:
            canister_opt = canister_metadata.get(0)
            if canister_opt:
                current_owners = canister_opt['owners']
                current_owners.append(str(collection_owner))
                canister_opt['owners'] = current_owners
                canister_metadata.insert(0,canister_opt)
                new_event('Add Owner',f"New collection owner added {collection_owner}.")
                return {'ok':f'Collection owner {collection_owner} added successfully.'}
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
        return {'err':'The principal you are trying to add is not the correct length.'}
    else:
        return {'err':'Only admin can call add collection owner.'}

@update
def remove_collection_owner(owner: str) -> FunctionCallResult:
    '''
    Remove collection owner.
    '''
    if str(ic.caller()) in get_permissions('level_3'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            owner_array = canister_opt['owners']
            if owner in owner_array:
                owner_array.remove(owner)
                canister_opt['owners'] = owner_array
                canister_metadata.insert(0,canister_opt)
                new_event('Remove Super Admin',f"Collection owner {owner} removed from owner array.")
                return {'ok':f'Collection owner {owner} removed successfully.'}
            else:
                return {'err':'Sorry, that principal is not listed as a current super admin.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call remove collection owner.'}

@query
def get_collection_owners() -> list[str]:
    '''
    Get all collection owners.
    '''
    canister_opt = canister_metadata.get(0)
    if canister_opt:
        return canister_opt['owners']
    else:
        return []

@update
def add_collection_collaborator(collection_collaborator: str) -> FunctionCallResult:
    '''
    Add new collection collaborator.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        collection_collaborator = collection_collaborator.strip()
        if len(collection_collaborator) == 27 or len(collection_collaborator) == 63:
            canister_opt = canister_metadata.get(0)
            if canister_opt:
                current_collaborators = canister_opt['collaborators']
                current_collaborators.append(str(collection_collaborator))
                canister_opt['owners'] = current_collaborators
                canister_metadata.insert(0,canister_opt)
                new_event('Add Owner',f"New collection owner added {collection_collaborator}.")
                return {'ok':f'Collection owner {collection_collaborator} added successfully.'}
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
        return {'err':'The principal you are trying to add is not the correct length.'}
    else:
        return {'err':'Only admin can call add collection collaborator.'}

@update
def remove_collection_collaborator(collaborator: str) -> FunctionCallResult:
    '''
    Remove a specific collection collaborator.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            collaborator_array = canister_opt['collaborators']
            if collaborator in collaborator_array:
                collaborator_array.remove(collaborator)
                canister_opt['owners'] = collaborator_array
                canister_metadata.insert(0,canister_opt)
                new_event('Remove Super Admin',f"Collection owner {collaborator} removed from collaborator array.")
                return {'ok':f'Collection owner {collaborator} removed successfully.'}
            else:
                return {'err':'Sorry, that principal is not listed as a current super admin.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call remove collection collaborator.'}

@query
def get_collection_collaborators() -> list[str]:
    '''
    Return all collection collaborators.
    '''
    canister_opt = canister_metadata.get(0)
    if canister_opt:
        return canister_opt['collaborators']
    else:
        return []

@update
def set_license(license: str) -> FunctionCallResult:
    '''
    Set NFT license globally at the collection level.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        canister_opt = canister_metadata.get(0)
        if canister_opt:
            canister_opt['license'] = license
            canister_metadata.insert(0,canister_opt)
            new_event('Edit Collection Metadata',f"License changed to {license}")
            return {'ok':'Collection license set successfully.'}
        else:
            return {'err':'Sorry, metadata has not been set on this canister yet.'}
    else:
        return {'err':'Only admin can call set burn address.'}

@update
def upload_raw_asset(raw_asset: RawAssetForUpload) -> FunctionCallResultNat:
    '''
    Upload raw asset. Assets are stored individually and can then be pulled into an NFT via asset displays, asset views, and reveal categories.
    '''
    chunk = raw_asset['chunk']
    raw_asset_index = raw_asset['raw_asset_index']
    if str(ic.caller()) in get_permissions('level_1'):
        if chunk == 0 or chunk is None:
            if raw_asset_index is None:
                if raw_assets.len() == 0:
                    raw_asset_index = 0
                else:
                    max_array_opt = max_of_arrays.get('raw_assets')
                    if max_array_opt:
                        raw_asset_index = max_array_opt + 1
                        max_of_arrays.insert('raw_assets',raw_asset_index)
                    else:
                        max_of_arrays.insert('raw_assets',1)
                        raw_asset_index = 0

            raw_assets.insert(raw_asset_index,{
                'asset_file_name':raw_asset['asset_file_name'],
                'asset_bytes':[raw_asset['asset_bytes']],
                'asset_file_type':raw_asset['asset_file_type'],
                'thumb_file_name':raw_asset['thumb_file_name'] if raw_asset['thumb_file_name'] else 'default',
                'thumbnail_bytes':raw_asset['thumbnail_bytes'] if raw_asset['thumbnail_bytes'] else bytes(),
                'thumb_file_type':raw_asset['thumb_file_type'] if raw_asset['thumb_file_type'] else 'png'
            })
            new_event('Asset was uploaded',f"Asset {raw_asset_index} was uploaded.")
            return {'ok':raw_asset_index}
        else:
            if raw_asset_index is not None:
                raw_asset_opt = raw_assets.get(raw_asset_index)
                if raw_asset_opt:
                    current_bytes_array = raw_asset_opt['asset_bytes']
                    current_bytes_array.append(raw_asset['asset_bytes'])
                    raw_asset_opt['asset_bytes'] = current_bytes_array
                    raw_assets.insert(raw_asset_index,raw_asset_opt)
                    return {'ok':chunk}
                else:
                    return {'err':'Sorry, that asset index could not be found.'}
            else:
                return {'err':'When passing a chunk greater than 0 you must pass in an asset index'}
    else:
        return {'err':'Only admin can call upload asset.'}

@update
def create_full_asset_display(display: AssetDisplayForUpload) -> FunctionCallResultNat:
    '''
    A full asset display will have a display index, an asset view, and a reveal category, all pointing to a single asset index.
    '''
    display_index = display['display_index']
    asset_view = display['asset_view']
    reveal_category = display['reveal_category']
    raw_asset_index = display['raw_asset_index']
    
    if str(ic.caller()) in get_permissions('level_1'):
        if asset_view is None:
            asset_view = 'image'
        if reveal_category is None:
            reveal_category = 'start'
        
        if display_index is None:
            if asset_views.len() == 0:
                display_index = 0
            else:
                max_length_opt = max_of_arrays.get('asset_display')
                if max_length_opt:
                    display_index = max_length_opt + 1
                else:
                    display_index = 0
                    max_of_arrays.insert('asset_display',0)

        display_to_raw_asset.insert({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category},raw_asset_index)
        new_event('Asset was uploaded',f"Display {display_index} was uploaded.")
        return {'ok':display_index}
    else:
        return {'err':'Only admin can call upload asset.'}

@update
def create_many_full_asset_displays(display_list: list[AssetDisplayForUpload]) -> FunctionCallResult:
    '''
    A convenience function for speed. Allows creating many full asset displays all at the same time in the same update call.
    '''
    if str(ic.caller()) in get_permissions('level_1'):
        for display in display_list:
            display_index = display['display_index']
            asset_view = display['asset_view']
            reveal_category = display['reveal_category']
            raw_asset_index = display['raw_asset_index']
            if asset_view is None:
                asset_view = 'image'
            if reveal_category is None:
                reveal_category = 'start'
            
            if display_index is None:
                if asset_views.len() == 0:
                    display_index = 0
                else:
                    max_length_opt = max_of_arrays.get('asset_display')
                    if max_length_opt:
                        display_index = max_length_opt + 1
                    else:
                        display_index = 0
                        max_of_arrays.insert('asset_display',0)

            display_to_raw_asset.insert({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category},raw_asset_index)
            new_event('Asset was uploaded',f"Display {display_index} was uploaded.")
        return {'ok':f'You successfully uploaded {len(display_list)} asset displays.'}
    else:
        return {'err':'Only admin can call upload asset.'}

def get_raw_asset_items() -> list[tuple[nat16,str,str,str,str]]:
    '''
    A helper function to return all raw assets without actually returning the image values.
    '''
    final_assets: list[tuple[nat16,str,str,str,str]] = []
    for raw_asset_index in range(raw_assets.len()):
        raw_asset_opt = raw_assets.get(raw_asset_index)
        if raw_asset_opt:
            final_assets.append((raw_asset_index,raw_asset_opt['asset_file_name'],raw_asset_opt['asset_file_type'],raw_asset_opt['thumb_file_name'],raw_asset_opt['thumb_file_type']))
    return final_assets

@query
def get_raw_assets() -> list[tuple[nat16,str,str,str,str]]:
    '''
    Returns all asset names, file types, etc.
    '''
    return get_raw_asset_items()

@update
def edit_raw_asset(raw_asset: EditRawAsset) -> FunctionCallResult:
    '''
    A nice "opt" all to edit an asset however you would like.
    '''
    chunk = raw_asset['chunk']
    raw_asset_index = raw_asset['raw_asset_index']

    if str(ic.caller()) in get_permissions('level_1'):
        if chunk == 0 or chunk is None:
            opt_asset = raw_assets.get(raw_asset_index)
            if opt_asset:
                if raw_asset['asset_bytes']:
                    opt_asset['asset_bytes'] = [raw_asset['asset_bytes']]
                    new_event('Edit Asset',f"Asset {raw_asset_index} was changed.")

                if raw_asset['thumbnail_bytes']:
                    opt_asset['thumbnail_bytes'] = raw_asset['thumbnail_bytes']
                    new_event('Edit Thumbnail',f"Asset thumbnail {raw_asset_index} was changed.")
                        
                if raw_asset['asset_file_name']:
                    opt_asset['asset_file_name'] = raw_asset['asset_file_name']
                    new_event('Edit Asset Filename',f"Asset {raw_asset_index} filename was changed to '{raw_asset['asset_file_name']}'.")

                if raw_asset['thumb_file_name']:
                    opt_asset['thumb_file_name'] = raw_asset['thumb_file_name']
                    new_event('Edit Asset Filename',f"Asset {raw_asset_index} filename was changed to '{raw_asset['thumb_file_name']}'.")

                if raw_asset['asset_file_type']:
                    opt_asset['asset_file_type'] = raw_asset['asset_file_type']
                    new_event('Edit Asset File Type',f"Asset {raw_asset_index} file_type was changed to '{raw_asset['asset_file_type']}'.")
                
                if raw_asset['thumb_file_type']:
                    opt_asset['thumb_file_type'] = raw_asset['thumb_file_type']
                    new_event('Edit Asset File Type',f"Asset {raw_asset_index} file_type was changed to '{raw_asset['thumb_file_type']}'.")
            
                raw_assets.insert(raw_asset_index,opt_asset)
                return {'ok':'Asset successfully updated'}
            else:
                return {'err':'Sorry, this asset index does not exist so you cannot edit it.'}
        else:
            if raw_asset['asset_bytes']:
                raw_asset_opt = raw_assets.get(raw_asset_index)
                if raw_asset_opt:
                    current_bytes_array = raw_asset_opt['asset_bytes']
                    current_bytes_array.append(raw_asset['asset_bytes'])
                    raw_asset_opt['asset_bytes'] = current_bytes_array
                    raw_assets.insert(raw_asset_index,raw_asset_opt)
                    return {'ok':f"You successfully added an asset chunk to your existing asset."}
                else:
                    return {'err':'Sorry that raw asset could not be found.'}
            else:
                return {'err':'If you supply a chunk you must also supply an asset_bytes.'}
    else:
        return {'err':'Only admin can call edit asset.'}

@update
def remove_raw_asset(raw_asset_index: nat) -> FunctionCallResult:
    '''
    Remove a raw asset index from existence. Careful, you can't get these back.
    '''
    if str(ic.caller()) in get_permissions('level_1'):
        raw_asset_opt = raw_assets.get(raw_asset_index)
        if raw_asset_opt:
            raw_assets.remove(raw_asset_index)
            new_event('Remove Asset',f"Asset {raw_asset_index} was removed.")
            return {'ok':'Asset successfully deleted.'}
        else:
            return {'err':'Sorry that asset index does not exist.'}
    else:
        return {'err':'You must be an admin to call remove asset.'}

@update
def mint_many_NFTs(nft_objects: list[NftForMinting]) -> ManyMintResult:
    '''
    A convenience function to mint many (up to 1000 possibly) NFTs in a single update call.
    '''
    error_messages: list[str] = []
    if str(ic.caller()) in get_permissions('level_2'):
        canister_meta_opt = canister_metadata.get(0)
        if canister_meta_opt:
            if registry.len() + len(nft_objects) < canister_meta_opt['max_number_of_nfts_to_mint']:
                for nft_object in nft_objects:
                    nft_index = nft_object['nft_index']
                    asset_url = nft_object['asset_url']
                    thumbnail_url = nft_object['thumbnail_url']
                    display_index = nft_object['display_index']
                    metadata_index = nft_object['metadata_index']
                    to_address = sanitize_address(nft_object['to_address'])
                    
                    if not nft_index:
                        if registry.len() == 0:
                            nft_index = 0
                        else:
                            registry_max_opt = max_of_arrays.get('registry')
                            if registry_max_opt:
                                nft_index = registry_max_opt + 1
                                max_of_arrays.insert('registry',nft_index)
                            else:
                                nft_index = 0
                                max_of_arrays.insert('registry',nft_index)
                    
                    if not registry.contains_key(nft_index):
                        if registry.len() < canister_meta_opt['max_number_of_nfts_to_mint']:
                            if len(to_address) == 64:
                                registry.insert(nft_index,to_address)

                                address_registry_opt = address_registry.get(to_address)
                                if address_registry_opt:
                                    address_registry_opt.append(nft_index)
                                    address_registry.insert(to_address,address_registry_opt)
                                else:
                                    address_registry.insert(to_address,[nft_index])


                                nfts.insert(nft_index,{
                                    'nft_index': nft_index,
                                    'asset_url': asset_url,
                                    'thumbnail_url': thumbnail_url,
                                    'display_index': display_index,
                                    'metadata_index': metadata_index
                                })
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
    The official NFT minting method.
    '''
    nft_index = nft_object['nft_index']
    asset_url = nft_object['asset_url']
    thumbnail_url = nft_object['thumbnail_url']
    display_index = nft_object['display_index']
    metadata_index = nft_object['metadata_index']
    to_address = sanitize_address(nft_object['to_address'])
    
    if not nft_index:
        if registry.len() == 0:
            nft_index = 0
        else:
            registry_max_opt = max_of_arrays.get('registry')
            if registry_max_opt:
                nft_index = registry_max_opt + 1
                max_of_arrays.insert('registry',nft_index)
            else:
                nft_index = 0
                max_of_arrays.insert('registry',nft_index)
    
    canister_meta_opt = canister_metadata.get(0)
    if canister_meta_opt:
        if not registry.contains_key(nft_index):
            if registry.len() < canister_meta_opt['max_number_of_nfts_to_mint']:
                if len(to_address) == 64:
                    registry.insert(nft_index,to_address)

                    address_registry_opt = address_registry.get(to_address)
                    if address_registry_opt:
                        address_registry_opt.append(nft_index)
                        address_registry.insert(to_address,address_registry_opt)
                    else:
                        address_registry.insert(to_address,[nft_index])

                    nfts.insert(nft_index,{
                        'nft_index': nft_index,
                        'asset_url': asset_url,
                        'thumbnail_url': thumbnail_url,
                        'display_index': display_index,
                        'metadata_index': metadata_index
                    })
                    new_event('Mint New NFT',f"NFT {nft_index} was minted with display_index {display_index} asset_url {asset_url} thumbnail_url {thumbnail_url} metadata {metadata}")
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
    A nice "opt" all enabling editing of an NFT across its fields.
    '''
    nft_index = nft_object['nft_index']
    asset_url = nft_object['asset_url']
    thumbnail_url = nft_object['thumbnail_url']
    display_index = nft_object['display_index']
    metadata_index = nft_object['metadata_index']

    if str(ic.caller()) in get_permissions('level_1'):
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            if asset_url:
                nft_opt['asset_url'] = asset_url
                new_event('Edit NFT Asset URL',f"NFT {nft_index} asset_url was changed to '{asset_url}'.")
                    
            if thumbnail_url:
                nft_opt['thumbnail_url'] = thumbnail_url
                new_event('Edit NFT Thumbnail URL',f"NFT {nft_index} thumbnail_url was changed from to '{thumbnail_url}'.")

            if display_index is not None:
                nft_opt['display_index'] = display_index
                new_event('Edit Asset Index',f"Asset {display_index} was changed to '{display_index}'.")

            if metadata:
                nft_opt['metadata_index'] = metadata_index
                new_event('Edit NFT Metadata',f"NFT {nft_index} metadata was changed to '{metadata_index}'.")

            nfts.insert(nft_index,nft_opt)
            return {'ok':'NFT edited successfully.'}
        else:
            return {'err':'This NFT does not exist'}
    else:
        return {'err':'Sorry, only admin can call edit asset'}

@update
def unmint_nft(nft_index: nat) -> FunctionCallResult:
    '''
    Different than burning. Unminting removes from existence. Index no longer exists.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        current_owner_opt = registry.get(nft_index)
        if current_owner_opt:
            registry.remove(nft_index)
            address_opt = address_registry.get(current_owner_opt)
            if address_opt:
                address_opt.remove(nft_index)
                address_registry.insert(current_owner_opt,address_opt)
            nfts.remove(nft_index)

            new_event('Unmint NFT',f"NFT {nft_index} has been unminted and completely removed from the canister")
            new_transfer_event(current_owner_opt,'',nft_index,'Unminted')
            return {'ok':'NFT successfully unminted.'}
        else:
            return {'err':'NFT does not exist yet.'}
    else:
        return {'err':'Only admin can call unmint NFT'}

@update
def burn_nft(nft_index: nat) -> FunctionCallResult:
    '''
    Transfers NFT to the burn address specified in the canister. Still shows up in registry.
    '''
    canister_opt = canister_metadata.get(0)
    if canister_opt:
        burn_address = sanitize_address(canister_opt['burn_address'])
        current_owner_opt = registry.get(nft_index)
        if current_owner_opt:
            caller_address = str(ic.caller().to_account_id())[2:]
            if caller_address == current_owner_opt:
                registry.insert(nft_index,burn_address)
                
                address_opt = address_registry.get(current_owner_opt)
                if address_opt:
                    address_opt.remove(nft_index)
                    address_registry.insert(current_owner_opt,address_opt)
                
                burn_opt = address_registry.get(burn_address)
                if burn_opt:
                    burn_opt.append(nft_index)
                    address_registry.insert(burn_address,burn_opt)

                new_transfer_event(caller_address,burn_address,nft_index,'Burned')
                return {'ok':'NFT burned successfully.'}
            else:
                return {'err':'Sorry, you do not own this NFT.'}
        else:
            return {'err':'Sorry, this NFT does not exist.'}
    else:
        return {'err':'Sorry burn address has not been set yet.'}

def _transfer(nft_index: nat, from_address: str, to_address: str) -> FunctionCallResult:
    '''
    The official transfer function. EXT transfer uses this under the hood.
    '''
    current_owner_opt = registry.get(nft_index)
    if current_owner_opt:
        if from_address == current_owner_opt:
            if len(to_address) == 64:
                
                registry.insert(nft_index,to_address)

                to_nfts_owner_opt = address_registry.get(to_address)
                if to_nfts_owner_opt:
                    to_nfts_owner_opt.append(nft_index)
                    address_registry.insert(to_address,to_nfts_owner_opt)
                else:
                    address_registry.insert(to_address,[nft_index])

                from_nfts_owned_opt = address_registry.get(from_address)
                if from_nfts_owned_opt:
                    from_nfts_owned_opt.remove(nft_index)
                    address_registry.insert(from_address,from_nfts_owned_opt)

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
    '''
    Call to management canister to get on-chain randomness.
    '''
    management_canister = ManagementCanister(Principal.from_str('aaaaa-aa'))
    randomness_result: CanisterResult[blob] = yield management_canister.raw_rand()
    if randomness_result.err is not None:
        return bytes()
    return randomness_result.ok

@update
def airdrop(to_addresses: list[str], nft_indexes: opt[list[nat]]) -> Async[FunctionCallResult]:
    '''
    A really nice airdrop function that takes a list of to_addresses, an option nft_index array, and then airdrops truly randomly.
    '''
    if str(ic.caller()) in get_permissions('level_2'):
        available_tokens_opt = address_registry.get('0000')
        if available_tokens_opt:
            if nft_indexes is not None:
                if len(to_addresses) == len(nft_indexes):
                    if set(nft_indexes).issubset(set(available_tokens_opt)):
                        for to_address,nft_index in zip(to_addresses,nft_indexes):
                            to_address = sanitize_address(to_address)
                            
                            registry.insert(nft_index, to_address)
                            
                            from_nfts_owned_opt = address_registry.get('0000')
                            if from_nfts_owned_opt:
                                from_nfts_owned_opt.remove(nft_index)
                                address_registry.insert('0000',from_nfts_owned_opt)
                            
                            to_nfts_owned_opt = address_registry.get(to_address)
                            if to_nfts_owned_opt:
                                to_nfts_owned_opt.append(nft_index)
                                address_registry.insert(to_address, to_nfts_owned_opt)

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
                
                seed = int.from_bytes(randomness,'big')
                random = MersenneTwister(seed) # type: ignore
                random.shuffle(to_addresses) # type: ignore

                if len(to_addresses) <= len(available_tokens_opt):
                    for to_address in to_addresses:
                        to_address = sanitize_address(to_address)
                        nft_index = available_tokens_opt.pop(0)
                        registry.insert(nft_index, to_address)

                        from_nfts_owned_opt = address_registry.get('0000')
                        if from_nfts_owned_opt:
                            from_nfts_owned_opt.remove(nft_index)
                            address_registry.insert('0000',from_nfts_owned_opt)
                        
                        to_nfts_owned_opt = address_registry.get(to_address)
                        if to_nfts_owned_opt:
                            to_nfts_owned_opt.append(nft_index)
                            address_registry.insert(to_address, to_nfts_owned_opt)

                        new_transfer_event("0000",to_address,nft_index,'Admin Airdrop')

                    new_event('NFT airdropped',f"Admin airdropped {len(to_addresses)} NFTs from '0000'")
                    return {'ok':'Admin airdrop successful.'}
                else:
                    return {'err':f'Sorry, you only have {len(available_tokens_opt)} NFTs available in "0000" but you uploaded {len(to_addresses)} addresses.'}
        else:
            return {'err':'Sorry, no available tokens'}
    else:
        return {'err':"Sorry, only admin can call admin transfer."}

@update
def admin_transfer(nft_index: nat, to_address: str) -> FunctionCallResult:
    '''
    A GOD-mode method allowing this user (only super admin) to transfer an NFT even if it isn't owned by them.
    '''
    to_address = sanitize_address(to_address)
    current_owner_opt = registry.get(nft_index)
    if current_owner_opt:
        if str(ic.caller()) in get_permissions('level_3'):
            if len(to_address) == 64:
                registry.insert(nft_index,to_address)

                to_nfts_owner_opt = address_registry.get(to_address)
                if to_nfts_owner_opt:
                    to_nfts_owner_opt.append(nft_index)
                    address_registry.insert(to_address,to_nfts_owner_opt)
                else:
                    address_registry.insert(to_address,[nft_index])

                from_nfts_owned_opt = address_registry.get(current_owner_opt)
                if from_nfts_owned_opt:
                    from_nfts_owned_opt.remove(nft_index)
                    address_registry.insert(current_owner_opt,from_nfts_owned_opt)

                new_event('Admin transfer',f"Admin transferred {nft_index} from {current_owner_opt} to {to_address}")
                new_transfer_event(current_owner_opt,to_address,nft_index,'Admin Transfer')
                
                return {'ok':'Admin transfer successful.'}
            else:
                return {'err':'Incorrect length for to address.'}
        else:
            return {'err':"Sorry, only admin can call admin transfer."}
    else:
        return {'err':"Sorry, that NFT does not exist."}

@query
def get_unique_holders() -> nat:
    '''
    Returns the unique holders for the collection. Currently includes the burn address.
    '''
    unique_holders = address_registry.len()
    return unique_holders

def get_index_from_token_id(tokenid: str) -> nat:
    '''
    Helper function to convert token identifier back to NFT index.
    '''
    return int.from_bytes(Principal.from_str(tokenid).bytes[-4:],'big')

@query
def get_token_id(nft_index: nat) -> FunctionCallResult:
    '''
    Helper function that returns a token identifier for a given NFT index for this canister.
    '''
    token_id = Principal(bytes('\x0Atid','utf-8') + ic.id().bytes + int(nft_index).to_bytes(4,'big')).to_str()
    return {'ok':token_id}

def get_request_params(request_url: str) -> dict[str,str]:
    '''
    A helper function that parses the request params for http request methods.
    '''
    query_string = request_url.split('?')[-1]
    params  = dict(param.split('=') for param in query_string.split('&'))
    return params

default_response: HttpResponse = {
    'status_code':400,
    'headers':[('Content-Type','text/html')],
    'body':bytes('NFT image not found','utf-8'),
    'streaming_strategy': None,
    'upgrade': False
}

@query
def http_request_streaming_callback(token: Token) -> StreamingCallbackHttpResponse:
    '''
    The streaming callback is what gets called in call #2 if you specify a streaming callback (when you need more than 2MB message with big assets.)
    '''
    token_array = token['arbitrary_data'].split(':')
    display_index = int(token_array[0])
    asset_view = str(token_array[1])
    reveal_category = str(token_array[2])
    chunk_num = int(token_array[3])

    raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
    if raw_asset_index:
        raw_asset = raw_assets.get(raw_asset_index)
        if raw_asset:
            asset_bytes = raw_asset['asset_bytes']
            if len(asset_bytes) - 1 > chunk_num:
                return {
                    'body':asset_bytes[chunk_num],
                    'token':{'arbitrary_data':f'{display_index}:{asset_view}:{reveal_category}:{chunk_num + 1}'}
                }
            # this is the final condition, token = None means we don't have any more chunks
            else:
                return {
                    'body':asset_bytes[chunk_num],
                    'token':None
                }
        else:
            return {
                'body':bytes('Error','utf-8'),
                'token':None
            }
    else:
        return {
                'body':bytes('Error','utf-8'),
                'token':None
            }

def get_content_type(file_type: str) -> str:
    '''
    A helper function that converts nicely named file types to mime types.
    '''
    if file_type == 'png':
        content_type = 'image/png'
    elif file_type == 'jpg' or file_type == 'jpeg':
        content_type = 'image/jpeg'
    elif file_type == 'gif':
        content_type = 'image/gif'
    elif file_type == 'mp4':
        content_type = 'video/mp4'
    else:
        content_type = 'image/png'
    return content_type

def return_thumbnail_bytes(thumbnail_bytes: blob, thumb_file_type: str) -> HttpResponse:
    '''
    A helper function that returns thumbnail bytes in a specific format (no streaming since thumbnails are less than 2 MB)
    '''
    content_type = get_content_type(thumb_file_type)

    return {
        'status_code':200,
        'headers':[
            ('Content-Type', content_type)
        ],
        'body':thumbnail_bytes,
        'streaming_strategy': None,
        'upgrade': False
    }

def return_image_html(asset_url: opt[str], asset_view: opt[str], asset_file_type: str) -> HttpResponse:
    '''
    Main method that returns HTML surrounding an asset (linking to asset URL). This doesn't handle assets, just asset packaging.
    '''
    content_type = get_content_type(asset_file_type)
    if asset_view is None:
        asset_view = 'image'

    if asset_url:
        if 'image' in content_type:
            width = 800
            height = 800
            
            asset_url = asset_url.replace('&', '&amp;')
            http_response_body = bytes(f'''
                <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="width: {width}px;height: {height}px;" version="1.1" id="generated" x="0px" y="0px" viewBox="0 0 {width} {height}" xml:space="preserve">
                    <g>
                        <image href="{asset_url}&amp;view={asset_view}"/>
                    </g>
                </svg>
            ''',encoding='utf-8')
            return {
                'status_code':200,
                'headers':[
                    ('Content-Type','image/svg+xml'),
                ],
                'body':http_response_body,
                'streaming_strategy': None,
                'upgrade': False
            }
        elif 'video' in content_type:
            width = 800
            height = 800
            
            asset_url = asset_url.replace('&', '&amp;')
            http_response_body = bytes(f'''
                <!DOCTYPE html>
                <html>
                <body>
                    <video width="{width}" height="{height}" autoplay loop>
                        <source src="{asset_url}&amp;view={asset_view}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </body>
                </html>
            ''',encoding='utf-8')
            return {
                'status_code':200,
                'headers':[
                    ('Content-Type','text/html'),
                ],
                'body':http_response_body,
                'streaming_strategy': None,
                'upgrade': False
            }
        else:
            return {
                'status_code':400,
                'headers':[('Content-Type','text/html')],
                'body':bytes(f'NFT asset type {content_type} not supported','utf-8'),
                'streaming_strategy': None,
                'upgrade': False
            }        
    else:
        return default_response

def return_multipart_image_html(display_index: opt[nat], asset_view: str, reveal_category: str, asset_file_type: str, asset_bytes: opt[blob]) -> HttpResponse:
    '''
    The main asset return function that returns a single chunk or multiple chunks depending on the asset.
    '''
    if asset_bytes:
        if display_index is not None:
            if asset_file_type in ['png','jpeg','jpg','gif']:
                raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
                if raw_asset_index:
                    raw_asset_opt = raw_assets.get(raw_asset_index)
                    if raw_asset_opt:
                        raw_asset_bytes = raw_asset_opt['asset_bytes']
                        if len(raw_asset_bytes) > 1:
                            # we have more than one chunk, so use http_request_streaming_callback
                            return {
                                'status_code':200,
                                'headers':[
                                    ('Content-Type','image/png'),
                                    ('Transfer-Encoding', 'chunked')
                                ],
                                'body':asset_bytes,
                                'streaming_strategy': {
                                    'Callback':{
                                        'token':{'arbitrary_data':f'{display_index}:{asset_view}:{reveal_category}:1'}, #chunk num is 1 for the 2nd param
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
                                'body':asset_bytes,
                                'streaming_strategy': None,
                                'upgrade': False
                            }
            elif asset_file_type in ['mp4']:
                raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
                if raw_asset_index:
                    raw_asset_opt = raw_assets.get(raw_asset_index)
                    if raw_asset_opt:
                        raw_asset_bytes = raw_asset_opt['asset_bytes']
                        if len(raw_asset_bytes) > 1:
                            # we have more than one chunk, so use http_request_streaming_callback
                            return {
                                'status_code':200,
                                'headers':[
                                    ('Content-Type','video/mp4'),
                                    ('Transfer-Encoding', 'chunked')
                                ],
                                'body':asset_bytes,
                                'streaming_strategy': {
                                    'Callback':{
                                        'token':{'arbitrary_data':f'{display_index}:{asset_view}:{reveal_category}:1'}, #chunk num is 1 for the 2nd param
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
                                    ('Content-Type','video/mp4'),
                                ],
                                'body':asset_bytes,
                                'streaming_strategy': None,
                                'upgrade': False
                            }
            else:
                return {
                    'status_code':400,
                    'headers':[('Content-Type','text/html')],
                    'body':bytes(f'NFT asset type {asset_file_type} not supported','utf-8'),
                    'streaming_strategy': None,
                    'upgrade': False
                }    
        else:
            return default_response
    else:
        return default_response
    return default_response

@query
def http_request(request: HttpRequest) -> HttpResponse:
    '''
    Based on IC spec, this is what will be called when your main canister URL is visited.
    '''
    request_url = request['url']
    if '&' in request_url and '=' in request_url and '?' in request_url:
        params = get_request_params(request_url)
    else:
        return get_home_page_html(registry, address_registry, canister_metadata, events)

    if 'view' in params:
        asset_view = params['view']
    else:
        asset_view = 'image'

    if 'index' in request_url and 'thumbnail' not in request_url:
        
        nft_index = int(params['index'])
        if 'view' in params:
            asset_view = params['view']
        else:
            asset_view = 'image'
        
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            display_index = nft_opt['display_index']
            reveal_category = determine_reveal_category(display_index, asset_view)
            raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
            if raw_asset_index:
                raw_asset_opt = raw_assets.get(raw_asset_index)
                if raw_asset_opt:
                    asset_type = raw_asset_opt['asset_file_type']
                    asset_url = nft_opt['asset_url']
                    return return_image_html(asset_url, asset_view, asset_type)

        return return_image_html(None, None, '')

    elif 'index' in request_url and 'thumbnail' in request_url:
        params = get_request_params(request_url)
        nft_index = int(params['index'])
        if 'view' in params:
            asset_view = params['view']
        else:
            asset_view = 'image'
        
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            display_index = nft_opt['display_index']
            reveal_category = determine_reveal_category(display_index, asset_view)
            raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
            if raw_asset_index:
                raw_asset_opt = raw_assets.get(raw_asset_index)
                if raw_asset_opt:
                    thumbnail_bytes = raw_asset_opt['thumbnail_bytes']
                    thumb_file_type = raw_asset_opt['thumb_file_name']
                    return return_thumbnail_bytes(thumbnail_bytes, thumb_file_type)
        return return_image_html(None, None, '')

    elif 'tokenid' in request_url and 'thumbnail' not in request_url:
        params = get_request_params(request_url)
        tokenid = str(params['tokenid'])
        nft_index = get_index_from_token_id(tokenid)
        if 'view' in params:
            asset_view = params['view']
        else:
            asset_view = 'image'
        
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            display_index = nft_opt['display_index']
            reveal_category = determine_reveal_category(display_index, asset_view)
            raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
            if raw_asset_index:
                raw_asset_opt = raw_assets.get(raw_asset_index)
                if raw_asset_opt:
                    asset_type = raw_asset_opt['asset_file_type']
                    asset_url = nft_opt['asset_url']
                    return return_image_html(asset_url, asset_view, asset_type)
        return return_image_html(None, None, '')
    
    elif 'tokenid' in request_url and 'thumbnail' in request_url:
        params = get_request_params(request_url)
        tokenid = str(params['tokenid'])
        nft_index = get_index_from_token_id(tokenid)
        if 'view' in params:
            asset_view = params['view']
        else:
            asset_view = 'image'
        
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            display_index = nft_opt['display_index']
            reveal_category = determine_reveal_category(display_index, asset_view)
            raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
            if raw_asset_index:
                raw_asset_opt = raw_assets.get(raw_asset_index)
                if raw_asset_opt:
                    thumbnail_bytes = raw_asset_opt['thumbnail_bytes']
                    thumb_file_type = raw_asset_opt['thumb_file_name']
                    return return_thumbnail_bytes(thumbnail_bytes, thumb_file_type)
        return return_image_html(None, None, '')
    
    elif 'asset' in request_url and 'thumbnail' not in request_url:
        params = get_request_params(request_url)
        display_index = int(params['asset'])
        if 'view' in params:
            asset_view = params['view']
        else:
            asset_view = 'image'
        
        reveal_category = determine_reveal_category(display_index, asset_view)
        raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
        if raw_asset_index:
            raw_asset_opt = raw_assets.get(raw_asset_index)
            if raw_asset_opt:
                asset_bytes = raw_asset_opt['asset_bytes'][0]
                asset_type = raw_asset_opt['asset_file_type']
                return return_multipart_image_html(display_index, asset_view, reveal_category, asset_type, asset_bytes)
        return return_image_html(None, None, '')
    
    elif 'asset' in request_url and 'thumbnail' in request_url:
        params = get_request_params(request_url)
        display_index = int(params['asset'])
        if 'view' in params:
            asset_view = params['view']
        else:
            asset_view = 'image'
        
        reveal_category = determine_reveal_category(display_index, asset_view)
        raw_asset_index = display_to_raw_asset.get({'display_index':display_index,'asset_view':asset_view,'reveal_category':reveal_category})
        if raw_asset_index:
            raw_asset_opt = raw_assets.get(raw_asset_index)
            if raw_asset_opt:
                thumbnail_bytes = raw_asset_opt['thumbnail_bytes']
                thumb_file_type = raw_asset_opt['thumb_file_type']
                return return_thumbnail_bytes(thumbnail_bytes, thumb_file_type)
        return return_image_html(None, None, '')

    else:
        return get_home_page_html(registry, address_registry, canister_metadata, events)

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
    
    address_of_caller = str(ic.caller().to_account_id(sub_account_num))[2:]
    if from_address == address_of_caller:

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
    nft_opt = nfts.get(nft_index)
    if nft_opt:
        metadata_index = nft_opt['metadata_index']
        metadata_opt = nft_metadata.get(metadata_index)
        if metadata_opt:        
            return {
                'ok':{
                    'nonfungible':{
                        'metadata':str(metadata_opt),
                    }
                }
            }
        else:
            return {'err':{'Other':'Metadata index not setup correctly.'}}
    return {'err':{'Other':'NFT index could not be found.'}}

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
    address = sanitize_address(address)
    address_opt = address_registry.get(address)
    if address_opt:
        return {'ok':[(x,None,None) for x in address_opt]}
    else:
        return {'err':{'Other':'Sorry, address not found'}}

def get_ext_tokens_items() -> list[tuple[nat32,Metadata]]:
    final_ext_tokens: list[tuple[nat32,Metadata]] = []
    for nft_index in range(nfts.len()):
        nft_opt = nfts.get(nft_index)
        if nft_opt:
            final_ext_tokens.append((nft_opt['nft_index'],{'nonfungible':{'metadata':None}}))
    return final_ext_tokens

def get_tokens_items() -> list[tuple[nat32,Metadata]]:
    final_tokens: list[tuple[nat32,Metadata]] = []
    registry_max = max_of_arrays.get('registry')
    if registry_max:
        for nft_index in range(registry_max):
            registry_opt = registry.get(nft_index)
            if registry_opt:
                final_tokens.append((nft_index,{'nonfungible':{'metadata':None}}))
        return final_tokens
    return []

# ext_getTokens
@query
def getTokens() -> list[tuple[nat32,Metadata]]:
    return get_tokens_items()

# ext_listings (required for now to show up in Entrepot)
@query
def listings() -> list[str]:
    return []