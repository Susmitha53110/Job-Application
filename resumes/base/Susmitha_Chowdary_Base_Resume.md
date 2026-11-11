# SUSMITHA CHOWDARY

Data Engineer | Python · SQL · PySpark · Databricks · Snowflake · Azure · AWS

Susmithachowdary67@gmail.com | 9132073787 | 1601 Scottsdale Ln, Austin, Texas, 78754

## Summary

Data Engineer with 5 years of experience in healthcare and banking data, with experience developing and supporting banking ETL at Citi and owning Azure, Databricks, and Snowflake pipelines at Optum. Builds incremental ingestion, automated data-quality checks, and dimensional models that analytics teams rely on. Experienced with HIPAA-regulated PHI at Optum and with payment, transaction, fraud-analytics, and lending data, regulatory reporting, and data controls at Citi.

## Skills

Languages: Python, SQL, PySpark, Bash
Azure: Azure Data Factory, ADLS Gen2, Azure Databricks, Azure DevOps
AWS: Amazon S3, AWS Glue, Glue Data Catalog, Amazon Athena, Amazon CloudWatch
Data Platforms: Snowflake, Databricks, Apache Spark, Delta Lake (medallion architecture), Oracle
Data Engineering: ETL/ELT, incremental ingestion, dimensional modeling, SCD Type 2, reconciliation, data quality
Snowflake: External stages, COPY INTO, MERGE, SQL transformations, role-based access, masking policies
DevOps & Operations: Git, CI/CD, automated testing, pipeline monitoring, on-call incident response, controlled backfills
Domain & Compliance: Healthcare claims, HIPAA/PHI handling, payment and transaction data, fraud analytics data, lending and credit-risk data, regulatory reporting, data controls

## Experience

Data Engineer — Optum | Austin, TX | May 2025 – Present
- Own production ingestion pipelines in Azure Data Factory and Azure Databricks, integrating claims, eligibility, and provider feeds into ADLS Gen2 and Delta Lake bronze, silver, and gold layers; designed a reusable, config-driven PySpark ingestion framework that cut onboarding time for a new source feed from ~2 weeks to ~4 days.
- Reduced runtime of the critical claims-processing workflow from about 2 hours to 75 minutes using incremental Delta merges, partition pruning, and resolution of skewed Spark joins.
- Built automated data-quality checks for duplicate claim lines, missing identifiers, invalid service dates, and eligibility mismatches, quarantining failed records before publication, and applied HIPAA-aligned PHI controls (column-level masking, role-based access, PHI-safe logging) in Snowflake and Azure.
- Delivered the Snowflake layer: loaded validated Parquet via external stages and COPY INTO, applied MERGE logic for new and adjusted claims, and modeled claims, member, and provider dimensions used by multiple analytics teams.
- Improved scheduled pipeline success rate from about 97% to 99.5% with dependency checks, bounded retries, and idempotent backfills that recover failed runs without duplicating data, and lowered Databricks compute cost through cluster right-sizing.
- Maintain CI/CD and automated tests in Azure DevOps, review pull requests, mentor junior engineers, and take part in the on-call rotation.

Data Engineer — Citi | Pune, India | January 2020 – May 2023
- Progressed from SQL transformations, Python validation, and source-to-target testing to owning batch ETL jobs in AWS Glue and PySpark, integrating Oracle extracts and file feeds through Amazon S3 landing and curated layers and processing ~5 million payment and transaction records per business day.
- Automated source-to-target reconciliation controls over record counts, transaction totals, and account balances, producing exception files for investigation and cutting daily manual verification from about 90 to 25 minutes.
- Delivered curated transaction datasets to the fraud analytics team for rule and model scoring, adding validation checks on transaction classifications and timestamps so alerts ran on complete, consistent data.
- Prepared and reconciled datasets for monthly regulatory and risk reporting with lineage documentation and control checks for audit review, and implemented SCD Type 2 history for customer and account dimensions to support point-in-time lending and credit-risk analysis.
- Shortened the overnight batch window from about 5 hours to 3 hours through watermark-based incremental extraction and join optimization, and supported production jobs in the on-call rotation using CloudWatch logs, restart checkpoints, and runbooks.

## Education

Master of Science in Computer Science | University of Central Missouri | Warrensburg, MO | Jan 2024 – Dec 2025
