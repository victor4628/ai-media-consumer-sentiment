"""Agreement with the single human reference; attribution supplied by the owner."""
from .ai_validation import compare_labels

REFERENCE_SCOPE = "Single-human-reference versus ChatGPT agreement, not consensus truth accuracy"


def compare_reference_group(items, reference, gpt):
    ids = {item['id'] for item in items}
    if not ids.issubset(reference) or not ids.issubset(gpt):
        raise ValueError('Missing attempted reference IDs')
    pairs = [item for item in items if reference[item['id']]['label'] is not None
             and gpt[item['id']]['label'] is not None]
    agreement = compare_labels([reference[item['id']] for item in pairs],
                               [gpt[item['id']] for item in pairs]) if pairs else None
    if agreement is not None:
        agreement['scope'] = REFERENCE_SCOPE
    return {'attempted': len(items),
            'valid_A': sum(reference[item_id]['label'] is not None for item_id in ids),
            'valid_B': sum(gpt[item_id]['label'] is not None for item_id in ids),
            'valid_pairs': len(pairs), 'agreement': agreement}


def reference_validation(items, splits, reference, gpt):
    index = {item['id']: item for item in items}
    result = {
        'role': 'GPT primary coding compared with one independent human annotator.',
        'reviewers': {'A': 'human_01: one human annotator', 'B': 'ChatGPT primary coding'},
        'human_annotators': 1,
        'source_attribution': 'Project owner corrected reference-label provenance; see data/shareable/human_reference/protocol.json.',
        'independence': 'Human annotation is independent according to the project owner. Existing reference labels and original GPT sample judgments are reused; this is not a new annotation exercise. Original split identities are retained, not a prospectively isolated new validation. GPT spans multiple sessions with version uncertainty.',
    }
    for key, split in [('all_300', 'all_300'), ('original_development_100', 'development_100'),
                       ('original_held_out_200', 'held_out_200')]:
        result[key] = compare_reference_group([index[item_id] for item_id in splits[split]], reference, gpt)
    result['by_platform'] = {
        platform: compare_reference_group([index[item_id] for item_id in splits['all_300']
                                           if index[item_id]['platform'] == platform], reference, gpt)
        for platform in ['news', 'twitter']
    }
    return result
