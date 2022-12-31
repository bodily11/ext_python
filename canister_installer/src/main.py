from kybra import ic, blob, Variant, Async, CanisterResult, Principal, update, StableBTreeMap, query, opt, nat16, Record, init
from kybra.canisters.management import CreateCanisterResult, management_canister

class DefaultResult(Variant, total=False):
    ok: bool
    err: str

class ExecuteCreateCanisterResult(Variant, total=False):
    ok: CreateCanisterResult
    err: str

class FunctionCallResult(Variant, total=False):
    ok: str
    err: str

# TYPE TO MAX SIZE HELPER
# single Nat64: 7 + 8 bytes, max value is 1.84E19
# single Nat32: 7 + 4 bytes, max value is 4294967295
# single Nat16: 7 + 2 bytes, max value is 65535
# single Nat8: 7 + 1 byte, max value is 256
# str: 8 + 1 byte per character
# list of Nats: 10 bytes + (actual_nat)*n
# record: 9 + 6*keys + actual_values
# variant: 10 + 6*keys (include all keys) + actual_value selected
# list in record: 3 + (actual_nat)*n
# string in record: 1 + 1 byte per character
# opt adds 3 bytes
# tuple adds 6 bytes + values within
# bool is 1 byte solo, unknown by itself

#                                 name, canister_id
canister_registry = StableBTreeMap[str, str](memory_id=0, max_key_size=40, max_value_size=35)

#                            name, wasm binary bytes
wasm_binaries = StableBTreeMap[str, blob](memory_id=1, max_key_size=40, max_value_size=10485760)

#                          0 index, list of admin principals
admin_array = StableBTreeMap[nat16, list[str]](memory_id=2, max_key_size=9, max_value_size=350)

class RawBinaryForUpload(Record):
    binary_bytes: blob
    chunk: opt[nat16]
    canister_name: str

@init
def init_():
    admin_array.insert(0,['2sr56-kadmk-wfai7-753z7-yo6rd-a4d2f-ghedf-wrkvd-rav3s-2vcfm-wae'])

def admin():
    calling_principal = str(ic.caller())
    admin_array_opt = admin_array.get(0)
    if admin_array_opt:
        if calling_principal in admin_array_opt:
            return True
        else:
            return False
    else:
        return False

@update
def upload_wasm_binary(raw_binary: RawBinaryForUpload) -> FunctionCallResult:
    if not admin():
        return {'err':'Sorry, you must be admin to call this.'}
    chunk = raw_binary['chunk']
    if chunk == 0 or chunk is None:
        wasm_binaries.insert(raw_binary['canister_name'],raw_binary['binary_bytes'])
        return {'ok':'First chunk of wasm binary successfully uploaded.'}
    else:
        current_binary_opt = wasm_binaries.get(raw_binary['canister_name'])
        if current_binary_opt:
            current_binary_opt = current_binary_opt + raw_binary['binary_bytes']
            wasm_binaries.insert(raw_binary['canister_name'],current_binary_opt)
            return {'ok':f"Added new chunk to wasm binary {raw_binary['canister_name']}. Now {len(current_binary_opt)} chunks long."}
        else:
            return{'err':'No existing binary found. When chunk is greater than 0 we are expecting to add to existing wasm binary.'}

@update
def install_code(canister_name: str) -> Async[DefaultResult]:
    if not admin():
        return {'err':'Sorry, you must be admin to call this.'}
    canister_id_opt = canister_registry.get(canister_name)
    if canister_id_opt:
        canister_id_for_install: Principal = Principal.from_str(canister_id_opt)
        wasm_module_opt = wasm_binaries.get(canister_name)
        if wasm_module_opt:
            canister_result: CanisterResult[None] = yield management_canister.install_code({
                'mode': {
                    'install': None
                },
                'canister_id': canister_id_for_install,
                'wasm_module': wasm_module_opt,
                'arg': bytes()
            })

            if canister_result.err is not None:
                return {
                    'err': canister_result.err
                }
            return {
                'ok': True
            }
        else:
            return {'err':'Sorry, no wasm module was found for the specified canister name.'}
    else:
        return {'err':'Sorry, no canister id was found for this canister name. Try creating a canister first.'}

@update
def reinstall_code(canister_name: str) -> Async[DefaultResult]:
    if not admin():
        return {'err':'Sorry, you must be admin to call this.'}
    canister_id_opt = canister_registry.get(canister_name)
    if canister_id_opt:
        canister_id_for_install: Principal = Principal.from_str(canister_id_opt)
        wasm_module_opt = wasm_binaries.get(canister_name)
        if wasm_module_opt:
            canister_result: CanisterResult[None] = yield management_canister.install_code({
                'mode': {
                    'reinstall': None
                },
                'canister_id': canister_id_for_install,
                'wasm_module': wasm_module_opt,
                'arg': bytes()
            })

            if canister_result.err is not None:
                return {
                    'err': canister_result.err
                }
            return {
                'ok': True
            }
        else:
            return {'err':'Sorry, no wasm module was found for the specified canister name.'}
    else:
        return {'err':'Sorry, no canister id was found for this canister name. Try creating a canister first.'}

@update
def create_canister(canister_name: str) -> Async[ExecuteCreateCanisterResult]:
    if not admin():
        return {'err':'Sorry, you must be admin to call this.'}
    create_canister_result_canister_result: CanisterResult[CreateCanisterResult] = yield management_canister.create_canister({
        'settings': None
    }).with_cycles(int(10e12))

    if create_canister_result_canister_result.err is not None:
        return {
            'err': create_canister_result_canister_result.err
        }

    create_canister_result = create_canister_result_canister_result.ok
    canister_registry.insert(canister_name, create_canister_result['canister_id'].to_str())
    
    return {
        'ok': create_canister_result
    }

@update
def change_canister_name(old_canister_name: str, new_canister_name: str) -> FunctionCallResult:
    if not admin():
        return {'err':'Sorry, you must be admin to call this.'}
    old_canister_opt = canister_registry.get(old_canister_name)
    if old_canister_opt:
        canister_registry.remove(old_canister_name)
        canister_registry.insert(new_canister_name,old_canister_opt)
        return {'ok':f'Canister {old_canister_name} successfully changed to {new_canister_name}.'}
    else:
        return {'err':'Sorry, existing canister name not found.'}

@query
def get_canister_id(canister_name: str) -> str:
    if not admin():
        return 'Sorry, you must be admin to call this.'
    canister_name_opt = canister_registry.get(canister_name)
    if canister_name_opt:
        return canister_name_opt
    else:
        return ''