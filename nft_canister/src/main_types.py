from kybra import nat,nat8,nat16,nat32,nat64,blob,opt,float64,Variant,Record,Query,Func,StableBTreeMap
from typing import TypeAlias

tupleType = tuple[nat16,float64]

class TraitType(Variant, total=False):
    number: float64
    string: str

class NftMetadata(Record):
    name: opt[str] # 4 + 64 characters, 68 bytes
    description: opt[str] # 4 + 300 characters, 304 bytes
    dynamic_traits_text: list[tuple[str,str]] # 3 + 6 + (64 + 64)*10, 1289 bytes
    dynamic_traits_number: list[tuple[str,float64]] # 9 + (64 + 8)*10, 729 bytes 
    static_traits_text: list[tuple[str,str]] # 1289 bytes
    static_traits_number: list[tuple[str,float64]] # 729 bytes
    rarity_scores: opt[list[tuple[str,float64]]] # 729 bytes
    license: opt[str]

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
    nft_index: nat16 # 2 bytes
    asset_url: str # max len 256, 264 bytes
    thumbnail_url: str # max len 256, 264 bytes
    display_index: nat16 # 2 bytes
    metadata_index: nat16 # 2 bytes
# 9 + 6*5 + 264 + 264 + 6 = 573

class NftForMinting(Record):
    nft_index: opt[nat]
    asset_url: str
    thumbnail_url: str
    display_index: nat
    metadata_index: nat16
    to_address: str

class ManyMintResult(Variant, total=False):
    ok: list[str]
    err: str

class TransferEvent(Record):
    from_address: str # max 64 characters
    to_address: str # max 64 characters
    timestamp: nat64 # 15 bytes
    nft_index: nat16 # 9 bytes
    transfer_type: str # max 64 characters
# 9 + 30 + 64*3 + 15 + 9 = 255

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
    event_type: str # max 64 characters
    description: str # max 256 characters
    timestamp: nat32 # 11 bytes
    actor_principal: str # max 64 characters
# 9 + 6*4 + 72 + 264 + 11 + 72 = 452

class CanisterMeta(Record):
    collection_name: str # 64 characters max, 72 bytes
    royalty: list[tuple[str, nat16]] # 3 + (6 + 72 + 9) * n
    super_admin: list[str] # 3 + 71 * n
    owners: list[str] # 3 + 71 * n
    collaborators: list[str] # 3 + 71 * n
    burn_address: str # 64 characters max, 72 bytes
    max_number_of_nfts_to_mint: nat16 # 9 bytes
    license: str # 300 characters max, 308 bytes
    blurb: opt[str] # 300 characters max
    brief: opt[str] # 300 characters max
    description: opt[str] # 500 characters max
    detailpage: opt[str] # 64 characters
    keywords: opt[str] # 256 characters
    twitter: opt[str] # 128 characters
    discord: opt[str] # 128 characters
    distrikt: opt[str] # 256 characters
    dscvr: opt[str] # 256 characters
    web: opt[str] # 256 characters
# 72 + 87*5 + 3 + 358 + 358 + 358 + 308*3 + 508 + 72 + 264 + 136 + 136 + 264 + 264 + 264 = 4416

class CanisterImage(Record):
    avatar: opt[blob] # less than 2 MB
    banner: opt[blob] # less than 2 MB
    collection: opt[blob] # less than 2 MB
# 9 + 18 + 3*1,992,294 = 5_976_909

class SetCanister(Record):
    collection_name: opt[str]
    license: opt[str]
    avatar: opt[blob]
    banner: opt[blob]
    blurb: opt[str]
    brief: opt[str]
    collection: opt[blob]
    description: opt[str]
    detailpage: opt[str]
    keywords: opt[str]
    twitter: opt[str]
    discord: opt[str]
    distrikt: opt[str]
    dscvr: opt[str]
    web: opt[str]

class Asset(Record):
    asset_file_name: str # 256 max length
    asset_bytes: list[blob] # 
    asset_file_type: str # 64 max length
    thumb_file_name: str # 256 max length
    thumbnail_bytes: blob # 1,992,294
    thumb_file_type: str # 64 max length
# 9 + 36 + 264 + 72 + 263=4 + 72 + 1_992_294 + 1_992_294 = 3_985_305

class RawAssetForUpload(Record):
    asset_file_name: str
    asset_bytes: blob
    asset_file_type: str
    thumb_file_name: opt[str]
    thumbnail_bytes: opt[blob]
    thumb_file_type: opt[str]
    chunk: opt[nat]
    raw_asset_index: opt[nat]

class EditRawAsset(Record):
    asset_file_name: opt[str]
    asset_bytes: opt[blob]
    asset_file_type: opt[str]
    thumb_file_name: opt[str]
    thumbnail_bytes: opt[blob]
    thumb_file_type: opt[str]
    chunk: opt[nat]
    raw_asset_index: nat

class AssetDisplayForUpload(Record):
    display_index: nat16
    asset_view: str
    reveal_category: str
    raw_asset_index: nat16

class DisplayToRawAsset(Record):
    display_index: nat16
    asset_view: str # max of 64 characters
    reveal_category: str # max of 64 characters
# 9 + 6*3 + 2 + 72 + 72 = 173

class AssetView(Record):
    view_name: str # max 64 characters
    view_file_type: str # max 32 characters
    default: bool # 1 byte
    priority: nat8 # 1 byte
    hidden: bool # 1 byte
# 9 + 30 + 72 + 40 + 3 = 154

class RevealCondition(Variant, total=False):
    single_time_condition: nat16 # time after which to change
    # repeated_time_condition: RepeatedTimeCondition
    # data_condition: DataCondition
    manual_condition: bool # whether true or false
# 10 + 12 + 2

class RevealCategory(Record):
    condition_index: nat16 # RevealConditions index, 2 bytes
    priority: nat16 # priority number, 2 bytes
    category_name: str # 64 character max, 72 bytes
# 9 + 18 + 76 = 175

class DisplayToRevealCategories(Record):
    display_index: nat16 # 9 bytes
    asset_view: str # max of 64 characters, 72 bytes
# 9 + 12 + 72 + 9 = 102

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