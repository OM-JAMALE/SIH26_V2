# Security

This repository is a development scaffold and must not be used with real patient data until reviewed.

Required production controls include authenticated access, authorization by patient and organization, encryption in transit and at rest, consent enforcement, immutable audit events, secret management, retention and deletion policies, provider data-processing agreements, and clinical safety review.

Never place tokens in frontend code, logs, prompts, fixtures, or committed environment files.
