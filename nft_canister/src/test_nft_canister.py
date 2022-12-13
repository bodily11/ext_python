from ic.canister import Canister
from ic.client import Client
from ic.agent import Agent
from ic.candid import encode # type: ignore
from ic.identity import Identity
from kybra import Variant
local = False

with open('/Users/bob/Downloads/identity.pem','r') as f:
    private_key_1 = f.read()

i1 = Identity.from_pem(private_key_1)
if local:
    client = Client(url = "http://127.0.0.1:4943")
else:
    client = Client()
agent = Agent(i1, client)

params = []
params = encode(params) # type: ignore

canister_id = '5bgk3-4yaaa-aaaam-aayrq-cai'

response = agent.query_raw(canister_id,'__get_candid_interface_tmp_hack',params) # type: ignore
canister_did: str = response[0]['value'] # type: ignore
my_canister = Canister(agent=agent, canister_id=canister_id, candid=canister_did)

from kybra import Variant
class FunctionCallResult(Variant, total=False):
    ok: str
    err: str



# add_collection_collaborator : (text) -> (FunctionCallResult);
def test_add_collection_collaborator(text: str, authorized: bool) -> FunctionCallResult:
    if authorized:
        result = my_canister.add_collection_collaborator(text)[0] # type: ignore
        if 'ok' in result:
            text = text.strip()
            result2 = my_canister.get_collection_collaborators()[0] # type: ignore
            if text in result2:
                return {'ok':'Add collection collaborator passed.'}
            else:
                return {'err':f"Add collection collaborator verification failed with input '{text}'. {result['err']}"}
        else:
            return {'err':f"Add collection collaborator function failed with input '{text}'.\nError: {result['err']}"}
    else:
        result = unauthorized_canister.add_collection_collaborator(text)[0] # type: ignore
        if 'ok' in result:
            return {'err':f"Authorization failed for add collection collaborator."}
        else:
            return {'ok':f"Add collection collaborator passed."}

result1 = test_add_collection_collaborator('leem4-edexi-gizih-27zhr-5bakc-gtvr5-nuxax-in5yc-l2fn5-dnhk4-3ae', True)
result2 = test_add_collection_collaborator('rrkah-fqaaa-aaaaa-aaaaq-cai', True)
result3 = test_add_collection_collaborator('leem4-edexi-gizih-27zhr-5bakc-gtvr5-nuxax-in5yc-l2fn5-dnhk4-3ae  ', True)
result4 = test_add_collection_collaborator('leem4-edexi-gizih-27zhr-5bakc-gtvr5-nuxax-in5yc-l2fn5-dnhk4-3a', True)
result5 = test_add_collection_collaborator('leem4-edexi-gizih-27zhr-5bakc-gtvr5-nuxax-in5yc-l2fn5-dnhk4-3ae', False)

if 'ok' in result1 and 'ok' in result2 and 'ok' in result3 and 'err' in result4 and 'ok' in result5:
    print('Passed')
else:
    print('Failed')
