import pytest
from app.messengers.whatsapp import get_bridge_url


def test_get_bridge_url_consistent_routing():
    """Same session_id always routes to same bridge."""
    bridges = ["http://bridge-1:3000", "http://bridge-2:3000", "http://bridge-3:3000"]
    url1 = get_bridge_url(42, bridges)
    url2 = get_bridge_url(42, bridges)
    assert url1 == url2


def test_get_bridge_url_distributes():
    """Different session_ids distribute across bridges."""
    bridges = ["http://bridge-1:3000", "http://bridge-2:3000", "http://bridge-3:3000"]
    urls = {get_bridge_url(i, bridges) for i in range(10)}
    assert len(urls) > 1
