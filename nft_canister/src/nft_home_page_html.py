from kybra import StableBTreeMap,nat16,nat8, nat64
from main_types import CanisterMeta, Event, HttpResponse

def return_default_cell(name: str, value: str) -> str:
    return f'''
        <tr style="border-bottom: 1px solid #dddddd">
            <td style="padding: 12px 15px;">{name}</td>
            <td style="padding: 12px 15px;">{value}</td>
        </tr>
    '''

def event_items(events: StableBTreeMap[nat64, Event]) -> str:
    all_events: list[str] = []
    for event_index in range(events.len()):
        opt_event = events.get(event_index)
        if opt_event:
            all_events.append('<tr style="border-bottom: 1px solid #dddddd"><td style="padding: 12px 15px;">' + opt_event['event_type'] + '</td><td style="padding: 12px 15px;">' + str(opt_event['timestamp']) + '</td><td style="padding: 12px 15px;">' + opt_event['description'] + '</td></tr>')
    return ''.join(all_events)


def get_home_page_html(registry: StableBTreeMap[nat16, str], address_registry: StableBTreeMap[str, list[nat16]], canister_metadata: StableBTreeMap[nat8, CanisterMeta], events: StableBTreeMap[nat64, Event]) -> HttpResponse:
    canister_meta_opt = canister_metadata.get(0)
    if canister_meta_opt:
        super_admin = ','.join(canister_meta_opt['super_admin'])
        owners = ','.join(canister_meta_opt['owners'])
        collaborators = ','.join(canister_meta_opt['collaborators'])
        burn_address = canister_meta_opt['burn_address']
        collection_name = canister_meta_opt['collection_name']
    else:
        super_admin = ''
        owners = ''
        collaborators = ''
        burn_address = ''
        collection_name = ''
        
    minted_nfts_count = registry.len()
    burned_amount_opt = address_registry.get(burn_address)
    if burned_amount_opt:
        burned_nfts_count = len(burned_amount_opt)
    else:
        burned_nfts_count = 0

    current_supply = minted_nfts_count - burned_nfts_count
    unique_holders = address_registry.len()
    http_response_body = http_response_body = nft_home_page_html.get_home_page_html(registry, address_registry, canister_metadata, events) #type: ignore
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
                            {return_default_cell('Collection Name', collection_name)}
                            {return_default_cell('Super Admin', super_admin)}
                            {return_default_cell('Owners', owners)}
                            {return_default_cell('Collaborators', collaborators)}
                            {return_default_cell('Burn Address', burn_address)}
                            {return_default_cell('# of Minted NFTs', str(minted_nfts_count))}
                            {return_default_cell('# of Burned NFTs', str(burned_nfts_count))}
                            {return_default_cell('Current Supply', str(current_supply))}
                            {return_default_cell('Unique Holders', str(unique_holders))}
                        </table>
                    </div>
                    <div>
                        <table style="border-collapse:collapse; margin: 25px 0; min-width: 400px;">
                            <tr style="border-bottom: 1px solid #dddddd">
                                <th style="padding: 12px 15px;">Event Type</th>
                                <th style="padding: 12px 15px;">Timestamp</th>
                                <th style="padding: 12px 15px;">Description</th>
                            </tr>
                            {event_items(events)}
                        </table>
                    </div>
                </body>
            </html>
        ''',encoding='utf-8')

    return {
        'status_code':200,
        'headers':[('Content-Type','text/html')],
        'body':http_response_body,
        'streaming_strategy': None,
        'upgrade': False
    }