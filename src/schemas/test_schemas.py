import sys
import os
import json

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )
)

from schemas.records import (
    startup_record,
    product_record,
    paper_record,
    job_record
)


print("\nSTARTUP")
print(
    json.dumps(
        startup_record(
            "TestSource",
            "https://example.com",
            "OpenAI",
            3000
        ),
        indent=2
    )
)


print("\nPRODUCT")
print(
    json.dumps(
        product_record(
            "TestSource",
            "https://example.com",
            "OpenAI",
            "PAID"
        ),
        indent=2
    )
)


print("\nRESEARCH PAPER")
print(
    json.dumps(
        paper_record(
            "Example AI Paper",
            ["Author One", "Author Two"],
            "https://arxiv.org/example",
            "https://github.com/example/repo",
            1500,
            "2026-08-12T10:00:00Z"
        ),
        indent=2
    )
)


print("\nJOB")
print(
    json.dumps(
        job_record(
            "Example AI",
            "2026-08-12T10:00:00Z",
            True,
            "Engineering"
        ),
        indent=2
    )
)