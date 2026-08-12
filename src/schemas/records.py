from datetime import datetime


def startup_record(
    source_name,
    source_url,
    name,
    employee_count=None
):
    return {
        "schemaVersion": "1.0",
        "recordType": "STARTUP",
        "source": {
            "name": source_name,
            "url": source_url
        },
        "content": {
            "entityName": name,
            "data": {
                "employeeCount": employee_count
            }
        },
        "collectedAt": datetime.utcnow().isoformat() + "Z"
    }


def product_record(
    source_name,
    source_url,
    startup_name,
    pricing_model
):
    return {
        "schemaVersion": "1.0",
        "recordType": "PRODUCT",
        "source": {
            "name": source_name,
            "url": source_url
        },
        "content": {
            "startupName": startup_name,
            "pricingModel": pricing_model
        },
        "collectedAt": datetime.utcnow().isoformat() + "Z"
    }


def paper_record(
    title,
    authors,
    paper_url,
    github_url=None,
    github_stars=None,
    published_date=None
):
    return {
        "schemaVersion": "1.0",
        "recordType": "RESEARCH_PAPER",
        "content": {
            "title": title,
            "authors": authors,
            "paper_url": paper_url,
            "github_url": github_url,
            "github_stars": github_stars,
            "published_date": published_date
        }
    }


def job_record(
    company,
    date,
    is_remote,
    role_family
):
    return {
        "schemaVersion": "1.0",
        "recordType": "JOB",
        "content": {
            "company": company,
            "date": date,
            "is_remote": is_remote,
            "role_family": role_family
        }
    }