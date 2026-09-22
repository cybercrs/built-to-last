"""Student-facing case content for the asset lifecycle."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChoiceQuestion:
    id: str
    artifact: str
    title: str
    story: str
    prompt: str
    options: tuple[str, ...]
    correct: str
    explanation: str
    account_effect: str
    statement_effect: str


COMPANY_NAME = "Gem City Adventure Works"
REPORTING_DATE = "December 31, 2031"

UPKEEP_OPTIONS = (
    "Increase the related plant asset",
    "Increase current-period expense",
)


ACQUISITION_QUESTIONS = (
    ChoiceQuestion(
        id="site_closing",
        artifact="Attorney invoice and tax notice",
        title="Complete the land purchase",
        story=(
            "The company pays $6,000 of title and attorney fees and assumes a $5,000 obligation "
            "for unpaid property taxes attached to the site."
        ),
        prompt="Which account changes explain both the closing costs and the assumed obligation?",
        options=(
            "Land increases $11,000; Cash decreases $6,000; Property Taxes Payable increases $5,000",
            "Land increases $6,000; Cash decreases $6,000; Property Taxes Payable increases $5,000",
            "Land increases $11,000; Cash decreases $11,000; Property Taxes Payable is unchanged",
        ),
        correct="Land increases $11,000; Cash decreases $6,000; Property Taxes Payable increases $5,000",
        explanation="Closing costs and assumed liens are necessary costs of acquiring the land.",
        account_effect=(
            "Land increases $11,000; Cash decreases $6,000; Property Taxes Payable increases $5,000."
        ),
        statement_effect="Total assets and liabilities each increase $5,000; there is no current expense.",
    ),
    ChoiceQuestion(
        id="parking_lot",
        artifact="Contractor invoice",
        title="Pave the parking lot",
        story="A contractor charges $36,000 to install a paved parking lot with a limited service life.",
        prompt="Which asset balance should include the paving cost?",
        options=("Land Improvements", "Land", "Building"),
        correct="Land Improvements",
        explanation="A parking lot is a land improvement because it has a limited useful life.",
        account_effect="Land Improvements increases $36,000; Cash decreases $36,000.",
        statement_effect="The cost becomes a depreciable plant asset.",
    ),
    ChoiceQuestion(
        id="equipment_ready",
        artifact="Equipment purchase packet",
        title="Prepare the activity equipment",
        story=(
            "The equipment costs $82,000. Sales tax is $5,000, freight is $2,000, and installation "
            "and testing cost $5,000."
        ),
        prompt="Which cost belongs in the Equipment balance when the equipment is ready for use?",
        options=(
            "$94,000: price, sales tax, freight, installation, and testing",
            "$89,000: price, sales tax, and freight",
            "$87,000: price and sales tax",
        ),
        correct="$94,000: price, sales tax, freight, installation, and testing",
        explanation="All four costs are necessary to acquire the equipment and prepare it for use.",
        account_effect="Equipment increases $94,000; Cash decreases $94,000.",
        statement_effect="The full ready-for-use cost is reported as a plant asset.",
    ),
    ChoiceQuestion(
        id="staff_training",
        artifact="Training provider invoice",
        title="Train the staff",
        story="After installation, the company pays $3,000 to train employees to operate the equipment.",
        prompt="The equipment was ready for use before this training. Which treatment fits?",
        options=("Increase Training Expense", "Increase Equipment"),
        correct="Increase Training Expense",
        explanation="Employee training is not part of the equipment's ready-for-use cost.",
        account_effect="Training Expense increases $3,000; Cash decreases $3,000.",
        statement_effect="Current net income and equity decrease $3,000.",
    ),
)


UPKEEP_QUESTIONS = (
    ChoiceQuestion(
        id="van_tuneup",
        artifact="Vehicle service order",
        title="Keep the delivery van running",
        story="A $1,200 tune-up maintains the van's normal operating efficiency and expected life.",
        prompt="How should the company treat this expenditure?",
        options=UPKEEP_OPTIONS,
        correct="Increase current-period expense",
        explanation="Routine work that maintains normal operations is an ordinary repair.",
        account_effect="Maintenance Expense increases $1,200; Cash decreases $1,200.",
        statement_effect="Current net income and equity decrease $1,200.",
    ),
    ChoiceQuestion(
        id="climbing_system",
        artifact="Expansion proposal",
        title="Add a new climbing system",
        story="An $18,000 addition increases the equipment's capacity and creates new customer sessions.",
        prompt="How should the company treat this expenditure?",
        options=UPKEEP_OPTIONS,
        correct="Increase the related plant asset",
        explanation="The addition increases productive capacity and provides benefits beyond the current period.",
        account_effect="Equipment increases $18,000; Cash decreases $18,000.",
        statement_effect="There is no immediate expense; future cost allocation will reflect the added investment.",
    ),
    ChoiceQuestion(
        id="building_paint",
        artifact="Painter invoice",
        title="Refresh the building",
        story="The company pays $6,000 to repaint worn interior walls and restore their normal condition.",
        prompt="How should the company treat this expenditure?",
        options=UPKEEP_OPTIONS,
        correct="Increase current-period expense",
        explanation="Painting that restores normal condition is an ordinary repair.",
        account_effect="Maintenance Expense increases $6,000; Cash decreases $6,000.",
        statement_effect="Current net income and equity decrease $6,000.",
    ),
    ChoiceQuestion(
        id="party_room",
        artifact="Construction completion report",
        title="Add a party room",
        story="A $90,000 building addition creates rentable space that did not previously exist.",
        prompt="How should the company treat this expenditure?",
        options=UPKEEP_OPTIONS,
        correct="Increase the related plant asset",
        explanation="The addition expands the building's productive capacity and creates future benefits.",
        account_effect="Building increases $90,000; Cash decreases $90,000.",
        statement_effect="There is no immediate expense; the Building balance increases.",
    ),
)


DEPRECIATION_FACTS = {
    "cost": 50_000,
    "salvage_value": 5_000,
    "useful_life_years": 5,
    "months_used_2028": 9,
}

DEPRECIATION_FIELDS = (
    ("depreciable_cost", "Depreciable cost", 45_000),
    ("annual_depreciation", "Full-year depreciation expense", 9_000),
    ("first_year_expense", "2028 depreciation expense", 6_750),
    ("accumulated_depreciation", "Accumulated Depreciation at December 31, 2030", 24_750),
    ("book_value", "Book value at December 31, 2030", 25_250),
)

DEPRECIATION_QUESTIONS = (
    ChoiceQuestion(
        id="allocation_not_value",
        artifact="Manager's valuation question",
        title="Interpret the van's reported value",
        story="At the end of 2030, a dealer estimates the van could sell for $30,000. Its calculated book value is $25,250.",
        prompt="Why can the reported book value differ from the dealer's estimate?",
        options=(
            "Book value reflects allocated historical cost, while the dealer estimates a selling price",
            "Book value reflects cash set aside for a replacement, while the dealer estimates a selling price",
            "Book value reflects this year's operating cash flow, while the dealer estimates a selling price",
        ),
        correct="Book value reflects allocated historical cost, while the dealer estimates a selling price",
        explanation="Depreciation allocates historical cost over useful life; book value is not a current selling-price estimate.",
        account_effect="Equipment cost remains $50,000 and Accumulated Depreciation reaches $24,750.",
        statement_effect="The van is reported at $25,250 net; the dealer's estimate does not replace that amount.",
    ),
    ChoiceQuestion(
        id="annual_effects",
        artifact="Year-end account review",
        title="Trace one year's allocation",
        story="The company recognizes one full year of straight-line depreciation on the van.",
        prompt="Which set of effects is correct?",
        options=(
            "Depreciation Expense increases; Accumulated Depreciation increases; net income and total assets decrease",
            "Depreciation Expense increases; Equipment cost decreases; net income and total assets decrease",
            "Depreciation Expense increases; Accumulated Depreciation increases; Cash decreases",
        ),
        correct=(
            "Depreciation Expense increases; Accumulated Depreciation increases; net income and total assets decrease"
        ),
        explanation="The annual allocation raises expense and accumulated depreciation without changing Cash or Equipment cost.",
        account_effect="Depreciation Expense increases $9,000; Accumulated Depreciation increases $9,000.",
        statement_effect="Net income, equity, and total assets each decrease $9,000.",
    ),
    ChoiceQuestion(
        id="land_exception",
        artifact="Asset register",
        title="Review the land balance",
        story="The building and the land beneath it were purchased together. The building wears out; the land continues to be used.",
        prompt="How should cost allocation differ between these two assets?",
        options=(
            "Depreciate the building; leave Land at historical cost",
            "Depreciate both over the building's useful life",
            "Depreciate Land but leave Building at historical cost",
        ),
        correct="Depreciate the building; leave Land at historical cost",
        explanation="The building has a limited useful life; land normally does not, so land is not routinely depreciated.",
        account_effect="The Land balance remains at historical cost.",
        statement_effect="No depreciation expense arises from the Land account.",
    ),
)


DISPOSAL_FACTS = {
    "sale_date": "July 1, 2031",
    "cost": 50_000,
    "accumulated_before_2031": 24_750,
    "annual_depreciation": 9_000,
    "cash_proceeds": 18_000,
}

DISPOSAL_FIELDS = (
    ("current_year_depreciation", "2031 depreciation through the sale date", 4_500),
    ("accumulated_depreciation", "Accumulated Depreciation at the sale date", 29_250),
    ("book_value", "Book value at the sale date", 20_750),
    ("loss_on_sale", "Loss on sale", 2_750),
)

DISPOSAL_QUESTIONS = (
    ChoiceQuestion(
        id="sale_comparison",
        artifact="Sale-date statement review",
        title="Explain the sale's statement effect",
        story="After the sale-date depreciation update, the van has a $20,750 book value. The company sells it for $18,000 cash.",
        prompt="Why do total assets fall even though Cash rises?",
        options=(
            "The $20,750 van leaves the balance sheet; $18,000 Cash replaces part of its book value",
            "The $50,000 original cost leaves the balance sheet; the related depreciation stays on the balance sheet",
            "The $18,000 Cash replaces the van; the difference is reported as additional depreciation expense",
        ),
        correct="The $20,750 van leaves the balance sheet; $18,000 Cash replaces part of its book value",
        explanation="Removing a $20,750 net asset and receiving $18,000 cash lowers assets by $2,750, the loss on sale.",
        account_effect="Cash increases $18,000; the van cost and related accumulated depreciation leave the accounts.",
        statement_effect="The $2,750 loss reduces net income and equity; total assets decrease $2,750.",
    ),
    ChoiceQuestion(
        id="retirement",
        artifact="Retirement authorization",
        title="Retire fully depreciated equipment",
        story="A machine costing $20,000 has $20,000 of accumulated depreciation and is discarded for no proceeds.",
        prompt="What happens when the company retires it?",
        options=(
            "Equipment and related Accumulated Depreciation each decrease $20,000; no gain or loss",
            "Equipment decreases $20,000; Accumulated Depreciation stays; a loss increases $20,000",
            "Equipment and related Accumulated Depreciation each decrease $20,000; a loss increases $20,000",
        ),
        correct="Equipment and related Accumulated Depreciation each decrease $20,000; no gain or loss",
        explanation="The asset has zero book value, so removing both balances creates no gain or loss.",
        account_effect="Equipment decreases $20,000; Accumulated Depreciation decreases $20,000.",
        statement_effect="Net plant assets, net income, and equity do not change.",
    ),
)


INTANGIBLE_QUESTIONS = (
    ChoiceQuestion(
        id="patent_defense",
        artifact="Legal invoice",
        title="Successfully defend the patent",
        story="The company acquired a patent for $60,000. It now pays $12,000 in legal costs and successfully defends its rights.",
        prompt="Which treatment reflects the benefit of the successful defense?",
        options=(
            "Increase Patent to $72,000 before later amortization",
            "Leave Patent at $60,000 and increase current legal expense $12,000",
            "Increase Goodwill $12,000 and leave Patent at $60,000",
        ),
        correct="Increase Patent to $72,000 before later amortization",
        explanation="Successful defense costs are added to the Patent balance.",
        account_effect="Patent increases $12,000; Cash decreases $12,000.",
        statement_effect="There is no immediate expense; the additional cost is allocated over the remaining useful life.",
    ),
    ChoiceQuestion(
        id="copyright",
        artifact="Content rights agreement",
        title="Acquire training-video rights",
        story="The company purchases a copyright expected to benefit operations for eight years.",
        prompt="Which treatment best fits the expected benefit?",
        options=(
            "Increase Copyright and amortize it over eight years",
            "Increase Copyright and amortize it over its remaining legal life even if longer than eight years",
            "Increase Copyright and wait until the rights expire to recognize expense",
        ),
        correct="Increase Copyright and amortize it over eight years",
        explanation="A limited-life intangible is allocated to expense over its useful life.",
        account_effect="Copyright increases at acquisition; accumulated amortization builds over its useful life.",
        statement_effect="Amortization expense reduces net income over the eight-year benefit period.",
    ),
    ChoiceQuestion(
        id="trademark",
        artifact="Trademark purchase agreement",
        title="Acquire a renewable brand name",
        story="The company buys a trademark for $40,000 and expects to renew and use it indefinitely.",
        prompt="Which treatment is appropriate while the life remains indefinite?",
        options=(
            "Increase Trademark and do not amortize it",
            "Increase Trademark and amortize it over an estimated five-year period",
            "Increase Trademark and expense the entire purchase price this year",
        ),
        correct="Increase Trademark and do not amortize it",
        explanation="An indefinite-life intangible is reported at cost without routine amortization.",
        account_effect="Trademark increases $40,000; Cash decreases $40,000.",
        statement_effect="There is no routine amortization expense while the life remains indefinite.",
    ),
    ChoiceQuestion(
        id="franchise_purchase",
        artifact="Franchise agreement",
        title="Purchase a ten-year territory",
        story="The company pays $100,000 up front for exclusive franchise rights lasting ten years.",
        prompt="How should the up-front payment be treated?",
        options=(
            "Increase Franchise and amortize it over ten years",
            "Increase Franchise and amortize it over a period based on expected renewals beyond ten years",
            "Increase current expense for the full payment because the agreement requires annual fees",
        ),
        correct="Increase Franchise and amortize it over ten years",
        explanation="The payment acquires a limited-life contractual right.",
        account_effect="Franchise increases $100,000 at acquisition.",
        statement_effect="Amortization expense allocates the cost across the ten-year useful life.",
    ),
    ChoiceQuestion(
        id="franchise_annual_fee",
        artifact="Annual franchise invoice",
        title="Pay the annual operating fee",
        story="The franchiser charges an $8,000 fee for the current year's continuing services.",
        prompt="How should the annual fee be treated?",
        options=(
            "Increase operating expense for the current year",
            "Increase Franchise and spread the fee over the remaining contract",
            "Increase a prepaid asset and spread the fee over future contract years",
        ),
        correct="Increase operating expense for the current year",
        explanation="An annual payment for current services is an operating expense for the period.",
        account_effect="Operating Expense increases $8,000; Cash decreases $8,000.",
        statement_effect="Current net income and equity decrease $8,000.",
    ),
    ChoiceQuestion(
        id="goodwill",
        artifact="Business acquisition analysis",
        title="Acquire an established competitor",
        story="The purchase price exceeds the fair value of the competitor's identifiable net assets by $200,000.",
        prompt="How should the $200,000 difference be reported?",
        options=(
            "Increase Goodwill and do not routinely amortize it",
            "Allocate the difference to identifiable assets without evidence of higher fair values",
            "Increase current acquisition expense for the full difference",
        ),
        correct="Increase Goodwill and do not routinely amortize it",
        explanation="Goodwill arises only from acquiring a business and is considered to have an indefinite life.",
        account_effect="Goodwill increases $200,000 as part of the business acquisition.",
        statement_effect="There is no routine amortization expense for Goodwill.",
    ),
    ChoiceQuestion(
        id="research_development",
        artifact="Product-development cost report",
        title="Develop a new attraction",
        story="The company spends $75,000 researching and developing a new interactive attraction.",
        prompt="How should the $75,000 be reported?",
        options=(
            "Increase Research and Development Expense",
            "Increase an internally developed Patent asset",
            "Increase a development asset until commercial success is known",
        ),
        correct="Increase Research and Development Expense",
        explanation="Research and development costs are expensed when incurred because future benefits are uncertain.",
        account_effect="Research and Development Expense increases $75,000; Cash decreases $75,000.",
        statement_effect="Current net income and equity decrease $75,000.",
    ),
)


ANALYSIS_FACTS = {
    "net_income": 96_000,
    "net_sales": 1_200_000,
    "average_total_assets": 800_000,
}

ANALYSIS_FIELDS = (
    ("profit_margin", "Profit margin", 8.0),
    ("asset_turnover", "Asset turnover", 1.5),
    ("return_on_assets", "Return on assets", 12.0),
)

ANALYSIS_QUESTIONS = (
    ChoiceQuestion(
        id="presentation",
        artifact="Draft balance sheet",
        title="Present long-lived assets",
        story="The draft combines equipment, accumulated depreciation, patents, and trademarks in one unlabeled total.",
        prompt="Which revision would help readers distinguish the resources and their cost allocation?",
        options=(
            "Show property, plant, and equipment net of accumulated depreciation and show intangible assets separately",
            "Show a single long-lived-assets total and explain the mix of assets in the notes",
            "Show property, plant, and equipment at original cost and include accumulated depreciation with intangible assets",
        ),
        correct=(
            "Show property, plant, and equipment net of accumulated depreciation and show intangible assets separately"
        ),
        explanation="Plant assets and intangible assets are presented separately, with accumulated depreciation reducing plant assets.",
        account_effect="Cost and accumulated depreciation remain visible as related balances.",
        statement_effect="Readers can distinguish physical resources from contractual and legal rights.",
    ),
    ChoiceQuestion(
        id="disclosures",
        artifact="Financial statement notes",
        title="Complete the asset disclosures",
        story="Management wants the notes to explain how the reported long-lived-asset amounts were produced.",
        prompt="Which information should the company disclose?",
        options=(
            "Major asset classes, accumulated depreciation, methods used, and depreciation and amortization expense",
            "Major asset classes and current-year asset purchases, without the allocation methods or related expense",
            "Asset replacement plans and estimated selling prices, without cost-allocation methods",
        ),
        correct=(
            "Major asset classes, accumulated depreciation, methods used, and depreciation and amortization expense"
        ),
        explanation="Those disclosures help users interpret the reported cost allocations and asset balances.",
        account_effect="The underlying account balances do not change.",
        statement_effect="The notes make the statement amounts more understandable and comparable.",
    ),
    ChoiceQuestion(
        id="same_roa",
        artifact="Strategy comparison",
        title="Compare two paths to the same return",
        story="Strategy A has a 10% margin and 1.20 turnover. Strategy B has a 6% margin and 2.00 turnover.",
        prompt="Which operating plan best supports Strategy B's route to a 12% return on assets?",
        options=(
            "Keep existing attractions busy enough to generate high sales volume despite a thinner margin",
            "Accept fewer customer visits and rely on higher profit per sale to replace the lost volume",
            "Add more attractions before demand grows so the company has a larger asset base",
        ),
        correct="Keep existing attractions busy enough to generate high sales volume despite a thinner margin",
        explanation="B's lower margin is paired with higher asset turnover, so busy assets and sustained sales volume are central to its 12% return.",
        account_effect="No account balance changes; this is an analysis of reported results.",
        statement_effect="Return on assets reflects both profitability per sales dollar and sales generated per asset dollar.",
    ),
    ChoiceQuestion(
        id="improve_roa",
        artifact="Expansion proposal",
        title="Evaluate a larger asset base",
        story="Management could add a new attraction. It would increase average assets immediately, while customer demand and profit from the attraction would build over time.",
        prompt="What should managers watch when judging whether the expansion improves return on assets?",
        options=(
            "Whether added profit eventually offsets the larger average asset base",
            "Whether visitor sales rise after launch, even if the added expenses outpace those sales",
            "Whether the new attraction earns a profit, without comparing that profit with the larger investment",
        ),
        correct="Whether added profit eventually offsets the larger average asset base",
        explanation="A larger asset base can lower return on assets until the attraction generates enough additional net income.",
        account_effect="The new attraction increases plant assets; later operating results affect net income.",
        statement_effect="Return on assets rises only if net income grows enough relative to average assets.",
    ),
)


# Hints point students back to the evidence without revealing the response.
CHOICE_HINTS = {
    "site_closing": "Separate the amount paid now from the obligation assumed at closing. Which asset cost includes both?",
    "parking_lot": "Consider whether the paving is the land itself or a separate improvement with a limited life.",
    "equipment_ready": "Ask which costs were necessary to get the equipment to its intended location and working condition.",
    "staff_training": "Consider whether training changes the condition of the equipment or develops the employees' ability to use it.",
    "van_tuneup": "Does the service create a new benefit beyond the van's original capacity and life?",
    "climbing_system": "Compare the equipment's capability before and after the addition.",
    "building_paint": "Does the work add new capacity or restore the existing space?",
    "party_room": "Consider whether this creates usable space that the building did not have before.",
    "allocation_not_value": "Compare what historical cost less accumulated depreciation measures with what a dealer offers to pay.",
    "annual_effects": "The asset's original cost remains in Equipment. Which related balance records cost allocated so far?",
    "land_exception": "Which asset has a finite service life that can be allocated over time?",
    "sale_comparison": "Compare the net asset removed with the cash received, rather than comparing cash with original cost.",
    "retirement": "Find the machine's book value before deciding whether discarding it creates a loss.",
    "patent_defense": "A successful defense preserves a legal right that will benefit later periods.",
    "copyright": "Use the period the rights are expected to benefit operations, not an assumed renewal period.",
    "trademark": "The useful life is expected to continue indefinitely; consider whether there is a fixed allocation period.",
    "franchise_purchase": "Separate the up-front right to operate for ten years from later service fees.",
    "franchise_annual_fee": "The invoice covers services in the current year, not a new ten-year right.",
    "goodwill": "The premium arises from acquiring an entire business. Look for the balance that captures that residual value.",
    "research_development": "The spending has occurred, but the project has not produced a purchased legal right or a ready-for-use asset.",
    "presentation": "Keep physical assets and legal rights distinguishable, and show the effect of past cost allocation.",
    "disclosures": "Readers need enough detail to understand both asset categories and how their costs reached expense.",
    "same_roa": "Strategy B earns less on each sales dollar, so consider the role of visitor volume and asset use.",
    "improve_roa": "Return on assets compares net income with the average asset base. Consider both sides after expansion.",
}

NUMERIC_HINTS = {
    "depreciation": {
        "depreciable_cost": "Identify the part of cost expected to be used up over the van's life.",
        "annual_depreciation": "Spread depreciable cost evenly across the five-year useful life.",
        "first_year_expense": "The van entered service on April 1, so 2028 uses nine months of a full year.",
        "accumulated_depreciation": "Add the partial 2028 amount and two full years, 2029 and 2030.",
        "book_value": "Begin with original cost and account for all cost allocated through 2030.",
    },
    "disposal": {
        "current_year_depreciation": "The July 1 sale follows six months of 2031 use.",
        "accumulated_depreciation": "Add depreciation through the sale date to the balance from December 31, 2030.",
        "book_value": "Compare original van cost with the updated accumulated depreciation balance.",
        "loss_on_sale": "Compare cash received with book value at the sale date.",
    },
    "analysis": {
        "profit_margin": "Compare net income with net sales, then express the result as a percentage.",
        "asset_turnover": "Compare net sales with average total assets; report the result in times.",
        "return_on_assets": "Compare net income with average total assets; report the result as a percentage.",
    },
}
