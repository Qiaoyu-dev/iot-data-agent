from rag.chunk import split_by_structure


def test_short_paragraphs_merge_up_to_limit():
    text = "## 标题\n\n第一段。\n\n第二段。"
    chunks = split_by_structure(text, max_chars=30, overlap=5)
    assert chunks
    assert all(len(chunk) <= 30 for chunk in chunks)


def test_heading_is_prefixed_to_chunks():
    chunks = split_by_structure("## 温度告警\n\n温度超过 85 度需要立即处置。", max_chars=50)
    assert any("温度告警" in chunk for chunk in chunks)


def test_overlong_paragraph_uses_sliding_window():
    para = "水泵维护要求" * 20
    chunks = split_by_structure(f"## 保养\n\n{para}", max_chars=40, overlap=8)
    assert len(chunks) > 1
