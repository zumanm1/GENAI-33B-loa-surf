# Mock Data Bundle

This directory contains **self-contained mock data and payload templates** to help you wire up UI components and backend API calls before connecting to real devices.

All content is fictitious. When you move to the lab, swap the values to match your actual routers/switches.

## Contents

```
mock_data/
│ README.md                 – this file
│
├── cli_outputs/            – raw CLI command captures (plain-text)
│   ├── show_running_config_R15.txt
│   ├── show_ip_interface_brief_R15.txt
│   └── show_version_R15.txt
│
├── structured/             – machine-readable representations
│   ├── R15_sample.json
│   ├── R15_simple.yaml
│   └── R15_full.yaml
│
├── templates/              – Jinja2 snippets ready for rendering / push
│   └── push_snippet.j2
│
└── api_payloads/           – example REST payloads
    └── examples.json
```

### How to use

1. **Unit / integration tests** – load JSON / YAML fixtures from `structured/`.
2. **Frontend prototyping** – import the JSON file via the dev server or embed it in a stub endpoint.
3. **Backend stub mode** – serve the CLI text files as if they were captured from Telnet.
4. **Config Push** – render `templates/push_snippet.j2` with your data structure, then POST to `/api/devices/<id>/config` (see sample in `api_payloads/examples.json`).

Feel free to extend the directory with more devices or commands.
