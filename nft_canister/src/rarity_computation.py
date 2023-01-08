from kybra import nat16,StableBTreeMap,nat8,float64
from main_types import CanisterMeta,Nft,NftMetadata,tupleType,FunctionCallResult
import math

def run_rarity_calcs(canister_metadata: StableBTreeMap[nat8, CanisterMeta], nfts: StableBTreeMap[nat16, Nft], registry: StableBTreeMap[nat16, str], nft_metadata: StableBTreeMap[nat16, NftMetadata], nft_rarity_scores: StableBTreeMap[str, list[tupleType]], caller_principal: str) -> FunctionCallResult:

    def get_permissions(permission_type: str) -> list[str]:
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

    total_nfts = nfts.len()
    final_sorted_scores: dict[str,list[float]] = {'information_score':[], 'probability_score':[],'expected_value':[],'open_rarity_score':[]}
    if caller_principal in get_permissions('level_2'):
        trait_category_text_counts: dict[str, dict[str,int]] = {}
        trait_category_number_arrays: dict[str, list[float]] = {}

        all_nfts = registry.items()
        for nft in all_nfts:
            nft_index = nft[0]
            single_nft = nfts.get(nft_index)
            if single_nft:
                metadata_index = single_nft['metadata_index']
                metadata_opt = nft_metadata.get(metadata_index)
                if metadata_opt:
                    for trait_category,trait_value in metadata_opt['static_traits_text']:
                        if trait_category not in trait_category_text_counts:
                            trait_category_text_counts[trait_category] = {}
                        if trait_value not in trait_category_text_counts[trait_category]:
                            trait_category_text_counts[trait_category][trait_value] = 0

                        trait_category_text_counts[trait_category][trait_value] += 1

                    for trait_category,trait_value in metadata_opt['static_traits_number']:
                        if trait_category not in trait_category_number_arrays:
                            trait_category_number_arrays[trait_category] = []

                        trait_category_number_arrays[trait_category].append(trait_value)

        expected_value_sum = 0
        for nft in all_nfts:
            nft_index = nft[0]
            single_nft = nfts.get(nft_index)
            if single_nft:
                metadata_index = single_nft['metadata_index']
                metadata_opt = nft_metadata.get(metadata_index)
                if metadata_opt:
                    information_bit_total = 0
                    final_trait_probability = 1
                    for trait_category,trait_value in metadata_opt['static_traits_text']:
                        trait_count = trait_category_text_counts[trait_category][trait_value]

                        trait_probability = trait_count / total_nfts
                        information_bit = -1 * math.log2(trait_probability)

                        information_bit_total += information_bit
                        final_trait_probability = final_trait_probability * trait_probability

                    for trait_category,trait_value in metadata_opt['static_traits_number']:
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
                    metadata_opt['rarity_scores'] = new_rarity_data
                    nft_metadata.insert(metadata_index, metadata_opt)
                    
                    final_sorted_scores['information_score'].append(information_bit_total)
                    final_sorted_scores['probability_score'].append(final_trait_probability)
                    final_sorted_scores['expected_value'].append(expected_value)

                    # we need this summed across NFTs for standardization purposes
                    expected_value_sum += expected_value

        for nft in all_nfts:
            nft_index = nft[0]
            single_nft = nfts.get(nft_index)
            if single_nft:
                metadata_index = single_nft['metadata_index']
                metadata_opt = nft_metadata.get(metadata_index)
                if metadata_opt:
                    rarity_scores = metadata_opt['rarity_scores']
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
        
        all_information: list[tuple[nat16, float64]] = []
        all_probability: list[tuple[nat16, float64]] = []
        all_expected_value: list[tuple[nat16, float64]] = []
        all_open_rarity: list[tuple[nat16, float64]] = []

        for nft in all_nfts:
            nft_index = nft[0]
            single_nft = nfts.get(nft_index)
            if single_nft:
                metadata_index = single_nft['metadata_index']
                metadata_opt = nft_metadata.get(metadata_index)
                if metadata_opt:
                    rarity_scores = metadata_opt['rarity_scores']
                    if rarity_scores:
                        score = [x[1] for x in rarity_scores if x[0] == 'information_score'][0]
                        rarity_scores.append(('information_percentile', information_percentiles[score]))
                        all_information.append((nft_index, information_percentiles[score]))

                        score = [x[1] for x in rarity_scores if x[0] == 'probability_score'][0]
                        rarity_scores.append(('probability_percentile', probability_percentiles[score]))
                        all_probability.append((nft_index, probability_percentiles[score]))

                        score = [x[1] for x in rarity_scores if x[0] == 'expected_value'][0]
                        rarity_scores.append(('expected_value_percentile', expected_value_percentiles[score]))
                        all_expected_value.append((nft_index,expected_value_percentiles[score]))
                        
                        score = [x[1] for x in rarity_scores if x[0] == 'open_rarity_score'][0]
                        rarity_scores.append(('open_rarity_percentile', open_rarity_percentiles[score]))
                        all_open_rarity.append((nft_index,open_rarity_percentiles[score]))

                        metadata_opt['rarity_scores'] = rarity_scores
                        nft_metadata.insert(nft_index, metadata_opt)
        
        nft_rarity_scores.insert('information',all_information)
        nft_rarity_scores.insert('probability',all_probability)
        nft_rarity_scores.insert('expected_value',all_expected_value)
        nft_rarity_scores.insert('open_rarity',all_open_rarity)
        return {'ok':'Open rarity, information, probability, and expected value scores and percentiles have been successfully computed for your NFTs.'}
    else:
        return {'err':'Sorry, you have to be admin to run compute rarity.'}
