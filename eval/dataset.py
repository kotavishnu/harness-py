from dataclasses import dataclass, field


@dataclass
class TestCase:
    id: str
    input: str
    expected: str
    trap: str | None = None
    tags: list[str] = field(default_factory=list)


dataset: list[TestCase] = [
    TestCase(
        id="geo-australia-capital",
        input="What is the capital of Australia?",
        expected="Canberra",
        trap="Sydney",
        tags=["geography"],
    ),
    TestCase(
        id="geo-brazil-capital",
        input="What is the capital of Brazil?",
        expected="Brasília",
        trap="Rio de Janeiro",
        tags=["geography"],
    ),
    TestCase(
        id="geo-most-lakes",
        input="Which country has the most natural lakes in the world?",
        expected="Canada",
        trap="Russia",
        tags=["geography"],
    ),
    TestCase(
        id="bio-octopus-hearts",
        input="How many hearts does an octopus have?",
        expected="3",
        trap="1",
        tags=["biology"],
    ),
    TestCase(
        id="bio-spider-legs",
        input="How many legs does a spider have?",
        expected="8",
        trap="6",
        tags=["biology"],
    ),
    TestCase(
        id="astro-mars-moons",
        input="How many moons does Mars have?",
        expected="2",
        trap="1",
        tags=["astronomy"],
    ),
    TestCase(
        id="geo-populous-2024",
        input="What is the most populous country in the world as of 2024?",
        expected="India",
        trap="China",
        tags=["geography", "recency"],
    ),
    TestCase(
        id="sci-salt-boiling",
        input="Does adding salt to water raise or lower its boiling point?",
        expected="raise",
        trap="lower",
        tags=["science"],
    ),
]
