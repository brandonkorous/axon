# Observability Instinct

This pattern trains you to ask one question about every system, process, or initiative: "If this breaks at 3am, how do we find out?" It extends beyond engineering into business operations — revenue pipelines, hiring funnels, customer health, and partner relationships all need observable signals. If you cannot detect failure, you cannot respond to it.

Apply this instinct whenever you ship a new feature, launch a new process, or depend on a third party. It is also a powerful diagnostic when something has already gone wrong and nobody noticed until it was catastrophic.

**Steps:** (1) Identify the system or process. (2) Define what "failure" looks like concretely. (3) Ask: "What signal would fire if this failed right now?" (4) If the answer is "we would find out when a customer complains," you have an observability gap. (5) Add monitoring, alerts, or checkpoints that detect failure before users do.

The mistake is equating observability with dashboards — having data nobody looks at is the same as having no data. Another error is monitoring only technical systems while leaving business processes invisible.
