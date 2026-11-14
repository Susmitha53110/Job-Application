# Interview prep — solvd / Senior Data Engineer — Knowledge Ingestion

Built ONLY from Susmitha's real background (Optum + Citi Data Engineer, Azure/AWS/Databricks/Snowflake).

## 1) Walk me through a production pipeline you owned end-to-end.
Model answer (~spoken):
At Optum I own production ingestion in Azure Data Factory and Databricks for claims, eligibility, and provider feeds into ADLS Gen2 and Delta Lake bronze, silver, and gold. I built a config-driven PySpark framework so a new source feed went from about two weeks of onboarding to about four days. I also put automated data-quality checks in front of publication and applied HIPAA-aligned PHI controls like column masking and role-based access in Snowflake and Azure. On the Snowflake side I load validated Parquet with external stages and COPY INTO, MERGE for new and adjusted claims, and model claims, member, and provider dimensions for analytics teams. I can go deeper on any layer you care about.

## 2) How did you improve pipeline reliability or runtime with real impact?
Model answer (~spoken):
Two concrete examples. At Optum I reduced a critical claims workflow from about two hours to seventy-five minutes using incremental Delta merges, partition pruning, and fixing skewed Spark joins. I also raised scheduled pipeline success from about ninety-seven percent to ninety-nine point five with dependency checks, bounded retries, and idempotent backfills that recover failed runs without duplicating data. At Citi I shortened the overnight batch window from about five hours to three with watermark-based incremental extraction and join optimization while processing about five million payment and transaction records per business day.

## 3) How do you handle data quality and compliance in regulated data?
Model answer (~spoken):
At Optum I built automated checks for duplicate claim lines, missing identifiers, invalid service dates, and eligibility mismatches, and I quarantine failed records before publication. Because this is PHI, I applied HIPAA-aligned controls: column-level masking, role-based access, and PHI-safe logging in Snowflake and Azure. At Citi I automated source-to-target reconciliation on counts, transaction totals, and account balances, produced exception files, and prepared datasets for regulatory and risk reporting with lineage and control checks for audit review. I do not claim tools or certifications that are not on my resume.
