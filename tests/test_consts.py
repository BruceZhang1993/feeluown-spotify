from fuo_spotify.consts import PROVIDER_ID, PROVIDER_NAME, QUALITY_MAP


def test_provider_constants():
    assert PROVIDER_ID == 'spotify'
    assert PROVIDER_NAME == 'Spotify'


def test_quality_map_has_all_levels():
    assert set(QUALITY_MAP.keys()) == {'lq', 'sq', 'hq', 'shq'}
    for _, config in QUALITY_MAP.items():
        assert 'bitrate' in config
        assert 'format' in config
