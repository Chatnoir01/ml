from adversarial_sbox.phase2e import replacement_summary


def test_d3_classifies_score_caused_entrants_at_next_corresponding_stage() -> None:
    run = {
        'selection_events': [
            {
                'generation': 0,
                'stage': 'shortlist',
                'score_caused_entered': ['kept', 'same_lost', 'gone', 'worse'],
                'active_tags': [],
                'base_group': [],
            },
            {
                'generation': 1,
                'stage': 'shortlist',
                'score_caused_entered': [],
                'active_tags': [],
                'base_group': ['kept', 'same_lost'],
            },
        ],
        'generation_trace': [
            {
                'generation': 0,
                'population_before': [],
                'shortlist': [],
                'proposals': [],
                'next_population': ['kept', 'same_lost', 'worse'],
            },
            {
                'generation': 1,
                'population_before': ['kept', 'same_lost', 'worse'],
                'shortlist': ['kept'],
                'proposals': [],
                'next_population': ['kept'],
            },
        ],
    }
    summary = replacement_summary(run)
    assert len(summary['entrant_records']) == 4
    by_fp = {item['fingerprint']: item for item in summary['entrant_records']}
    assert by_fp['kept']['classification'] == 'retained'
    assert by_fp['same_lost']['classification'] == 'same_key_not_selected'
    assert by_fp['gone']['classification'] == 'lineage_not_present'
    assert by_fp['worse']['classification'] == 'strictly_better_classical_key_present'
    assert summary['entrant_loss_classifications']['same_key_not_selected'] == 1
    assert summary['entrant_loss_classifications']['lineage_not_present'] == 1
    assert summary['entrant_loss_classifications']['strictly_better_classical_key_present'] == 1
