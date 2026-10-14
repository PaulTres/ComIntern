from app.services.scoring import Item, overall, score_items


def test_weighted_score_excludes_not_applicable():
    s = score_items([
        Item(3, "compliant", True), Item(2, "in_progress"), Item(1, "not_started"), Item(5, "not_applicable"),
    ])
    assert s.score == round(100 * (3 + 1) / 6)
    assert (s.compliant, s.in_progress, s.not_started, s.not_applicable, s.evidenced) == (1, 1, 1, 1, 1)
    assert s.level == "amber"


def test_no_applicable_requirements():
    s = score_items([Item(2, "not_applicable")])
    assert s.score is None and s.level == "none"


def test_overall_weighted_by_regulation_weight():
    a = score_items([Item(3, "compliant")])  # 100, weight 3
    b = score_items([Item(1, "not_started")])  # 0, weight 1
    assert overall([a, b]) == 75
    assert overall([]) is None
