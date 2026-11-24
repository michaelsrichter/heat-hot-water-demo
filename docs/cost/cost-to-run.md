# Cost to run

Azure has created the resource group, ADLS account, container, monitoring,
registry, and Container Apps environment in the signed-in demo subscription.
No measured billing amount is claimed yet.

The new ADLS Gen2 path adds:

- a standard locally redundant StorageV2 account;
- a hot-tier data container;
- storage diagnostic logs; and
- read and write operations from ingestion and Strategy refresh.

The data size is small for a demo. Log Analytics and Container Apps are more
likely cost drivers than Blob capacity.

The template retains a USD 50 monthly budget alert. This is a default ceiling,
not an approved spending commitment. Budget alerts do not stop paid workloads.

Power BI/Fabric capacity is not required by this architecture.

