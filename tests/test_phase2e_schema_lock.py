from adversarial_sbox.phase2e import replacement_summary, tag_utilization_summary


def test_tag_summary_reports_score_caused_entries_and_creation_rate() -> None:
    run = {
        'selection_events': [
            {
                'generation': 1,
                'stage': 'shortlist',
                'cutoff': 2,
                'group_start': 1,
                'base_group': ['a', 'b'],
                'score_ordered_group': ['b', 'a'],
                'final_group': ['b', 'a'],
                'active_tags': [],
                'score_caused_entered': ['b', 'x'],
                'tag_created': ['b'],
            }
        ]
    }
    summary = tag_utilization_summary(run)
    assert summary['score_caused_entry_occurrences'] == 2
    assert summary['score_caused_entry_unique'] == 2
    assert summary['created_occurrences'] == 1
    assert summary['tag_creation_rate_per_score_caused_entry'] == 0.5
    assert summary['by_stage']['shortlist']['score_caused_entry_occurrences'] == 2


def test_replacement_summary_emits_one_deterministic_receipt_per_active_tag() -> None:
    run = {
        'generation_trace': [
            {
                'generation': 1,
                'population_before': ['same', 'worse', 'keep'],
                'proposals': [],
                'next_population': ['same', 'keep'],
            }
        ],
        'selection_events': [
            {
                'generation': 1,
                'stage': 'shortlist',
                'cutoff': 1,
                'group_start': 0,
                'base_group': ['keep', 'same'],
                'final_group': ['keep', 'same'],
                'active_tags': ['same', 'gone', 'worse'],
                'selected_after': ['keep'],
            }
        ],
    }
    summary = replacement_summary(run)
    assert len(summary['records']) == 3
    assert summary['records'] == sorted(
        summary['records'],
        key=lambda item: (item['generation'], item['stage'], item['fingerprint']),
    )
    by_fp = {item['fingerprint']: item for item in summary['records']}
    assert by_fp['same']['classification'] == 'same_key_not_selected'
    assert by_fp['gone']['classification'] == 'lineage_not_present'
    assert by_fp['worse']['classification'] == 'strictly_better_classical_key_present'
    assert all('generation' in item and 'stage' in item for item in summary['records'])
