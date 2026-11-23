# SUSMITHA CHOWDARY

Data Engineer | Python · SQL · PySpark · Databricks · Snowflake

Austin, TX | dsusmitha55@gmail.com | 9132073787

## Summary

Data Engineer with nearly 5 years of experience designing, developing, and supporting scalable cloud data pipelines across healthcare and financial services. Skilled in Python, SQL, PySpark, Azure Databricks, AWS Glue, Snowflake, and Delta Lake. Experienced in incremental ETL/ELT processing, dimensional modeling, automated data-quality checks, and performance optimization. Strong background in HIPAA/PHI compliance, financial data reconciliation, CI/CD, and production pipeline reliability.

## Skills

Programming & Processing: Python, SQL, PySpark, Apache Spark, Bash
Cloud & Data Platforms: Azure Data Factory, Azure Databricks, ADLS Gen2, AWS Glue, Amazon S3, Amazon Athena, Amazon CloudWatch, Glue Data Catalog, Snowflake, Delta Lake, Oracle
Data Engineering & Modeling: ETL/ELT, Incremental Processing, MERGE, Dimensional Modeling, SCD Type 2, Medallion Architecture
Data Quality & Security: Validation, Reconciliation, HIPAA/PHI, Data Masking, Role-Based Access, Quarantine Controls
DevOps & Operations: Azure DevOps, Git, CI/CD, Automated Testing, Pipeline Monitoring, CloudWatch, Controlled Backfills
Domain: Healthcare Claims, Payment and Transaction Data, Fraud Analytics Data, Lending and Credit-Risk Data, Regulatory Reporting

## Experience

Data Engineer — Optum | Austin, TX | May 2025 – Present
- Maintain production ingestion pipelines in Azure Data Factory and Azure Databricks that integrate claims, eligibility, and provider feeds into ADLS Gen2 and Delta Lake bronze, silver, and gold layers.
- Designed a reusable, config-driven PySpark ingestion framework that cut onboarding time for a new source feed from ~2 weeks to ~4 days.
- Reduced runtime of the critical claims-processing workflow from about 2 hours to 75 minutes using incremental Delta merges, partition pruning, and resolution of skewed Spark joins.
- Built automated data-quality checks for duplicate claim lines, missing identifiers, invalid service dates, and eligibility mismatches, quarantining failed records before publication.
- Applied HIPAA-aligned PHI controls (column-level masking, role-based access, PHI-safe logging) in Snowflake and Azure.
- Delivered the Snowflake layer: loaded validated Parquet via external stages and COPY INTO, applied MERGE logic for new and adjusted claims, and modeled claims, member, and provider dimensions used by multiple analytics teams.
- Improved scheduled pipeline success rates from about 97% to 99.5% through dependency validation, controlled retries, and idempotent backfills; optimized Databricks compute costs through cluster right-sizing.
- Maintain CI/CD and automated tests in Azure DevOps, review pull requests, mentor junior engineers, and take part in the on-call rotation.

Data Engineer — Citi | Pune, India | January 2020 – May 2023
- Automated source-to-target reconciliation over record counts, transaction totals, and account balances, producing exception files for investigation and cutting daily manual verification from about 90 to 25 minutes.
- Owned batch ETL jobs in AWS Glue and PySpark that integrated Oracle extracts and file feeds through Amazon S3 landing and curated layers, processing ~5 million payment and transaction records per business day.
- Delivered curated transaction datasets to the fraud analytics team for rule and model scoring, with validation checks on transaction classifications and timestamps.
- Prepared and reconciled datasets for monthly regulatory and risk reporting with lineage documentation and control checks for audit review.
- Implemented SCD Type 2 history for customer and account dimensions to support point-in-time lending and credit-risk analysis.
- Shortened the overnight batch window from about 5 hours to 3 hours through watermark-based incremental extraction and join optimization.
- Supported production jobs in the on-call rotation using CloudWatch logs, restart checkpoints, and runbooks.

## Education

Master of Science in Computer Science | University of Central Missouri | Warrensburg, MO | Jan 2024 – Dec 2025
