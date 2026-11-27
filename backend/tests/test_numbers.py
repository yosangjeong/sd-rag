from sdrag.common.numbers import korean_amount, unsupported


def test_fractions_match_as_ratios_only():
    src = ["③법 제2조제2항에서 “대통령령으로 정하는 비율”이라 함은 1분의 100을 말한다."]
    assert unsupported("비율은 100분의 100입니다 [1].", src) == ["100분의 100"]  # r0111
    assert unsupported("1분의 100, 즉 100배입니다.", src) == []
    assert unsupported("25%", ["100분의 25"]) == []
    assert unsupported("1,000분의 2의 범위", ["보수총액에 1천분의 2의 범위에서"]) == []


def test_korean_and_english_units_and_number_words():
    assert unsupported("2 days are paid, then 72 hours", ["2일은 유급 72시간"]) == []
    assert unsupported("2 weeks", ["14일 이내"]) == []
    us = ["one thousand eight hundred and forty hours, one and one-half times the regular rate"]
    assert unsupported("not less than 1,840 hours at 1.5 times", us) == []


def test_amounts():
    assert korean_amount("6억9천만") == 690_000_000 and korean_amount("5천500만") == 55_000_000
    assert unsupported("690 million won", ["부산광역시: 6억9천만원"]) == []
    assert unsupported("500,000 won per day", ["1일에 50만원 이하의 과태료"]) == []
    assert unsupported("150,000 won or more", ["| 150만원 이상 |"]) == ["150,000 won"]  # g0224


def test_references_dates_rates_and_the_question_are_not_figures():
    assert unsupported("위반 시 3년 이하의 징역", ["2년 이하의 징역 제3조\n3. 기타"]) == ["3년"]
    assert unsupported("제18조의3에 따라 2026년 11월 27일부터, 1일 8시간", ["8시간"]) == []
    assert unsupported("보증금 1억5천만원이면", [""], question="보증금 1억5천만원으로 계약") == []


def test_korean_scaled_counts():
    src = ["개업공인중개사의 수가 5백명 이상이고"]
    assert unsupported("at least 500 individual agents", src) == []
    assert unsupported("5백명 이상", src) == [] and unsupported("3백명 이상", src) == ["3백명"]


def test_long_runs_of_scale_words_stay_fast():
    import time

    t = time.perf_counter()
    for s in ("1천" * 60 + " x", "1억 " * 60 + "입니다", "100만 " * 300):
        unsupported("x", [s])
    assert time.perf_counter() - t < 0.5  # was exponential: "1천" x 30 took minutes


def test_a_unit_that_starts_a_word_is_not_a_unit():
    assert unsupported("3주택자와 2회사", ["없음"]) == []


def test_dollar_signs_conversions_back_bare_amounts_and_ranges():
    from sdrag.common.numbers import unsupported

    assert unsupported("The minimum wage is $7.50 per hour", ["$7.25 an hour"]) == ["$7.50"]
    assert unsupported("The minimum wage is $7.25 per hour", ["$7.25 an hour"]) == []
    assert unsupported("90일 이내에", ["3개월 이내"]) == []  # days back to months
    assert unsupported("52주", ["1년"]) == [] and unsupported("365일", ["1년"]) == []
    # an amount the question gives without a unit may be repeated with one
    assert unsupported("2억원까지 보호됩니다", ["보증금"], "보증금 2억에 계약했는데") == []
    assert unsupported("2~5일", ["5일 이내"]) == ["2일"]  # the lower bound is checked too
