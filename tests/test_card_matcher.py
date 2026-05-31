"""
卡券匹配核心逻辑测试

测试范围：
- 规格匹配逻辑（多规格/通用卡券）
- 去重逻辑（同 card_id, own 优先）
- 边界情况（空列表/None/大小写）
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class FakeSession:
    """假 session，用于实例化 CardMatcher（不实际查库）"""
    pass


def _make_matcher():
    from common.services.card_matcher import CardMatcher
    return CardMatcher(session=FakeSession())


# ============================================================
# 规格匹配测试
# ============================================================

class TestMatchCardDictsBySpec:
    """测试 _match_card_dicts_by_spec"""

    def _match(self, card_dicts, spec_name=None, spec_value=None):
        matcher = _make_matcher()
        return matcher._match_card_dicts_by_spec(card_dicts, spec_name, spec_value)

    def test_no_spec_returns_generic_cards(self):
        """无规格时，只返回非多规格卡券"""
        cards = [
            {"id": 1, "name": "通用卡", "is_multi_spec": False},
            {"id": 2, "name": "红色S", "is_multi_spec": True, "spec_name": "颜色", "spec_value": "红色"},
        ]
        result = self._match(cards, spec_name=None, spec_value=None)
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_with_spec_returns_matching_multi_spec(self):
        """有规格时，返回匹配的多规格卡券"""
        cards = [
            {"id": 1, "name": "通用卡", "is_multi_spec": False},
            {"id": 2, "name": "红色", "is_multi_spec": True, "spec_name": "颜色", "spec_value": "红色"},
            {"id": 3, "name": "蓝色", "is_multi_spec": True, "spec_name": "颜色", "spec_value": "蓝色"},
        ]
        result = self._match(cards, spec_name="颜色", spec_value="红色")
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_spec_matching_is_case_insensitive(self):
        """规格匹配不区分大小写"""
        cards = [
            {"id": 1, "name": "XL码", "is_multi_spec": True, "spec_name": "Size", "spec_value": "XL"},
        ]
        result = self._match(cards, spec_name="size", spec_value="xl")
        assert len(result) == 1

    def test_spec_matching_strips_whitespace(self):
        """规格匹配去除前后空格"""
        cards = [
            {"id": 1, "name": "红色", "is_multi_spec": True, "spec_name": " 颜色 ", "spec_value": " 红色 "},
        ]
        result = self._match(cards, spec_name="颜色", spec_value="红色")
        assert len(result) == 1

    def test_no_match_returns_empty(self):
        """无匹配时返回空列表"""
        cards = [
            {"id": 1, "name": "红色", "is_multi_spec": True, "spec_name": "颜色", "spec_value": "红色"},
        ]
        result = self._match(cards, spec_name="颜色", spec_value="绿色")
        assert len(result) == 0

    def test_empty_cards_list(self):
        """空卡券列表返回空"""
        result = self._match([], spec_name="颜色", spec_value="红色")
        assert result == []

    def test_multi_spec_ignored_when_no_spec_provided(self):
        """有多规格卡券但未传规格时，多规格卡券被跳过"""
        cards = [
            {"id": 1, "name": "多规格", "is_multi_spec": True, "spec_name": "颜色", "spec_value": "红"},
        ]
        result = self._match(cards, spec_name=None, spec_value=None)
        assert len(result) == 0


# ============================================================
# 去重测试
# ============================================================

class TestDedupCardsById:
    """测试 _dedup_cards_by_id"""

    def _dedup(self, cards):
        from common.services.card_matcher import CardMatcher
        return CardMatcher._dedup_cards_by_id(cards)

    def test_no_duplicates(self):
        """无重复时原样返回"""
        cards = [
            {"id": 1, "name": "A", "card_source": "own"},
            {"id": 2, "name": "B", "card_source": "dock_l1"},
        ]
        result = self._dedup(cards)
        assert len(result) == 2

    def test_duplicate_keeps_own_source(self):
        """重复 card_id 优先保留 own 源"""
        cards = [
            {"id": 1, "name": "A", "card_source": "dock_l1"},
            {"id": 1, "name": "A", "card_source": "own"},
        ]
        result = self._dedup(cards)
        assert len(result) == 1
        assert result[0]["card_source"] == "own"

    def test_duplicate_keeps_first_when_no_own(self):
        """重复 card_id 都是非 own 时保留第一个"""
        cards = [
            {"id": 1, "name": "A", "card_source": "dock_l1"},
            {"id": 1, "name": "A", "card_source": "dock_l2"},
        ]
        result = self._dedup(cards)
        assert len(result) == 1
        assert result[0]["card_source"] == "dock_l1"

    def test_empty_list(self):
        """空列表返回空"""
        assert self._dedup([]) == []

    def test_preserves_order(self):
        """去重后保持原顺序"""
        cards = [
            {"id": 3, "name": "C", "card_source": "own"},
            {"id": 1, "name": "A", "card_source": "own"},
            {"id": 2, "name": "B", "card_source": "own"},
        ]
        result = self._dedup(cards)
        assert [c["id"] for c in result] == [3, 1, 2]
