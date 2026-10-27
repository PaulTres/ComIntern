# Official regulation texts

Put the official texts the assistant should quote here, one folder per regulation code from
`src/comintern/catalog/regulations/*.yaml`:

```
regulation_texts/
  EU_GDPR/gdpr_2016_679_en.pdf
  EU_NIS2/nis2_2022_2555_en.pdf
  RO_NIS2/oug_155_2024_ro.pdf
  DE_NIS2_BSIG/bsig_2025_de.pdf
```

Accepted: `.pdf`, `.docx`, `.txt`, `.md`. Then run `make seed` (or restart `docker compose up`,
whose `seed` service runs on every start). Seeding replaces the passages of every file, so running
it again is safe.

Download the texts from the official sources linked in each regulation's `source_url` (EUR-Lex,
gesetze-im-internet.de, legislatie.just.ro) and check each site's reuse terms before committing a file.
Until a regulation has texts here, the assistant answers from the ComIntern catalog only.
